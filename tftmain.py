import os
import sys
import time
import xbmc
import xbmcaddon
import xbmcgui
#import string

from ctypes import *


__addon__         = xbmcaddon.Addon()
__addonversion__  = __addon__.getAddonInfo('version')
__addonid__       = __addon__.getAddonInfo('id')
__addonname__     = __addon__.getAddonInfo('name')
__path__          = __addon__.getAddonInfo('path')
__icon__          = os.path.join(__path__, 'icon.png')
__lib__           = os.path.join(__path__, 'resources', 'lib')
__media__         = os.path.join(__path__, 'resources', 'media')

BASE_RESOURCE_PATH = xbmc.translatePath(__lib__)
sys.path.insert(0, BASE_RESOURCE_PATH)

from helper import *
from currentmode import *
from modeslist import ModesList
import config as glob

glob.navTimer = time.time()

os.environ["SDL_VIDEODRIVER"] = "fbcon"
os.environ["SDL_FBDEV"] = "/dev/fb1"

distro = getDistroName() # from helper.py
xbmc_log(xbmc.LOGNOTICE, 'Version %s running on %s' %(__addonversion__, distro))

if distro == 'LibreELEC':
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
		text = __addon__.getLocalizedString(32500)
		notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
		sys.exit(1)


try:
	import pygame
	from pygame.locals import *
except:
	text = __addon__.getLocalizedString(32501)
	notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
	sys.exit(1)





class MyMonitor(xbmc.Monitor):
	def __init__(self, *args, **kwargs):
		xbmc.Monitor.__init__(self)
		self.update_settings = kwargs['update_settings']
		xbmc_log(xbmc.LOGDEBUG, 'Monitor initalized')

	def onSettingsChanged(self):
		xbmc_log(xbmc.LOGNOTICE, 'Settings changed, perform update')
		self.update_settings()

	def onScreensaverDeactivated(self):
		ScreensaverRunning = False

	def onScreensaverActivated(self):
		ScreensaverRunning = True




class TFT():
	def __init__(self):
		pygame.display.init()
		pygame.font.init()
		pygame.mouse.set_visible(False)

		self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
		self.clock = pygame.time.Clock()
		TFTinfo = pygame.display.Info()
		self.display_w = TFTinfo.current_w
		self.display_h = TFTinfo.current_h
		self.background = pygame.Surface(self.screen.get_size())

		self.running = True
		self.distro = distro
		self.readSettings()

		xbmc_log(xbmc.LOGNOTICE, 'Display Resolution: ' + str(self.display_w) + 'x' + str(self.display_h))

		self.Monitor = MyMonitor(update_settings = self.readSettings)
		self.run()


	def readSettings(self):
		xbmc_log(xbmc.LOGNOTICE, 'Reading addon settings')
		self.fps = int(__addon__.getSetting('fps'))
		self.navtimeout = int(__addon__.getSetting('navtimeout'))
		self.displaystartscreen = bool(__addon__.getSetting('displaystartscreen'))
		self.timestartscreen = int(__addon__.getSetting('startscreentime'))
		glob.addonDebug = bool(__addon__.getSetting('debug'))

		self.wait = round(float(1)/self.fps, 3)

		# setup modeslist
		self.tftModes = ModesList(self.distro, self.display_w, self.display_h) # from modeslist.py
		if not self.tftModes.xmlToList():
			self.running = False
		self.tftmodeslist = self.tftModes.returnModes()


	def backgroundToDisplay(self, color):
		self.background.fill(color)


	def textToDisplay(self, text, condition, font, size, color, xpos, cx, ypos, cy):
		if xbmc.getCondVisibility(condition) or condition == 'visible':
#			xbmc_log(xbmc.LOGNOTICE, 'Text vor: %s' % text)
			if text.lower().find('$info') >= 0:
				text = xbmc.getInfoLabel(text)
#				xbmc_log(xbmc.LOGNOTICE, 'Text nach1: %s' % text)

#				text = xbmc.getInfoLabel(text).encode('utf-8', 'ignore')
#				xbmc_log(xbmc.LOGNOTICE, 'Text nach2: %s' % text)

			if font == 'None':
				self.font = pygame.font.Font(None, size)
			else:
				self.font = pygame.font.Font(font, size)
			self.image = self.font.render(text, 1, color)
			self.textpos = self.image.get_rect()

			if cx == 0:
				if int(xpos) < 0:
					self.textpos.x = self.display_w - self.image.get_width() + xpos
				else:
					self.textpos.x = int(xpos)
			else:
				self.textpos.centerx = xpos

			if cy == 0:
				if int(ypos) < 0:
					self.textpos.y = self.display_h - self.image.get_height() + ypos
				else:
					self.textpos.y = int(ypos)
			else:
				self.textpos.centery = ypos

			self.background.blit(self.image, self.textpos)


	def imageToDisplay(self, imgpath, condition, resx, resy, xpos, cx, ypos, cy):
		if xbmc.getCondVisibility(condition) or condition == 'visible':
			self.image = pygame.image.load(imgpath)
			if resx > 0 and resy > 0:
				self.image = pygame.transform.scale(self.image, aspect_scale(self.image, (int(resx), int(resy))))
			self.imagepos = self.image.get_rect()

			if cx == 0:
				if xpos < 0:
					self.imagepos.x = self.display_w - self.image.get_width() + xpos
				else:
					self.imagepos.x = xpos
			else:
				self.imagepos.centerx = xpos

			if cy == 0:
				if ypos < 0:
					self.imagepos.y = self.display_h - self.image.get_height() + ypos
				else:
					self.imagepos.y = ypos
			else:
				self.imagepos.centery = ypos

			self.background.blit(self.image, self.imagepos)


	def progressBarToDisplay(self, width, height, barcolor, progresscolor, border, bordercolor, xpos, cx, ypos, cy):
		progbar = pygame.Rect(0, 0, width, height)

		if cx == 0:
			if xpos < 0:
				progbar.x = self.display_w - width + xpos
			else:
				progbar.x = xpos
		else:
			progbar.centerx = xpos

		if cy == 0:
			if ypos < 0:
				progbar.y = self.display_h - height + ypos
			else:
				progbar.y = ypos
		else:
			progbar.centery = ypos

		# timeToSecs from helper.py
		playtime = timeToSecs(xbmc.getInfoLabel("Player.Time(hh:mm:ss)"))
		duration = timeToSecs(xbmc.getInfoLabel("Player.Duration(hh:mm:ss)"))

		if playtime > 0:
			percent = int(( 1. * progbar.width / duration ) * playtime)
		else:
			percent = 0

		progbar_done = pygame.Rect(progbar)
		progbar_done.width = percent
		pygame.draw.rect(self.background, barcolor, progbar )
		pygame.draw.rect(self.background, progresscolor, progbar_done )
		if border > 0:
			pygame.draw.rect(self.background, bordercolor, progbar, border)

	def drawToDisplay(self, mode):
		for i in range(0, len(self.tftmodeslist[mode])):
			func = self.tftmodeslist[mode][i][0]
			values = self.tftmodeslist[mode][i][1:]
			getattr(self, func)(*values)



	def run(self):

		if self.running and self.displaystartscreen:
			self.drawToDisplay(TFT_MODE.STARTSCREEN)
			self.screen.blit(self.background, (0, 0))
			pygame.display.flip()
			time.sleep(self.timestartscreen)

		# Event loop
		while self.running and not xbmc.abortRequested:

			if isNavigation(self.navtimeout):
				mode = TFT_MODE.NAVIGATION
			elif xbmc.getCondVisibility('Player.HasVideo'):
				mode = TFT_MODE.VIDEO
			elif xbmc.getCondVisibility('Player.HasAudio'):
				mode = TFT_MODE.MUSIC
			elif xbmc.getCondVisibility('System.ScreenSaverActive'):
				mode = TFT_MODE.SCREENSAVER
			else:
				mode = TFT_MODE.GENERAL

			xbmc_log(xbmc.LOGDEBUG, 'Drawing layout for mode %s' % mode)

			self.drawToDisplay(mode)
			self.screen.blit(self.background, (0, 0))
			pygame.display.flip()

#			self.clock.tick(self.fps)
			while self.Monitor.waitForAbort(self.wait):
				running = False

		del self.Monitor


if (__name__ == "__main__"):
	xbmc_log(xbmc.LOGNOTICE, 'Starting')
	TFT()
	xbmc_log(xbmc.LOGNOTICE, 'Closing')
	pygame.quit()
	sys.exit(0)
