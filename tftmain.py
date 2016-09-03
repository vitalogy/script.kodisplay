import os
import sys
import time
import xbmc
import xbmcaddon
import xbmcgui

from ctypes import *
#from array import array
from xml.etree import ElementTree as xmltree


__addon__         = xbmcaddon.Addon()
__addonversion__  = __addon__.getAddonInfo('version')
__addonid__       = __addon__.getAddonInfo('id')
__addonname__     = __addon__.getAddonInfo('name')
__cwd__           = __addon__.getAddonInfo('path')
__icon__          = os.path.join(__cwd__, 'icon.png')
__lib__           = os.path.join(__cwd__, 'resources', 'lib')
__media__         = os.path.join(__cwd__, 'resources', 'media')
__settings__      = xbmcaddon.Addon(id=__addonid__)
__tftxml__        = xbmc.translatePath( os.path.join("special://masterprofile","TFT.xml"))
__tftdefaultxml__ = xbmc.translatePath( os.path.join(__cwd__, "resources", "TFT.xml.defaults"))

BASE_RESOURCE_PATH = xbmc.translatePath(__lib__)
sys.path.insert(0, BASE_RESOURCE_PATH)

from helper import *
from currentmode import *
import config as glob

glob.navTimer = time.time()

os.environ["SDL_VIDEODRIVER"] = "fbcon"
os.environ["SDL_FBDEV"] = "/dev/fb1"

glob.distro = getDistroName() # from helper.py
xbmc_log(xbmc.LOGNOTICE, 'Running on ' + glob.distro)

if glob.distro == 'LibreELEC':
	# running on LibreELEC
	#  1.   check for existing lib.tgz (lib.tgz includes SDL-1.2 & pygame)
	#  1.1.   if the directories SDL and pygame exist, delete them
	#  1.2.   unpack lib.tgz, then move it to lib.tgz.x
	#  2.   load the needed shared libraries

	__libtgz__ = os.path.join(__lib__, 'lib.tgz')
	if os.path.exists(__libtgz__):
		xbmc_log(xbmc.LOGNOTICE, 'Will extracting needed libs from lib.tgz')
		# remove the directories SDL and pygame if they exist
		if os.path.isdir(os.path.join(__lib__, 'SDL')):
			xbmc_log(xbmc.LOGWARNING, 'Directory SDL exist, so remove it')
			execute('rm -rf ' + __lib__ + '/' + 'SDL')
		if os.path.isdir(os.path.join(__lib__, 'pygame')):
			xbmc_log(xbmc.LOGWARNING, 'Directory pygame exist, so remove it')
			execute('rm -rf ' + __lib__ + '/' + 'pygame')

		try:
			execute('tar xf ' + __libtgz__ + ' -C ' + __lib__)
			execute('mv ' + __libtgz__ + ' ' + __libtgz__ + '.x')
			xbmc_log(xbmc.LOGNOTICE, 'Extracting libs from lib.tgz was successfully')
		except:
			xbmc_log(xbmc.LOGWARNING, 'Extracting libs from lib.tgz goes wrong')
			sys.exit(1)

	try:
		cdll.LoadLibrary(os.path.join(__lib__, 'SDL', 'libSDL.so'))
		cdll.LoadLibrary(os.path.join(__lib__, 'SDL', 'libSDL_image.so'))
		cdll.LoadLibrary(os.path.join(__lib__, 'SDL', 'libSDL_ttf.so'))
	except:
		text = __settings__.getLocalizedString(32500)
		notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
		sys.exit(1)


try:
	import pygame
	from pygame.locals import *
except:
	text = __settings__.getLocalizedString(32501)
	notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
	sys.exit(1)


class displayProgressBar():
	def __init__(self, width, height, bkcolor, border, bordercolor, barcolor, xpos, cx, ypos, cy):
		self.rect_bar = pygame.Rect(xpos, ypos, width, height)
		self.border = border

		playtime = timeToSecs(xbmc.getInfoLabel("Player.Time(hh:mm:ss)"))
		duration = timeToSecs(xbmc.getInfoLabel("Player.Duration(hh:mm:ss)"))

		if playtime > 0:
			percent = int(( 1. * self.rect_bar.width / duration ) * playtime)
		else:
			percent = 0

		self.rect_done = pygame.Rect(self.rect_bar)
		self.rect_done.width = percent

		self.intbkcolor = hexToRGB(bkcolor)
		self.intbordercolor = hexToRGB(bordercolor)
		self.intbarcolor = hexToRGB(barcolor)

#      ToDo: implement 'center'
#		self.rectpos = self.rect_bar.get_rect()
#		if xpos < 0:
#			self.rectpos.x = glob.display_w - self.rect_bar.get_width() + xpos
#		else:
#			if cx == 1:
#				self.rectpos.centerx = xpos
#			else:
#				self.rectpos.x = xpos
#		if ypos < 0:
#			self.rectpos.y = glob.display_h - self.rect_bar.get_height() + ypos
#		else:
#			if cy == 1:
#				self.rectpos.centerx = ypos
#			else:
#				self.rectpos.y = ypos


	def draw(self, surface):
		pygame.draw.rect(surface, self.intbkcolor, self.rect_bar )
		pygame.draw.rect(surface, self.intbarcolor, self.rect_done )
		pygame.draw.rect(surface, self.intbordercolor, self.rect_bar, self.border)


class displayImage():
	def __init__(self, name, resx, resy, xpos, cx, ypos, cy):
		self.image = pygame.image.load(name)
		if resx > 0 or resy > 0:
			self.image = pygame.transform.scale(self.image, aspect_scale(self.image, (resx, resy)))

		self.imagepos = self.image.get_rect()
		if xpos < 0:
			self.imagepos.x = glob.display_w - self.image.get_width() + xpos
		else:
			if cx == 1:
				self.imagepos.centerx = xpos
			else:
				self.imagepos.x = xpos
		if ypos < 0:
			self.imagepos.y = glob.display_h - self.image.get_height() + ypos
		else:
			if cy == 1:
				self.imagepos.centerx = ypos
			else:
				self.imagepos.y = ypos

	def draw(self, surface):
		surface.blit(self.image, self.imagepos)


class displayText():
	def __init__(self, text, font, size, color, xpos, cx, ypos, cy):
		self.font = pygame.font.Font(None, size)
		self.image = self.font.render(text, 1, color)
		self.textpos = self.image.get_rect()

		if xpos < 0:
			self.textpos.x = glob.display_w - self.image.get_width() + xpos
		else:
			if cx == 1:
				self.textpos.centerx = xpos
			else:
				self.textpos.x = xpos

		if ypos < 0:
			self.textpos.y = glob.display_h - self.image.get_height() + ypos
		else:
			if cy == 1:
				self.textpos.centery = ypos
			else:
				self.textpos.y = ypos

	def draw(self, surface):
		surface.blit(self.image, self.textpos)



class TFT():
	def __init__(self):
		pygame.display.init()
		pygame.font.init()
		pygame.mouse.set_visible(False)

		self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
		self.clock = pygame.time.Clock()
		TFTinfo = pygame.display.Info()
		glob.display_w = TFTinfo.current_w
		glob.display_h = TFTinfo.current_h
		self.background = pygame.Surface(self.screen.get_size())
		self.tftmodes = [None] * TFT_MODE.MAX_MODES


	def checkFileXML(self):
		ret = True
		if not os.path.isfile(__tftxml__):
			if not os.path.isfile(__tftdefaultxml__):
				text = __settings__.getLocalizedString(32502)
				notify(__addonname__, text, 5000, __icon__, xbmc.LOGWARNING)
				return False
			else:
				try:
					shutil.copy2(__tftdefaultxml__, __tftxml__)
				except:
					text = __settings__.getLocalizedString(32503)
					notify(__addonname__, text, 5000, __icon__, xbmc.LOGWARNING)
					return False

		try:
			self.doc = xmltree.parse(__tftxml__)
		except:
			text = __settings__.getLocalizedString(32504)
			notify(__addonname__, text, 5000, __icon__, xbmc.LOGWARNING)
			return False

		xbmc_log(xbmc.LOGNOTICE, "Loading settings from %s" % (__tftxml__))
		return ret



	def setupArray(self, node, mode):
		self.tftmodes[mode] = []
		# begin every list with the background color black
		# when a background color is set in TFT.xml for the mode, then replace this
		self.tftmodes[mode].insert(0, 'backgroundToDisplay|#000000')

		text = __settings__.getLocalizedString(32505)

		for child in node:
			opt = ""
			sep = ';'



			if child.tag == 'background':
				opt = 'backgroundToDisplay|'
				color = child.find('color')
				if color is not None:
					if isColorHex(color.text):  # from helper.py
						opt = opt + color.text
					else:
						notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><color> %s has not the right format' % (node.tag, child.tag, color.text))
						return False
				else:
					notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing <color> tag' % (node.tag, child.tag))
					return False

				xbmc_log(xbmc.LOGDEBUG, '<%s><%s> %s' % (node.tag, child.tag, opt))
				self.tftmodes[mode][0] = opt  # replace default background color



			elif child.tag == 'text':
				opt = 'textToDisplay|'

				if child.get('display') is not None:
					if child.get('display').lower() == '$info[distroname]':
						opt = opt + glob.distro + sep
					else:
						opt = opt + child.attrib['display'] + sep
				else:
					notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing display attribut' % (node.tag, child.tag))
					return False

				font = child.find('font')
				if font is not None:
					if os.path.isfile(os.path.join(__media__, font.text)) or font.text == 'None':
						opt = opt + font.text + sep
					else:
						notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><font> %s not found' % (node.tag, child.tag, font.text))
						return False
				else:
					notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing <font> tag' % (node.tag, child.tag))
					return False

				size = child.find('size')
				if size is not None:
					if isInteger(size.text):  # from helper.py
						opt = opt + size.text + sep
					else:
						notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><size> %s is not an integer' % (node.tag, child.tag, size.text))
						return False
				else:
					notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing <size> tag' % (node.tag, child.tag))
					return False

				color = child.find('color')
				if color is not None:
					if isColorHex(color.text):  # from helper.py
						opt = opt + color.text + sep
					else:
						notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><color> %s has not the right format' % (node.tag, child.tag, color.text))
						return False
				else:
					notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing <color> tag' % (node.tag, child.tag))
					return False

				xpos = child.find('xpos')
				if xpos is not None:
					if isInteger(xpos.text):  # from helper.py
						opt = opt + xpos.text + sep + '0' + sep
					elif xpos.text == 'center':
						cpos = str(glob.display_w/2)
						opt = opt + cpos + sep + '1' + sep
					else:
						notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><xpos> value %s is not supported' % (node.tag, child.tag, xpos.text))
						return False
				else:
					notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing <xpos> tag' % (node.tag, child.tag))
					return False

				ypos = child.find('ypos')
				if ypos is not None:
					if isInteger(ypos.text):  # from helper.py
						opt = opt + ypos.text + sep + '0'
					elif ypos.text == 'center':
						cpos = str(glob.display_h/2)
						opt = opt + cpos + sep + '1'
					else:
						notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><ypos> value %s is not supported' % (node.tag, child.tag, ypos.text))
						return False
				else:
					notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing <ypos> tag' % (node.tag, child.tag))
					return False

				xbmc_log(xbmc.LOGDEBUG, '<%s><%s> %s' % (node.tag, child.tag, opt))
				self.tftmodes[mode].append(opt)



			elif child.tag == 'image':
				opt = 'imageToDisplay|'

				if child.get('path') is not None:
					if child.get('path').lower() == '$info[distrologo]':
						imagepath = __media__ + '/' + glob.distro.lower() + '.png'
						if not os.path.isfile(imagepath):
							imagepath = __media__ + '/' + 'kodi.png'
					elif os.path.isfile(child.get('path')):
						imagepath = child.get('path')
					elif os.path.isfile(os.path.join(__media__, child.get('path'))):
						imagepath = __media__ + '/' + child.get('path')
					else:
						imagepath = __media__ + '/' + 'error.png'
					opt = opt + imagepath + sep
				else:
					notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing path attribut' % (node.tag, child.tag))
					return False

				resx = child.find('resx')
				if resx is not None:
					if isInteger(resx.text):  # from helper.py
						if int(resx.text) < 0:
							notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
							xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><resx> value can not be %s (negative)' % (node.tag, child.tag, resx.text))
							return False
						else:
							opt = opt + resx.text + sep
					else:
						notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><resx> value %s is not supported' % (node.tag, child.tag, xpos.text))
						return False
				else:
					opt = opt + '0' + sep

				resy = child.find('resy')
				if resy is not None:
					if isInteger(resy.text):  # from helper.py
						if int(resy.text) < 0:
							notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
							xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><resy> value can not be %s (negative)' % (node.tag, child.tag, resy.text))
							return False
						else:
							opt = opt + resy.text + sep
					else:
						notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><resy> value %s is not supported' % (node.tag, child.tag, xpos.text))
						return False
				else:
					opt = opt + '0' + sep

				xpos = child.find('xpos')
				if xpos is not None:
					if isInteger(xpos.text):  # from helper.py
						opt = opt + xpos.text + sep + '0' + sep
					elif xpos.text == 'center':
						cpos = str(glob.display_w/2)
						opt = opt + cpos + sep + '1' + sep
					else:
						notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><xpos> value %s is not supported' % (node.tag, child.tag, xpos.text))
						return False
				else:
					notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing <xpos> tag' % (node.tag, child.tag))
					return False

				ypos = child.find('ypos')
				if ypos is not None:
					if isInteger(ypos.text):  # from helper.py
						opt = opt + ypos.text + sep + '0'
					elif ypos.text == 'center':
						cpos = str(glob.display_h/2)
						opt = opt + cpos + sep + '1'
					else:
						notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><ypos> value %s is not supported' % (node.tag, child.tag, ypos.text))
						return False
				else:
					notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing <ypos> tag' % (node.tag, child.tag))
					return False

				xbmc_log(xbmc.LOGDEBUG, '<%s><%s> %s' % (node.tag, child.tag, opt))
				self.tftmodes[mode].append(opt)



			elif child.tag == 'progressbar':
				opt = 'progressBarToDisplay|'

				width = child.find('width')
				if width is not None:
					if isInteger(width.text):  # from helper.py
						if int(width.text) < 0:
							notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
							xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><width> value can not be %s (negative)' % (node.tag, child.tag, width.text))
							return False
						else:
							opt = opt + width.text + sep
					else:
						notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><width> value %s is not supported' % (node.tag, child.tag, xpos.text))
						return False
				else:
					notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing <width> tag' % (node.tag, child.tag))
					return False

				height = child.find('height')
				if height is not None:
					if isInteger(height.text):  # from helper.py
						if int(height.text) < 0:
							notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
							xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><height> value can not be %s (negative)' % (node.tag, child.tag, height.text))
							return False
						else:
							opt = opt + height.text + sep
					else:
						notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><height> value %s is not supported' % (node.tag, child.tag, height.text))
						return False
				else:
					notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing <height> tag' % (node.tag, child.tag))
					return False

				color = child.find('barcolor')
				if color is not None:
					if isColorHex(color.text):  # from helper.py
						opt = opt + color.text + sep
					else:
						notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><barcolor> %s has not the right format' % (node.tag, child.tag, color.text))
						return False
				else:
					opt = opt + '#FF0000' + sep

				border = child.find('border')
				if border is not None:
					if isInteger(border.text):  # from helper.py
						if int(border.text) < 0:
							notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
							xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><border> value can not be %s (negative)' % (node.tag, child.tag, border.text))
							return False
						else:
							opt = opt + border.text + sep
					else:
						notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><border> value %s is not supported' % (node.tag, child.tag, border.text))
						return False
				else:
					opt = opt + '2' + sep

				color = child.find('bordercolor')
				if color is not None:
					if isColorHex(color.text):  # from helper.py
						opt = opt + color.text + sep
					else:
						notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><bordercolor> %s has not the right format' % (node.tag, child.tag, color.text))
						return False
				else:
					opt = opt + '#FFFFFF' + sep

				color = child.find('progresscolor')
				if color is not None:
					if isColorHex(color.text):  # from helper.py
						opt = opt + color.text + sep
					else:
						notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><progresscolor> %s has not the right format' % (node.tag, child.tag, color.text))
						return False
				else:
					opt = opt + '#0000FF' + sep

				xpos = child.find('xpos')
				if xpos is not None:
					if isInteger(xpos.text):  # from helper.py
						opt = opt + xpos.text + sep + '0' + sep
					elif xpos.text == 'center':
						cpos = str(glob.display_w/2)
						opt = opt + cpos + sep + '1' + sep
					else:
						notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><xpos> value %s is not supported' % (node.tag, child.tag, xpos.text))
						return False
				else:
					notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing <xpos> tag' % (node.tag, child.tag))
					return False

				ypos = child.find('ypos')
				if ypos is not None:
					if isInteger(ypos.text):  # from helper.py
						opt = opt + ypos.text + sep + '0'
					elif ypos.text == 'center':
						cpos = str(glob.display_h/2)
						opt = opt + cpos + sep + '1'
					else:
						notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
						xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s><ypos> value %s is not supported' % (node.tag, child.tag, ypos.text))
						return False
				else:
					notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
					xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s><%s> missing <ypos> tag' % (node.tag, child.tag))
					return False

				xbmc_log(xbmc.LOGDEBUG, '<%s><%s> %s' % (node.tag, child.tag, opt))
				self.tftmodes[mode].append(opt)



			else:
				notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
				xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s> the tag <%s> is not supported' % (node.tag, child.tag))
				return False



		xbmc_log(xbmc.LOGWARNING, '%s %s' % (mode, self.tftmodes[mode]))
		return True

	def xmlToArray(self):
		text = __settings__.getLocalizedString(32503)
		root = self.doc.getroot()

		for mode in glob.modes:
			tmpMode = root.find(mode)
			if tmpMode is not None:
				tftmode = 'TFT_MODE.' + mode.upper()
				if not self.setupArray(tmpMode, eval(tftmode)):
					return False
			else:
				notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
				xbmc_log(xbmc.LOGWARNING, 'TFT.xml: <%s> tag for the mode is missing' % mode)
				return False

		return True


	def backgroundToDisplay(self, color):
		intcolor = hexToRGB(color)
		self.background.fill(intcolor)

	def textToDisplay(self, text, font, size, color, xpos, cx, ypos, cy):
		if text.lower().find("$info") >= 0:
			text = xbmc.getInfoLabel(text).decode('utf-8')
		intcolor = hexToRGB(color)
		t = displayText(text, font, int(size), intcolor, int(xpos), int(cx), int(ypos), int(cy))
		t.draw(self.background)

	def imageToDisplay(self, name, resx, resy, xpos, cx, ypos, cy):
		i = displayImage(name, int(resx), int(resy), int(xpos), int(cx), int(ypos), int(cy))
		i.draw(self.background)

	def progressBarToDisplay(self, width, heigth, bkcolor, border, bordercolor, barcolor, xpos, cx, ypos, cy):
		p = displayProgressBar(int(width), int(heigth), bkcolor, int(border), bordercolor, barcolor, int(xpos), int(cx), int(ypos), int(cy))
		p.draw(self.background)


	def drawToDisplay(self, mode):
		for i in range(0, len(self.tftmodes[mode])):
			func, values = self.tftmodes[mode][i].split('|')
			values = values.split(';')
#			xbmc_log(xbmc.LOGNOTICE, str(func) + '   ' + str(values))
#			time.sleep(1)
			getattr(self, func)(*values)


	def run(self):
		running = True
		xbmc_log(xbmc.LOGNOTICE, 'Display Resolution: ' + str(glob.display_w) + 'x' + str(glob.display_h))

		if self.checkFileXML():
			if self.xmlToArray():
				self.drawToDisplay(TFT_MODE.STARTSCREEN)
				# Blit everything to the screen
				self.screen.blit(self.background, (0, 0))
				pygame.display.flip()
				time.sleep(3)
			else:
				running = False
		else:
			running = False

		# Event loop
		while (not xbmc.abortRequested) and running:

			if isNavigation():
				mode = TFT_MODE.NAVIGATION
			elif xbmc.getCondVisibility('Player.HasVideo'):
				mode = TFT_MODE.VIDEO
			elif xbmc.getCondVisibility('Player.HasAudio'):
				mode = TFT_MODE.MUSIC
			elif xbmc.getCondVisibility('System.ScreenSaverActive'):
				mode = TFT_MODE.SCREENSAVER
			else:
				mode = TFT_MODE.GENERAL

			self.drawToDisplay(mode)
			# Blit everything to the screen
			self.screen.blit(self.background, (0, 0))
			pygame.display.flip()

			self.clock.tick(5)

		pygame.quit()
		xbmc_log(xbmc.LOGNOTICE, 'Closing')
		sys.exit()

if (__name__ == "__main__"):
	TFT().run()
