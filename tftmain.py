import os
import sys
import time
import xbmc
import xbmcaddon
import xbmcgui

from ctypes import *
from array import array
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
from color import *
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
		# remove the dir SDL and pygame if they exist
		if os.path.isdir(os.path.join(__lib__, 'SDL')):
			execute('rm -rf ' + __lib__ + '/' + 'SDL')
		if os.path.isdir(os.path.join(__lib__, 'pygame')):
			execute('rm -rf ' + __lib__ + '/' + 'pygame')

		notify(__addonname__, 'Extracting libs from lib.tgz', 5000, __icon__, xbmc.LOGNOTICE)
		execute('tar xf ' + __libtgz__ + ' -C ' + __lib__)
		execute('mv ' + __libtgz__ + ' ' + __libtgz__ + '.x')

	try:
		cdll.LoadLibrary(os.path.join(__lib__, 'SDL', 'libSDL.so'))
		cdll.LoadLibrary(os.path.join(__lib__, 'SDL', 'libSDL_image.so'))
		cdll.LoadLibrary(os.path.join(__lib__, 'SDL', 'libSDL_ttf.so'))
	except:
		notify(__addonname__, 'Loading SDL failed', 10000, __icon__, xbmc.LOGERROR)
		sys.exit(1)


try:
	import pygame
	from pygame.locals import *
except:
	notify(__addonname__, 'Importing pygame failed', 10000, __icon__, xbmc.LOGERROR)
	sys.exit(1)



class displayImage():
	def __init__(self, name, resx, resy, xpos, ypos, cx, cy):
		if os.path.isfile(name):
			self.image = pygame.image.load(name)
		elif os.path.isfile(os.path.join(__media__, name)):
			self.image = pygame.image.load(os.path.join(__media__, name))
		else:
			self.image = pygame.image.load(os.path.join(__media__, 'error.png'))

		if resx < 0 or resy < 0:
			resx = 0
			resy = 0
		if resx > 0 and resy > 0:
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
	def __init__(self, text, font, size, color, xpos, ypos, cx, cy):
		self.font = pygame.font.Font(None, size)
		self.image = self.font.render(text, 1, (255,255,255))
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
				text = __settings__.getLocalizedString(32500)
				notify(__addonname__, text, 5000, __icon__, xbmc.LOGERROR)
				return False
			else:
				try:
					shutil.copy2(__tftdefaultxml__, __tftxml__)
				except:
					text = __settings__.getLocalizedString(32501)
					notify(__addonname__, text, 5000, __icon__, xbmc.LOGERROR)
					return False

		try:
			self.doc = xmltree.parse(__tftxml__)
		except:
			text = __settings__.getLocalizedString(32502)
			notify(__addonname__, text, 5000, __icon__, xbmc.LOGERROR)
			return False

		xbmc_log(xbmc.LOGNOTICE, "Loading settings from %s" % (__tftxml__))
		return ret


	def setupArray(self, node, mode):
		self.tftmodes[mode] = []

		for child in node:
			opt = ""
			if child.tag == 'text':
				opt = 'textToDisplay;' \
					+ child.attrib['display'] + ',' \
					+ child.find('font').text + ',' \
					+ child.find('size').text + ',' \
					+ child.find('color').text + ',' \
					+ child.find('xpos').text + ',' \
					+ child.find('ypos').text
				self.tftmodes[mode].append(opt)
			elif child.tag == 'image':
				opt = 'imageToDisplay;' \
					+ child.attrib['path'] + ',' \
					+ child.find('resx').text + ',' \
					+ child.find('resy').text + ',' \
					+ child.find('xpos').text + ',' \
					+ child.find('ypos').text
				self.tftmodes[mode].append(opt)


	def xmlToArray(self):
		root = self.doc.getroot()

		tmpMode = root.find('startlogo')
		self.setupArray(tmpMode, TFT_MODE.STARTLOGO)

		tmpMode = root.find('general')
		self.setupArray(tmpMode, TFT_MODE.GENERAL)

		tmpMode = root.find('navigation')
		self.setupArray(tmpMode, TFT_MODE.NAVIGATION)

		tmpMode = root.find('music')
		self.setupArray(tmpMode, TFT_MODE.MUSIC)

		tmpMode = root.find('video')
		self.setupArray(tmpMode, TFT_MODE.VIDEO)

		tmpMode = root.find('pvr')
		self.setupArray(tmpMode, TFT_MODE.PVR)


	def textToDisplay(self, text, font, size, color, xpos, ypos):
		cx = 0
		cy = 0

		if text.lower().find("$info") >= 0:
			if text.lower().find("$info[distroname]") >= 0:
				text = glob.distro
			else:
				text = xbmc.getInfoLabel(text)
		if xpos == 'center':
			xpos = str(glob.display_w/2)
			cx = 1
		if ypos == 'center':
			ypos = str(glob.display_h/2)
			cx = 1
		t = displayText(text, font, int(size), color, int(xpos), int(ypos), cx, cy)
		t.draw(self.background)

	def imageToDisplay(self, name, resx, resy, xpos, ypos):
		cx = 0
		cy = 0

		if name.lower().find("$info[distrologo]") >= 0:
			logopath = __media__ + '/' + glob.distro.lower() + '.' + 'png'
			if not os.path.isfile(logopath):
				logopath = __media__ + '/' + 'kodi.png'
			name = logopath
		if xpos == 'center':
			xpos = str(glob.display_w/2)
			cx = 1
		if ypos == 'center':
			ypos = str(glob.display_h/2)
			cy = 1
		i = displayImage(name, int(resx), int(resy), int(xpos), int(ypos), cx, cy)
		i.draw(self.background)


	def drawToDisplay(self, mode):
		for i in range(0, len(self.tftmodes[mode])):
			func, values = self.tftmodes[mode][i].split(';')
			values = values.split(',')
#			xbmc_log(xbmc.LOGNOTICE, str(func) + '   ' + str(values))
#			time.sleep(1)
			getattr(self, func)(*values)


	def run(self):
		running = True
		xbmc_log(xbmc.LOGNOTICE, 'Display Resolution: ' + str(glob.display_w) + 'x' + str(glob.display_h))

		if not self.checkFileXML():
			running = False

		if running:
			self.xmlToArray()
			self.drawToDisplay(TFT_MODE.STARTLOGO)
			# Blit everything to the screen
			self.screen.blit(self.background, (0, 0))
			pygame.display.flip()
			time.sleep(3)

		# Event loop
		while (not xbmc.abortRequested) and running:
			self.background.fill(COLOR.BLACK)

			if isNavigation():
				mode = TFT_MODE.NAVIGATION
#			elif playerIsPlayingVideo():
#				mode = TFT_MODE.VIDEO
#			elif playerIsPlayingAudio():
#				mode = TFT_MODE.MUSIC
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
