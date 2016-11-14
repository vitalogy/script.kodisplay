import os
import xbmc
import xbmcaddon
import shutil

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
	def __init__(self, distro, display_w, display_h):
		self.modeslist = [None] * TFT_MODE.MAX_MODES
		self.distro = distro
		self.display_w = display_w
		self.display_h = display_h


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
					xbmc_log(xbmc.LOGWARNING, 'Copied TFT.xml.defaults to TFT.xml!')
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
		for mode in modes:  # modes defined in modes.py
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
		# special infolabel distrologo present
		if path.lower() == '$info[distrologo]':
			logo = self.distro.lower() + '.png'
			imagepath = os.path.join(__media__, logo)
			if not os.path.isfile(imagepath):
				imagepath = os.path.join(__media__, 'kodi.png')
		# special infolabel from kodi present
		elif path.lower().find('$info') >= 0:
			imagepath = path
		# full path to the image given
		elif os.path.isfile(path):
			imagepath = path
		# look for the image in addons __media__ dir
		elif os.path.isfile(os.path.join(__media__, path)):
			imagepath = os.path.join(__media__, path)
		# look for the image in libreelec's storage dir
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

		# begin every list with a background in black color
		# when a background is set in TFT.xml for the mode, then replace this
		self.modeslist[mode].append(['renderBackground', 'visible', '#000000'])

		errortext = __addon__.getLocalizedString(32505)

		xbmc_log(xbmc.LOGDEBUG, '<%s>' % node.tag)

		for child in node:
			opt = []



		### background color
			if child.tag == 'background':
				opt.append('renderBackground')
				opt.append('visible')

				color = child.find('color')
				if color is not None:
					if isColorHex(color.text):  # from helper.py
						opt.append(color.text.encode('utf-8'))
					else:
						notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><color> %s has not the right format' % (node.tag, child.tag, color.text))
						return False
				else:
					notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing <color> tag' % (node.tag, child.tag))
					return False

				self.modeslist[mode][0] = opt[:]
				xbmc_log(xbmc.LOGDEBUG, '  <%s> %s' % (child.tag, opt))



		### text
			elif child.tag == 'text':
				opt.append('renderText')

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
					opt.append('marquee')

				# fontname
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

				# fontsize
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

				self.modeslist[mode].append(opt)
				xbmc_log(xbmc.LOGDEBUG, '  <%s>   %s   text: %s   scrollmode: %s' % (child.tag, opt[1], opt[2], opt[3]))



		### image
			elif child.tag == 'image':
				opt.append('renderImage')

				# visibility condition
				visible = child.find('visible')
				if visible is not None:
					if visible.text.lower() == 'visible':
						opt.append('visible')
					else:
						opt.append(visible.text)
				else:
					opt.append('visible')

				# append path to the image or the infolabel
				if child.get('path') is not None:
					opt.append(self.getImagePath(child.get('path')))
				else:
					notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing path attribut' % (node.tag, child.tag))
					return False

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
					opt.append(0)

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
					image_res_y = 0

				if image_res_x == 0 and image_res_y == 0:
					notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><resx> AND <resy> can not be both 0' % (node.tag, child.tag))
					return False

				# append the other information
				opt.extend([image_pos_x, centerx, image_pos_y, centery, image_res_x, image_res_y])

				self.modeslist[mode].append(opt)
				xbmc_log(xbmc.LOGDEBUG, '  <%s>  %s   path: %s' % (child.tag, opt[1], opt[2]))



		### progressbar
			elif child.tag == 'progressbar':
				opt.append('renderProgressbar')

				# visibility condition
				visible = child.find('visible')
				if visible is not None:
					if visible.text.lower() == 'visible':
						opt.extend(['visible', 'dummy'])
					else:
						opt.extend([visible.text, 'dummy'])
				else:
					opt.extend(['visible', 'dummy'])

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

				self.modeslist[mode].append(opt)
				xbmc_log(xbmc.LOGDEBUG, '  <%s>  %s   width: %s   height: %s' % (child.tag, opt[1], opt[3], opt[4]))



		### <tag> is not supported
			else:
				notify(__addonname__, errortext, 10000, __icon__, xbmc.LOGWARNING)
				xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s> the tag <%s> is not supported' % (node.tag, child.tag))
				return False


		return True
