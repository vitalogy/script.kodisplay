import os
import xbmc
import xbmcaddon

from xml.etree import ElementTree as xmltree


__addon__         = xbmcaddon.Addon()
__addonname__     = __addon__.getAddonInfo('name')
__path__          = __addon__.getAddonInfo('path')
__icon__          = os.path.join(__path__, 'icon.png')
__lib__           = os.path.join(__path__, 'resources', 'lib')
__media__         = os.path.join(__path__, 'resources', 'media')
__tftxml__        = xbmc.translatePath( os.path.join("special://masterprofile","TFT.xml"))
__tftdefaultxml__ = xbmc.translatePath( os.path.join(__path__, "resources", "TFT.xml.defaults"))

from helper import *
from currentmode import *


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
				text = __addon__.getLocalizedString(32502)
				notify(__addonname__, text, 5000, __icon__, xbmc.LOGWARNING)
				return False
			else:
				try:
					shutil.copy2(__tftdefaultxml__, __tftxml__)
				except:
					text = __addon__.getLocalizedString(32503)
					notify(__addonname__, text, 5000, __icon__, xbmc.LOGWARNING)
					return False

		try:
			self.doc = xmltree.parse(__tftxml__)
		except:
			text = __addon__.getLocalizedString(32504)
			notify(__addonname__, text, 5000, __icon__, xbmc.LOGWARNING)
			return False

		return True


	def xmlToList(self):
		text = __addon__.getLocalizedString(32505)

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
				notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
				xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s> tag for the mode is missing' % mode)
				return False

		xbmc_log(xbmc.LOGNOTICE, "Loaded layout from %s successfully" % (__tftxml__))
		return True



	def setupList(self, node, mode):
		# clear the list for the mode
		self.modeslist[mode] = []

		# begin every list with the background color black
		# when a background color is set in TFT.xml for the mode, then replace this
		self.modeslist[mode].append(['backgroundToDisplay', (0, 0, 0)])

		text = __addon__.getLocalizedString(32505)



		for child in node:
			opt = []


			# background
			if child.tag == 'background':
				opt.append('backgroundToDisplay')

				color = child.find('color')
				if color is not None:
					if isColorHex(color.text):  # from helper.py
						opt.append(hexToRGB(color.text))
					else:
						notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><color> %s has not the right format' % (node.tag, child.tag, color.text))
						return False
				else:
					notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing <color> tag' % (node.tag, child.tag))
					return False

				xbmc_log(xbmc.LOGDEBUG, '<%s><%s> %s' % (node.tag, child.tag, opt))
				self.modeslist[mode][0] = opt  # replace default background color



			# text
			elif child.tag == 'text':
				opt.append('textToDisplay')

				# display
				if child.get('display') is not None:
					if child.get('display').lower().find('$info') >= 0:
						if child.get('display').lower() == '$info[distroname]':
							opt.append(self.distro)
						elif xbmc.getInfoLabel(child.get('display')) is not None:
							opt.append(child.get('display'))
						else:
							notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
							xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> infolabel %s is unknown' % (node.tag, child.tag, child.attrib['display']))
							return False
					else:
						opt.append(child.get('display').encode('utf-8', 'ignore'))
				else:
					notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing display attribut' % (node.tag, child.tag))
					return False

				# visibility condition
				visible = child.find('visible')
				if visible is not None:
					if xbmc.getCondVisibility(visible.text) != None:
						opt.append(visible.text)
					else:
						notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><visible> condition %s is unknown' % (node.tag, child.tag, visible.text))
						return False
				else:
					opt.append('visible')

				# font
				font = child.find('font')
				if font is not None:
					if font.text == 'None':
						opt.append(font.text)
					elif os.path.isfile(os.path.join(__media__, font.text)):
						opt.append(os.path.join(__media__, font.text))
					else:
						notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><font> %s not found' % (node.tag, child.tag, font.text))
						return False
				else:
					notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing <font> tag' % (node.tag, child.tag))
					return False

				# size
				size = child.find('size')
				if size is not None:
					if isInteger(size.text):  # from helper.py
						opt.append(int(size.text))
					else:
						notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><size> %s is not an integer' % (node.tag, child.tag, size.text))
						return False
				else:
					notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing <size> tag' % (node.tag, child.tag))
					return False

				# color
				color = child.find('color')
				if color is not None:
					if isColorHex(color.text):  # from helper.py
						opt.append(hexToRGB(color.text))
					else:
						notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><color> %s has not the right format' % (node.tag, child.tag, color.text))
						return False
				else:
					notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing <color> tag' % (node.tag, child.tag))
					return False

				# xpos
				xpos = child.find('xpos')
				if xpos is not None:
					if xpos.text == 'center':
						centerx = self.display_w/2
						opt.append(centerx)
						opt.append(1)
					elif isInteger(xpos.text):
						opt.append(int(xpos.text))
						opt.append(0)
					else:
						notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><xpos> value %s is not supported' % (node.tag, child.tag, xpos.text))
						return False
				else:
					notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing <xpos> tag' % (node.tag, child.tag))
					return False

				# ypos
				ypos = child.find('ypos')
				if ypos is not None:
					if ypos.text == 'center':
						centery = self.display_h/2
						opt.append(centery)
						opt.append(1)
					elif isInteger(ypos.text):
						opt.append(int(ypos.text))
						opt.append(0)
					else:
						notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><ypos> value %s is not supported' % (node.tag, child.tag, ypos.text))
						return False
				else:
					notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing <ypos> tag' % (node.tag, child.tag))
					return False

				xbmc_log(xbmc.LOGDEBUG, '<%s><%s> %s' % (node.tag, child.tag, opt))
				self.modeslist[mode].append(opt)



			# image
			elif child.tag == 'image':
				opt.append('imageToDisplay')

				# path to the image
				if child.get('path') is not None:
					if child.get('path').lower() == '$info[distrologo]':
						imagepath = __media__ + '/' + self.distro.lower() + '.png'
						if not os.path.isfile(imagepath):
							imagepath = __media__ + '/' + 'kodi.png'
					elif os.path.isfile(child.get('path')):
						imagepath = child.get('path')
					elif os.path.isfile(os.path.join(__media__, child.get('path'))):
						imagepath = __media__ + '/' + child.get('path')
					else:
						imagepath = __media__ + '/' + 'error.png'
					opt.append(imagepath)
				else:
					notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing path attribut' % (node.tag, child.tag))
					return False

				# visibility condition
				visible = child.find('visible')
				if visible is not None:
					if xbmc.getCondVisibility(visible.text) != None:
						opt.append(visible.text)
					else:
						notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><visible> condition %s is unknown' % (node.tag, child.tag, visible.text))
						return False
				else:
					opt.append('visible')

				# resx
				resx = child.find('resx')
				if resx is not None:
					if isInteger(resx.text):  # from helper.py
						if int(resx.text) < 0:
							notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
							xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><resx> value can not be %s (negative)' % (node.tag, child.tag, resx.text))
							return False
						else:
							opt.append(int(resx.text))
					else:
						notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><resx> value %s is not supported' % (node.tag, child.tag, xpos.text))
						return False
				else:
					opt.append(0)

				# resy
				resy = child.find('resy')
				if resy is not None:
					if isInteger(resy.text):  # from helper.py
						if int(resy.text) < 0:
							notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
							xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><resy> value can not be %s (negative)' % (node.tag, child.tag, resy.text))
							return False
						else:
							opt.append(int(resy.text))
					else:
						notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><resy> value %s is not supported' % (node.tag, child.tag, xpos.text))
						return False
				else:
					opt.append(0)

				# xpos
				xpos = child.find('xpos')
				if xpos is not None:
					if xpos.text == 'center':
						centerx = self.display_w/2
						opt.append(centerx)
						opt.append(1)
					elif isInteger(xpos.text):
						opt.append(int(xpos.text))
						opt.append(0)
					else:
						notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><xpos> value %s is not supported' % (node.tag, child.tag, xpos.text))
						return False
				else:
					notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing <xpos> tag' % (node.tag, child.tag))
					return False

				# ypos
				ypos = child.find('ypos')
				if ypos is not None:
					if ypos.text == 'center':
						centery = self.display_h/2
						opt.append(centery)
						opt.append(1)
					elif isInteger(ypos.text):
						opt.append(int(ypos.text))
						opt.append(0)
					else:
						notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><ypos> value %s is not supported' % (node.tag, child.tag, ypos.text))
						return False
				else:
					notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing <ypos> tag' % (node.tag, child.tag))
					return False

				xbmc_log(xbmc.LOGDEBUG, '<%s><%s> %s' % (node.tag, child.tag, opt))
				self.modeslist[mode].append(opt)



			# progressbar
			elif child.tag == 'progressbar':
				opt.append('progressBarToDisplay')

				# width
				width = child.find('width')
				if width is not None:
					if isInteger(width.text):  # from helper.py
						if int(width.text) <= 0:
							notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
							xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><width> value should be greater 0, yours %s' % (node.tag, child.tag, width.text))
							return False
						else:
							opt.append(int(width.text))
					else:
						notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><width> value %s is not supported' % (node.tag, child.tag, xpos.text))
						return False
				else:
					notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing <width> tag' % (node.tag, child.tag))
					return False

				# height
				height = child.find('height')
				if height is not None:
					if isInteger(height.text):  # from helper.py
						if int(height.text) < 0:
							notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
							xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><height> value should be greater 0, yours %s' % (node.tag, child.tag, height.text))
							return False
						else:
							opt.append(int(height.text))
					else:
						notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><height> value %s is not supported' % (node.tag, child.tag, height.text))
						return False
				else:
					notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing <height> tag' % (node.tag, child.tag))
					return False

				# color
				color = child.find('barcolor')
				if color is not None:
					if isColorHex(color.text):  # from helper.py
						opt.append(hexToRGB(color.text))
					else:
						notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
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
						notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><progresscolor> %s has not the right format' % (node.tag, child.tag, color.text))
						return False
				else:
					opt.append(hexToRGB('#0000FF')) # blue

				# border
				border = child.find('border')
				if border is not None:
					if isInteger(border.text):  # from helper.py
						if int(border.text) < 0:
							notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
							xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><border> value can not be %s (negative)' % (node.tag, child.tag, border.text))
							return False
						else:
							opt.append(int(border.text))
					else:
						notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
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
						notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><bordercolor> %s has not the right format' % (node.tag, child.tag, color.text))
						return False
				else:
					opt.append(hexToRGB('#FFFFFF')) # white

				# xpos
				xpos = child.find('xpos')
				if xpos is not None:
					if xpos.text == 'center':
						centerx = self.display_w/2
						opt.append(centerx)
						opt.append(1)
					elif isInteger(xpos.text):  # from helper.py
						opt.append(int(xpos.text))
						opt.append(0)
					else:
						notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><xpos> value %s is not supported' % (node.tag, child.tag, xpos.text))
						return False
				else:
					notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing <xpos> tag' % (node.tag, child.tag))
					return False

				# ypos
				ypos = child.find('ypos')
				if ypos is not None:
					if ypos.text == 'center':
						centery = self.display_h/2
						opt.append(centery)
						opt.append(1)
					elif isInteger(ypos.text):  # from helper.py
						opt.append(int(ypos.text))
						opt.append(0)
					else:
						notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><ypos> value %s is not supported' % (node.tag, child.tag, ypos.text))
						return False
				else:
					notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing <ypos> tag' % (node.tag, child.tag))
					return False

				xbmc_log(xbmc.LOGDEBUG, '<%s><%s> %s' % (node.tag, child.tag, opt))
				self.modeslist[mode].append(opt)



			# <tag> is not supported
			else:
				notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
				xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s> the tag <%s> is not supported' % (node.tag, child.tag))
				return False



		xbmc_log(xbmc.LOGNOTICE, '%s %s' % (mode, self.modeslist[mode]))
		return True

