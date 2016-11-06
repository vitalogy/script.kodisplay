import os
import shutil
import xbmc
import xbmcaddon

from xml.etree import ElementTree as xmltree


__addon__         = xbmcaddon.Addon()
__addonname__     = __addon__.getAddonInfo('name')
__path__          = __addon__.getAddonInfo('path')
__icon__          = os.path.join(__path__, 'icon.png')
__lib__           = os.path.join(__path__, 'resources', 'lib')
__media__         = os.path.join(__path__, 'resources', 'media')
__font__         = os.path.join(__path__, 'resources', 'font')
__tftxml__        = os.path.join(xbmc.translatePath('special://masterprofile'),'TFT.xml')
__tftdefaultxml__ = os.path.join(__path__, 'resources', 'TFT.xml.defaults')

from helper import *
from modes import *


class ModesList():
	def __init__(self, distro, display_w, display_h, pygame):
		self.modeslist = [None] * TFT_MODE.MAX_MODES
		self.distro = distro
		self.display_w = display_w
		self.display_h = display_h
		self.pygame = pygame


	def returnModes(self):
		return self.modeslist


	def checkFileXML(self):
		if not os.path.isfile(__tftxml__):
			if not os.path.isfile(__tftdefaultxml__):
				errortext = __addon__.getLocalizedString(32502)
				notify(__addonname__, errortext, 5000, __icon__, xbmc.LOGWARNING)
				xbmc_log(xbmc.LOGWARNING, 'No TFT.xml found and TFT.xml.defaults missing!')
				return False
			else:
				try:
					shutil.copy2(__tftdefaultxml__, __tftxml__)
				except:
					errortext = __addon__.getLocalizedString(32503)
					notify(__addonname__, errortext, 5000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'Failed to copy TFT.xml.defaults to TFT.xml!')
					return False

		try:
			self.doc = xmltree.parse(__tftxml__)
		except xmltree.ParseError as err:
			errortext = __addon__.getLocalizedString(32504)
			notify(__addonname__, errortext, 5000, __icon__, xbmc.LOGWARNING)
			lineno, column = err.position
			xbmc_log(xbmc.LOGWARNING, 'Parsing of TFT.xml failed in line %s! Watch your <tag> naming! ' % str(lineno))
			return False

		return True


	def xmlToList(self):
		errortext = __addon__.getLocalizedString(32505)

		if not self.checkFileXML():
			return False

		root = self.doc.getroot()
		for mode in modes:  # modes defined in currentmode.py
			tmpMode = root.find(mode)
			if tmpMode is not None:
				tftmode = 'TFT_MODE.' + mode.upper()
				if not self.setupList(tmpMode, eval(tftmode)):
					return False
			else:
				notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
				xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s> tag for the mode is missing' % mode)
				return False

		xbmc_log(xbmc.LOGNOTICE, "Loaded layout from %s successfully" % (__tftxml__))
		return True

	def getImagePath(self, path):
		if path.lower() == '$info[distrologo]':
			logo = self.distro.lower() + '.png'
			imagepath = os.path.join(__media__, logo)
			if not os.path.isfile(imagepath):
				imagepath = os.path.join(__media__, 'kodi.png')
		# full path given
		elif os.path.isfile(path):
			imagepath = path
		# look for the image in addons __media__ dir
		elif os.path.isfile(os.path.join(__media__, path)):
			imagepath = os.path.join(__media__, path)
		# look for the image in libreelecs's storage dir
		elif os.path.isfile(os.path.join('/storage/', path)):
			imagepath = os.path.join('/storage/', path)
		# look for the image in kodi's configuration dir
		elif os.path.isfile(os.path.join(xbmc.translatePath('special://home'), path)):
			imagepath = os.path.join(xbmc.translatePath('special://home'), path)
		# if image could not be found, set path to error.png
		else:
			imagepath = os.path.join(__media__, 'error.png')

		return imagepath


	def setupList(self, node, mode):
		# clear the list for the mode
		self.modeslist[mode] = []

		# begin every list with the background with black color
		# when a background is set in TFT.xml for the mode, then replace this
		default_background = self.pygame.Surface((self.display_w, self.display_h)).convert()
		default_background.fill((0, 0, 0))
		self.modeslist[mode].append(['backgroundToDisplay', 'visible', default_background])

		new_background = default_background.copy()



		errortext = __addon__.getLocalizedString(32505)

		for child in node:
			opt = []


		### background color/image
			if child.tag == 'background':
				color = child.find('color')
				if color is not None:
					if isColorHex(color.text):  # from helper.py
						new_background.fill(hexToRGB(color.text))
						new_background = new_background.convert()
						default_background.blit(new_background, (0 ,0))
					else:
						notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><color> %s has not the right format' % (node.tag, child.tag, color.text))
						return False

				image = child.find('image')
				if image is not None:
					imagepath = self.getImagePath(image.text)
					image = self.pygame.image.load(imagepath).convert_alpha()
					image = self.pygame.transform.scale(image, (self.display_w, self.display_h))
					default_background.blit(image, (0, 0))

				if color is None and image is None:
					notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing <color> and/or <image> tag' % (node.tag, child.tag))
					return False

				xbmc_log(xbmc.LOGDEBUG, '<%s><%s> %s' % (node.tag, child.tag, default_background))
				self.modeslist[mode][0] = (['backgroundToDisplay', 'visible', default_background])  # replace default background


		### text
			elif child.tag == 'text':
				opt.append('textToDisplay')

				# visibility condition
				visible = child.find('visible')
				if visible is not None:
					if visible.text.lower() == 'visible':
						opt.append('visible')
					else:
						opt.append(visible.text)
				else:
					opt.append('visible')

				# display
				if child.get('display') is not None:
					if child.get('display').lower().find('$info') >= 0:
						if child.get('display').lower() == '$info[distroname]':
							opt.append(self.distro)
						else:
							opt.append(child.get('display'))
					else:
						opt.append(child.get('display').encode('utf-8', 'ignore'))
				else:
					notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing display attribut' % (node.tag, child.tag))
					return False

				# scrollmode
				scrollmode = child.find('scrollmode')
				if scrollmode is not None:
					if scrollmode.text.lower() == 'none':
						opt.append(scrollmode.text.lower())
					elif scrollmode.text.lower() == 'marquee':
						opt.append(scrollmode.text.lower())
					elif scrollmode.text.lower() == 'leftright':
						opt.append(scrollmode.text.lower())
					else:
						notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><scrollmode> %s is unknown' % (node.tag, child.tag, scrollmode.text))
						return False
				else:
					opt.append('none')

				# font
				font = child.find('font')
				if font is not None:
					if font.text.lower() == 'none':
						opt.append(font.text.lower())
					elif os.path.isfile(os.path.join(__font__, font.text)):
						opt.append(os.path.join(__font__, font.text))
					else:
						notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><font> %s not found' % (node.tag, child.tag, font.text))
						return False
				else:
					notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing <font> tag' % (node.tag, child.tag))
					return False

				# size
				size = child.find('size')
				if size is not None:
					if isInteger(size.text):  # from helper.py
						opt.append(int(size.text))
					else:
						notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><size> %s is not an integer' % (node.tag, child.tag, size.text))
						return False
				else:
					notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing <size> tag' % (node.tag, child.tag))
					return False

				# color
				color = child.find('color')
				if color is not None:
					if isColorHex(color.text):  # from helper.py
						opt.append(hexToRGB(color.text))
					else:
						notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><color> %s has not the right format' % (node.tag, child.tag, color.text))
						return False
				else:
					notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing <color> tag' % (node.tag, child.tag))
					return False

				# xpos
				xpos = child.find('xpos')
				if xpos is not None:
					if xpos.text.lower() == 'center':
						centerx = self.display_w/2
						opt.append(centerx)
						opt.append(1)
					elif isInteger(xpos.text):
						opt.append(int(xpos.text))
						opt.append(0)
					else:
						notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><xpos> value %s is not supported' % (node.tag, child.tag, xpos.text))
						return False
				else:
					notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing <xpos> tag' % (node.tag, child.tag))
					return False

				# ypos
				ypos = child.find('ypos')
				if ypos is not None:
					if ypos.text.lower() == 'center':
						centery = self.display_h/2
						opt.append(centery)
						opt.append(1)
					elif isInteger(ypos.text):
						opt.append(int(ypos.text))
						opt.append(0)
					else:
						notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><ypos> value %s is not supported' % (node.tag, child.tag, ypos.text))
						return False
				else:
					notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing <ypos> tag' % (node.tag, child.tag))
					return False

				xbmc_log(xbmc.LOGDEBUG, '<%s><%s> %s' % (node.tag, child.tag, opt))
				self.modeslist[mode].append(opt)



		### image
			elif child.tag == 'image':
				opt.append('imageToDisplay')

				# visibility condition
				visible = child.find('visible')
				if visible is not None:
					if visible.text.lower() == 'visible':
						opt.append('visible')
					else:
						opt.append(visible.text)
				else:
					opt.append('visible')

				# xpos
				xpos = child.find('xpos')
				if xpos is not None:
					if xpos.text.lower() == 'center':
						image_pos_x = self.display_w/2
						centerx = 1
					elif isInteger(xpos.text):
						image_pos_x = int(xpos.text)
						centerx = 0
					else:
						notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><xpos> value %s is not supported' % (node.tag, child.tag, xpos.text))
						return False
				else:
					notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing <xpos> tag' % (node.tag, child.tag))
					return False

				# ypos
				ypos = child.find('ypos')
				if ypos is not None:
					if ypos.text.lower() == 'center':
						image_pos_y = self.display_h/2
						centery = 1
					elif isInteger(ypos.text):
						image_pos_y = int(ypos.text)
						centery = 0
					else:
						notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><ypos> value %s is not supported' % (node.tag, child.tag, ypos.text))
						return False
				else:
					notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing <ypos> tag' % (node.tag, child.tag))
					return False

				# resx
				resx = child.find('resx')
				if resx is not None:
					if isInteger(resx.text):  # from helper.py
						if int(resx.text) < 0:
							notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
							xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><resx> value can not be %s (negative)' % (node.tag, child.tag, resx.text))
							return False
						else:
							image_res_x = int(resx.text)
					else:
						notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><resx> value %s is not supported' % (node.tag, child.tag, xpos.text))
						return False
				else:
					image_res_x = 0

				# resy
				resy = child.find('resy')
				if resy is not None:
					if isInteger(resy.text):  # from helper.py
						if int(resy.text) < 0:
							notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
							xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><resy> value can not be %s (negative)' % (node.tag, child.tag, resy.text))
							return False
						else:
							image_res_y = int(resy.text)
					else:
						notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><resy> value %s is not supported' % (node.tag, child.tag, xpos.text))
						return False
				else:
					image_resy_y = 0

				# load and prepare the image
				if child.get('path') is not None:
					imagepath = self.getImagePath(child.get('path'))
					image = self.pygame.image.load(imagepath)
					if image_res_x > 0 or image_res_y > 0:
						image = self.pygame.transform.scale(image, aspect_scale(image, (image_res_x, image_res_y)))
					image = image.convert_alpha()

					imagepos = image.get_rect()

					if centerx == 0:
						if image_pos_x < 0:
							imagepos.x = self.display_w - image.get_width() + image_pos_x
						else:
							imagepos.x = image_pos_x
					else:
						imagepos.centerx = image_pos_x

					if centery == 0:
						if image_pos_y < 0:
							imagepos.y = self.display_h - image.get_height() + image_pos_y
						else:
							imagepos.y = image_pos_y
					else:
						imagepos.centery = image_pos_y

					opt.extend([image, imagepos])
				else:
					notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing path attribut' % (node.tag, child.tag))
					return False


				xbmc_log(xbmc.LOGDEBUG, '<%s><%s> %s' % (node.tag, child.tag, opt))
				self.modeslist[mode].append(opt)



		### progressbar
			elif child.tag == 'progressbar':
				opt.append('progressBarToDisplay')

				# visibility condition
				visible = child.find('visible')
				if visible is not None:
					if visible.text.lower() == 'visible':
						opt.append('visible')
					else:
						opt.append(visible.text)
				else:
					opt.append('visible')

				# width
				width = child.find('width')
				if width is not None:
					if isInteger(width.text):  # from helper.py
						if int(width.text) <= 0:
							notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
							xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><width> value should be greater 0, yours %s' % (node.tag, child.tag, width.text))
							return False
						else:
							opt.append(int(width.text))
					else:
						notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><width> value %s is not supported' % (node.tag, child.tag, xpos.text))
						return False
				else:
					notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing <width> tag' % (node.tag, child.tag))
					return False

				# height
				height = child.find('height')
				if height is not None:
					if isInteger(height.text):  # from helper.py
						if int(height.text) < 0:
							notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
							xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><height> value should be greater 0, yours %s' % (node.tag, child.tag, height.text))
							return False
						else:
							opt.append(int(height.text))
					else:
						notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><height> value %s is not supported' % (node.tag, child.tag, height.text))
						return False
				else:
					notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing <height> tag' % (node.tag, child.tag))
					return False

				# color
				color = child.find('barcolor')
				if color is not None:
					if isColorHex(color.text):  # from helper.py
						opt.append(hexToRGB(color.text))
					else:
						notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><barcolor> %s has not the right format' % (node.tag, child.tag, color.text))
						return False
				else:
					opt.append(hexToRGB('#FF0000')) # red

				# color of progress
				color = child.find('progresscolor')
				if color is not None:
					if isColorHex(color.text):  # from helper.py
						opt.append(hexToRGB(color.text))
					else:
						notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><progresscolor> %s has not the right format' % (node.tag, child.tag, color.text))
						return False
				else:
					opt.append(hexToRGB('#0000FF')) # blue

				# border
				border = child.find('border')
				if border is not None:
					if isInteger(border.text):  # from helper.py
						if int(border.text) < 0:
							notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
							xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><border> value can not be %s (negative)' % (node.tag, child.tag, border.text))
							return False
						else:
							opt.append(int(border.text))
					else:
						notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><border> value %s is not supported' % (node.tag, child.tag, border.text))
						return False
				else:
					opt.append(1)

				# color of border
				color = child.find('bordercolor')
				if color is not None:
					if isColorHex(color.text):  # from helper.py
						opt.append(hexToRGB(color.text))
					else:
						notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><bordercolor> %s has not the right format' % (node.tag, child.tag, color.text))
						return False
				else:
					opt.append(hexToRGB('#FFFFFF')) # white

				# xpos
				xpos = child.find('xpos')
				if xpos is not None:
					if xpos.text.lower() == 'center':
						centerx = self.display_w/2
						opt.append(centerx)
						opt.append(1)
					elif isInteger(xpos.text):  # from helper.py
						opt.append(int(xpos.text))
						opt.append(0)
					else:
						notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><xpos> value %s is not supported' % (node.tag, child.tag, xpos.text))
						return False
				else:
					notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing <xpos> tag' % (node.tag, child.tag))
					return False

				# ypos
				ypos = child.find('ypos')
				if ypos is not None:
					if ypos.text.lower() == 'center':
						centery = self.display_h/2
						opt.append(centery)
						opt.append(1)
					elif isInteger(ypos.text):  # from helper.py
						opt.append(int(ypos.text))
						opt.append(0)
					else:
						notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><ypos> value %s is not supported' % (node.tag, child.tag, ypos.text))
						return False
				else:
					notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing <ypos> tag' % (node.tag, child.tag))
					return False

				xbmc_log(xbmc.LOGDEBUG, '<%s><%s> %s' % (node.tag, child.tag, opt))
				self.modeslist[mode].append(opt)



			# <tag> is not supported
			else:
				notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
				xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s> the tag <%s> is not supported' % (node.tag, child.tag))
				return False



#		xbmc_log(xbmc.LOGDEBUG, '%s %s' % (mode, self.modeslist[mode]))
		return True
