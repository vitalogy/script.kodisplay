import os
import sys
import time
import threading
import xbmc
import xbmcaddon
import xbmcgui


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
from modes import *
from modeslist import ModesList
import config as glob

glob.navTimer = time.time()
distro = getDistroName() # from helper.py
xbmc_log(xbmc.LOGNOTICE, 'Version %s running on %s' %(__addonversion__, distro))

if distro == 'LibreELEC':
	# running on LibreELEC
	#  1.   check for existing lib.tgz (lib.tgz includes SDL, pygame & RPi.GPIO)
	#  1.1.	if the directories SDL, pygame or RPi.GPIO exist, delete them
	#  1.2.	unpack lib.tgz, then move it to lib.tgz.x
	#  2.   load the needed shared libraries


	libtgz = 'lib.tgz'
	__libtgz__ = os.path.join(__lib__, 'libreelec', libtgz)
	if os.path.exists(__libtgz__):
		xbmc_log(xbmc.LOGNOTICE, 'Will extracting needed libs from %s' % libtgz)
		# remove the directories SDL, pygame and RPi if they exist
		if os.path.isdir(os.path.join(__lib__, 'SDL')):
			execute('rm -rf ' + __lib__ + '/' + 'SDL')
		if os.path.isdir(os.path.join(__lib__, 'pygame')):
			execute('rm -rf ' + __lib__ + '/' + 'pygame')
		if os.path.isdir(os.path.join(__lib__, 'RPi')):
			execute('rm -rf ' + __lib__ + '/' + 'RPi')

		try:
			execute('tar xf ' + __libtgz__ + ' -C ' + __lib__)
			execute('mv ' + __libtgz__ + ' ' + __libtgz__ + '.x')
			xbmc_log(xbmc.LOGNOTICE, 'Extracting needed libs was successfully.')
		except:
			xbmc_log(xbmc.LOGWARNING, 'Extracting libs from %s goes wrong!' % libtgz)
			sys.exit(1)


	if not os.path.exists(os.path.join(__lib__, 'SDL', 'libSDL.so')):
		text = __addon__.getLocalizedString(32400)
		notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
		xbmc_log(xbmc.LOGWARNING, 'Needed lib SDL is missing!')
		if not os.path.exists(__libtgz__):
			xbmc_log(xbmc.LOGWARNING, 'Missing %s to extract the needed libs from!' % libtgz)
		sys.exit(1)


	from ctypes import *

	try:
		cdll.LoadLibrary(os.path.join(__lib__, 'SDL', 'libSDL.so'))
		cdll.LoadLibrary(os.path.join(__lib__, 'SDL', 'libSDL_image.so'))
		cdll.LoadLibrary(os.path.join(__lib__, 'SDL', 'libSDL_ttf.so'))
	except:
		text = __addon__.getLocalizedString(32401)
		notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
		xbmc_log(xbmc.LOGWARNING, 'Loading the lib SDL failed!')
		sys.exit(1)


# import pygame
os.environ["SDL_VIDEODRIVER"] = "fbcon"
os.environ["SDL_FBDEV"] = "/dev/fb1"
try:
	import pygame
	from pygame.locals import *
except:
	text = __addon__.getLocalizedString(32500)
	notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
	xbmc_log(xbmc.LOGWARNING, 'Importing pygame failed!')
	sys.exit(1)

# import RPi.GPIO
try:
	import RPi.GPIO as GPIO
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BCM)
except:
	text = __addon__.getLocalizedString(32501)
	notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
	xbmc_log(xbmc.LOGWARNING, 'Importing RPi.GPIO failed!')
	sys.exit(1)




class MyMonitor(xbmc.Monitor):
	def __init__(self, *args, **kwargs):
		xbmc.Monitor.__init__(self)
		self.update_settings = kwargs['update_settings']
		xbmc_log(xbmc.LOGDEBUG, 'Monitor initalized')

	def onSettingsChanged(self):
		xbmc_log(xbmc.LOGNOTICE, 'Settings changed, perform update')
		self.update_settings()

#	def onScreensaverDeactivated(self):
#		ScreensaverRunning = False

#	def onScreensaverActivated(self):
#		ScreensaverRunning = True




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
		self.background = pygame.Surface(self.screen.get_size()).convert()

		self.dimmerisactive = False
		self.distro = distro
		xbmc_log(xbmc.LOGNOTICE, 'Display Resolution: ' + str(self.display_w) + 'x' + str(self.display_h))

		self.tftModes = ModesList(self.distro, self.display_w, self.display_h, pygame)

		self.mode = TFT_MODE.STARTSCREEN

		self.queryData = False

		if self.readSettings():
			self.run()




	def readSettings(self):

		if self.queryData:
			self.queryData = False
			self.qth.join()
			xbmc_log(xbmc.LOGNOTICE, 'Thread to query data has been stopped')

		try:
			self.fps = int(__addon__.getSetting('fps'))
			self.navtimeout = int(__addon__.getSetting('navtimeout'))
			self.displaystartscreen = True if __addon__.getSetting('displaystartscreen') == 'true' else False
			self.startscreentime = int(__addon__.getSetting('startscreentime'))
			self.scrollspeed = int(__addon__.getSetting('scrollspeed'))
			self.dimactivated = True if __addon__.getSetting('dimactive') == 'true' else False
			self.backlightgpio = int(__addon__.getSetting('backlightgpio'))
			self.dimonscreensaver = True if __addon__.getSetting('dimonscreensaver') == 'true' else False
			self.dimmervalue = int(__addon__.getSetting('dimmervalue'))
			glob.addonDebug = True if __addon__.getSetting('addondebug') == 'true' else False
			xbmc_log(xbmc.LOGNOTICE, 'Loaded addon settings successfully')
		except:
			xbmc_log(xbmc.LOGNOTICE, 'Failure by loading the addon settings')
			return False

		if self.dimactivated:
			GPIO.setup(self.backlightgpio, GPIO.OUT)
			self.pwm = GPIO.PWM(self.backlightgpio, 1000)
			self.pwm.start(100)
			self.dimmerisactive = True
		else:
			self.dimmerisactive = False

		if not self.tftModes.xmlToList():
			return False

		self.tftmodeslist = self.tftModes.returnModes()

		# create a list for holding scroll information
		# if the width of rendered image greater then display width, put the scroll infos in this list
		self.scrolllist = [[[1 for k in range(0, 2)] for j in range(0, len(self.tftmodeslist[i]))] for i in range(0, len(self.tftmodeslist))]

		# create a list for holding the data queried from kodi
		self.querylist = [[['0' for k in range(0, 3)] for j in range(0, len(self.tftmodeslist[i]))] for i in range(0, len(self.tftmodeslist))]

		self.queryData = True
		self.qth = threading.Thread(name='queryDataThread', target=self.queryDataThread)
		self.qth.start()

		return True



	def isNavigation(self):
		ret = False

		menu = xbmc.getInfoLabel('$INFO[System.CurrentWindow]')
		subMenu = xbmc.getInfoLabel('$INFO[System.CurrentControl]')

		if menu != glob.oldMenu or subMenu != glob.oldSubMenu or (glob.navTimer + self.navtimeout) > time.time():
			ret = True
		if menu != glob.oldMenu or subMenu != glob.oldSubMenu:
			glob.navTimer = time.time()
		glob.oldMenu = menu
		glob.oldSubMenu = subMenu

		return ret




	def queryDataThread(self):
		xbmc_log(xbmc.LOGNOTICE, 'Thread to query data was started successfully')

		while self.queryData:

#			starttime = time.time()

			if self.isNavigation():
				self.mode = TFT_MODE.NAVIGATION
			elif xbmc.getCondVisibility("PVR.IsPlayingTV"):
				self.mode = TFT_MODE.PVRTV
			elif xbmc.getCondVisibility("PVR.IsPlayingRadio"):
				self.mode = TFT_MODE.PVRRADIO
			elif xbmc.getCondVisibility('Player.HasVideo') and len(xbmc.getInfoLabel("VideoPlayer.TVShowTitle")):
				self.mode = TFT_MODE.TVSHOW
			elif xbmc.getCondVisibility('Player.HasVideo'):
				self.mode = TFT_MODE.VIDEO
			elif xbmc.getCondVisibility('Player.HasAudio'):
				self.mode = TFT_MODE.MUSIC
			elif xbmc.getCondVisibility('System.ScreenSaverActive'):
				self.mode = TFT_MODE.SCREENSAVER
			else:
				self.mode = TFT_MODE.GENERAL

			if self.dimmerisactive:
				self.backlightControl()

			xbmc.sleep(20)

			for i in range(0, len(self.tftmodeslist[self.mode])):
				if self.tftmodeslist[self.mode][i][1] == 'visible' or xbmc.getCondVisibility(self.tftmodeslist[self.mode][i][1]):
					self.querylist[self.mode][i][0] = 'visible'
				else:
					self.querylist[self.mode][i][0] = 'hide'

				xbmc.sleep(20)

				if self.tftmodeslist[self.mode][i][0] == 'textToDisplay':
					text = self.tftmodeslist[self.mode][i][2]
					if text.lower().find('$info') >= 0:
						text = xbmc.getInfoLabel(text)
						# remove special character from infolabel text
						for char in '()[]{}*':
							text = text.replace(char,'')
						# utf-8
						self.querylist[self.mode][i][1] = text.strip().decode('utf-8', 'ignore')

						xbmc.sleep(20)


				if self.tftmodeslist[self.mode][i][0] == 'progressBarToDisplay':
					# timeToSecs from helper.py
					self.querylist[self.mode][i][1] = str(timeToSecs(xbmc.getInfoLabel("Player.Time(hh:mm:ss)")))
					self.querylist[self.mode][i][2] = str(timeToSecs(xbmc.getInfoLabel("Player.Duration(hh:mm:ss)")))

					xbmc.sleep(20)

#			xbmc_log(xbmc.LOGNOTICE, 'start: %s  end: %s' % (str(starttime), str(time.time())))





	def backgroundToDisplay(self, condition, background, mode, index):
		self.background.blit(background, (0, 0))


	def textToDisplay(self, condition, text, scrollmode, txtfont, size, color, xpos, cx, ypos, cy, mode, index):
		if self.querylist[mode][index][0] == 'visible':
			if text.lower().find('$info') >= 0:
				text = self.querylist[mode][index][1]

			if txtfont == 'none':
				font = pygame.font.Font(None, size)
			else:
				font = pygame.font.Font(txtfont, size)
			textimage = font.render(text, 1, color)
			textimage = textimage.convert_alpha()

			if (cx == 1 and textimage.get_width() > self.display_w + 20) or \
				(cx == 0 and textimage.get_width() > (self.display_w - abs(xpos) + 10)):
				if cx == 1:
					xpos = 0
				max_width = self.display_w - abs(xpos)
				dx = self.scrolllist[mode][index][1]
				scroll = dx * self.scrollspeed

				if (self.scrolllist[mode][index][0] + scroll) > (textimage.get_width() - max_width):
					self.scrolllist[mode][index][0] = textimage.get_width() - max_width
					dx *= -1  # change direction
				elif self.scrolllist[mode][index][0] + scroll < 0:
					self.scrolllist[mode][index][0] = 0
					dx *= -1  # change direction
				else:
					self.scrolllist[mode][index][0] += scroll

				self.scrolllist[mode][index][1] = dx

				location = (self.scrolllist[mode][index][0], 0)
				size = (max_width, textimage.get_height())
				textimage = textimage.subsurface(pygame.Rect(location, size))
				textpos = textimage.get_rect()

				if cx == 0:
					if xpos < 0:
						textpos.x = self.display_w - textimage.get_width() + xpos
					else:
						textpos.x = xpos
				else:
					textpos.x = 0
			else:
				textpos = textimage.get_rect()
				if cx == 0:
					if xpos < 0:
						textpos.x = self.display_w - textimage.get_width() + xpos
					else:
						textpos.x = xpos
				else:
					textpos.centerx = xpos

			if cy == 0:
				if ypos < 0:
					textpos.y = self.display_h - textimage.get_height() + ypos
				else:
					textpos.y = ypos
			else:
				textpos.centery = ypos

			self.background.blit(textimage, textpos)


	def imageToDisplay(self, condition, image, imagepos, mode, index):
		if self.querylist[mode][index][0] == 'visible':
			self.background.blit(image, imagepos)


	def progressBarToDisplay(self, condition, width, height, barcolor, progresscolor, border, bordercolor, xpos, cx, ypos, cy, mode, index):
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

		playtime = int(self.querylist[mode][index][1])
		duration = int(self.querylist[mode][index][2])

		if (playtime > 0 and duration > 0):
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
			values.extend([mode, i])
			getattr(self, func)(*values)




	def backlightControl(self):
		if self.mode == TFT_MODE.SCREENSAVER:
			if self.dimonscreensaver:
				self.pwm.ChangeDutyCycle(self.dimmervalue)
		else:
			self.pwm.ChangeDutyCycle(100)



	def run(self):

		starttime = 0
		drawtodisplay = 0
		screenblit = 0
		screenflip = 0
		wholetime = 0

		monitor = MyMonitor(update_settings = self.readSettings)

		if self.displaystartscreen:
			self.drawToDisplay(self.mode)
			self.screen.blit(self.background, (0, 0))
			pygame.display.flip()
			xbmc.sleep(self.startscreentime * 1000)

		# run the event loop
		while not monitor.abortRequested():

			if glob.addonDebug:
				xbmc_log(xbmc.LOGDEBUG, 'NEW FRAME - MODE: %s' % modes[self.mode])
				starttime = time.time()


			self.drawToDisplay(self.mode)
			if glob.addonDebug:
				drawtodisplay = time.time() - starttime

			self.screen.blit(self.background, (0, 0))
			if glob.addonDebug:
				screenblit = time.time() - starttime - drawtodisplay

			pygame.display.flip()
			if glob.addonDebug:
				screenflip = time.time() - starttime - screenblit - drawtodisplay

			self.clock.tick(self.fps)

			if monitor.waitForAbort(0.00001):
				break

			if glob.addonDebug:
				wholetime = time.time() - starttime
				xbmc_log(xbmc.LOGDEBUG, 'drawtodisplay:%s\tscreenblit:%s\tscreenflip:%s\twholetime:%s' % (str(drawtodisplay), str(screenblit), str(screenflip), str(wholetime)))

		if self.dimactivated:
			self.pwm.stop()

		if self.queryData:
			self.queryData = False
			self.qth.join()
			xbmc_log(xbmc.LOGNOTICE, 'Thread to query data has been stopped')


if (__name__ == "__main__"):
	xbmc_log(xbmc.LOGNOTICE, 'Starting')
	TFT()
	xbmc_log(xbmc.LOGNOTICE, 'Closing')
	pygame.quit()
	GPIO.cleanup()
	sys.exit(0)

