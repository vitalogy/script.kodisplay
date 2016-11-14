import os
import sys
import time
import threading
import io
from urllib2 import urlopen
from urlparse import urlparse

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

sys.path.append(__lib__)
from helper import *
from modes import *
from modeslist import ModesList
import config as glob

oldMenu = ''
oldSubMenu = ''
navTimer = time.time()
distro = getDistroName() # from helper.py

if distro == 'LibreELEC':
	addondir = '/storage/.kodi/addons/virtual.sdl_pygame-libraries/lib'
	if os.path.isdir(addondir):
		sys.path.append('/storage/.kodi/addons/virtual.sdl_pygame-libraries/lib')
	else:
		text = __addon__.getLocalizedString(32400)
		notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
		xbmc_log(xbmc.LOGWARNING, 'Addon sdl_pygame not available!')
		sys.exit(1)

	addondir = '/storage/.kodi/addons/virtual.rpi-tools/lib'
	if os.path.isdir(addondir):
		sys.path.append('/storage/.kodi/addons/virtual.rpi-tools/lib')
	else:
		text = __addon__.getLocalizedString(32401)
		notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
		xbmc_log(xbmc.LOGWARNING, 'Addon rpi-tools not available!!')
		sys.exit(1)


# try import pygame
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

# try import RPi.GPIO
try:
	import RPi.GPIO as GPIO
	GPIO.setwarnings(False)
	GPIO.setmode(GPIO.BCM)
except:
	text = __addon__.getLocalizedString(32501)
	notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
	xbmc_log(xbmc.LOGERROR, 'Importing RPi.GPIO failed!')
	__addon__.setSetting('dimactive', 'false')
#	sys.exit(1)




class MyMonitor(xbmc.Monitor):
	def __init__(self, *args, **kwargs):
		xbmc.Monitor.__init__(self)
		self.update_settings = kwargs['update_settings']
		xbmc_log(xbmc.LOGDEBUG, 'Monitor initalized')

	def onSettingsChanged(self):
		xbmc_log(xbmc.LOGNOTICE, 'Settings changed, perform update')
		self.update_settings()




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

		self.tftModes = ModesList(self.distro, self.display_w, self.display_h)

		self.queryData = False
		self.surfaceRendering = False

		if self.readSettings():
			self.run()


	def stopSurfaceRenderingThread(self):
		if self.surfaceRendering == True:
			self.surfaceRendering = False
			self.rth.join()
			xbmc_log(xbmc.LOGDEBUG, 'Thread to rendering the surfaces has been stopped')

	def stopQueryDataThread(self):
		if self.queryData == True:
			self.queryData = False
			self.qth.join()
			xbmc_log(xbmc.LOGDEBUG, 'Thread to query data has been stopped')


	def readSettings(self):

		# stop both threads, if they are running
		self.stopSurfaceRenderingThread()
		self.stopQueryDataThread()

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
			self.debug_show_fps = True if __addon__.getSetting('showfps') == 'true' else False
			self.debug_show_wid = True if __addon__.getSetting('showwindowid') == 'true' else False
			self.debug_log_tpf = True if __addon__.getSetting('timeperframe') == 'true' else False

			xbmc_log(xbmc.LOGDEBUG, 'Loaded addon settings successfully')
		except:
			xbmc_log(xbmc.LOGWARNING, 'Failure by loading the addon settings')
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

		# create a list for holding the data queried from kodi
		self.querylist = [[[0 for k in range(0, 4)] for j in range(0, len(self.tftmodeslist[i]))] for i in range(0, len(self.tftmodeslist))]

		# create a list for holding render information (surfaces, positions)
		self.renderlist = [[[0 for k in range(0, 5)] for j in range(0, len(self.tftmodeslist[i]))] for i in range(0, len(self.tftmodeslist))]

		# create a list for holding scroll information
		# if the width of the text surface greater then display width, put the scroll informations in this list
		self.scrolllist = [[[1 for k in range(0, 2)] for j in range(0, len(self.tftmodeslist[i]))] for i in range(0, len(self.tftmodeslist))]

		# start both threads
		self.queryData = True
		self.qth = threading.Thread(name='queryDataThread', target=self.queryDataThread)
		self.qth.start()

		self.surfaceRendering = True
		self.rth = threading.Thread(name='surfaceRenderingThread', target=self.surfaceRenderingThread)
		self.rth.start()


		return True



	def backlightControl(self):
		if self.mode == TFT_MODE.SCREENSAVER:
			if self.dimonscreensaver:
				self.pwm.ChangeDutyCycle(self.dimmervalue)
		else:
			self.pwm.ChangeDutyCycle(100)



	def isNavigation(self):
		global oldMenu
		global oldSubMenu
		global navTimer
		ret = False

		menu = xbmc.getInfoLabel('$INFO[System.CurrentWindow]')
		subMenu = xbmc.getInfoLabel('$INFO[System.CurrentControl]')

		if menu != oldMenu or subMenu != oldSubMenu or (navTimer + self.navtimeout) > time.time():
			ret = True
		if menu != oldMenu or subMenu != oldSubMenu:
			navTimer = time.time()
		oldMenu = menu
		oldSubMenu = subMenu

		return ret


	def url_validator(self, url):
		try:
			result = urlparse(url)
			if result.scheme and result.netloc and result.path:
				return True
			else:
				return False
		except:
			return False


	def queryDataThread(self):
		xbmc_log(xbmc.LOGDEBUG, 'Thread to query data was started successfully')

		while self.queryData:
#			self.windowid = int(xbmcgui.getCurrentWindowId())
			if self.displaystartscreen:
				self.mode = TFT_MODE.STARTSCREEN
			elif self.isNavigation():
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

			mode = self.mode

			for index in range(0, len(self.tftmodeslist[mode])):
				if self.tftmodeslist[mode][index][1] == 'visible' or xbmc.getCondVisibility(self.tftmodeslist[mode][index][1]):
					self.querylist[mode][index][1] = 'visible'
				else:
					self.querylist[mode][index][1] = 'hide'

				if self.tftmodeslist[mode][index][0] == 'renderBackground':
					if self.tftmodeslist[mode][index][2] != self.querylist[mode][index][2]:
						self.querylist[mode][index][2] = self.tftmodeslist[mode][index][2]

				elif self.tftmodeslist[mode][index][0] == 'renderText':
					text = self.tftmodeslist[mode][index][2].strip().decode('utf-8')
					# get real text, if the variable text is a infolabel
					if text.lower().find('$info') >= 0:
						text = xbmc.getInfoLabel(text).strip().decode('utf-8')
						# remove special character from infolabel text
						for char in '()[]{}*':
							text = text.replace(char,'').strip()
					self.querylist[mode][index][2] = text

				elif self.tftmodeslist[mode][index][0] == 'renderImage':
					imagepath = self.tftmodeslist[mode][index][2]
					# get real imagepath, if the variable imagepath is a infolabel
					if imagepath.lower().find('$info') >= 0:
						imagepath = xbmc.getInfoLabel(imagepath)
						# if needed, let translate the path
						if imagepath.startswith('special://') >= 0:
							imagepath = xbmc.translatePath(imagepath)

					if imagepath:
						if os.path.isfile(imagepath):
							self.querylist[mode][index][3] = 'local'
						elif self.url_validator(imagepath):
							self.querylist[mode][index][3] = 'url'
						else:
							self.querylist[mode][index][3] = 'noimage'
							if imagepath != self.renderlist[mode][index][3]:
								xbmc_log(xbmc.LOGWARNING, '%s from %s  getting %s - this is not an local path, neither a url' % (mode, self.tftmodeslist[mode][index][2], imagepath))
								self.renderlist[mode][index][3] = imagepath
					else:
						self.querylist[mode][index][3] = 'noimage'

					if imagepath != self.renderlist[mode][index][3]:
						self.renderlist[mode][index][0] = 0
						self.querylist[mode][index][2] = imagepath

				elif self.tftmodeslist[mode][index][0] == 'renderProgressbar':
					# timeToSecs from helper.py
					self.querylist[mode][index][2] = str(timeToSecs(xbmc.getInfoLabel("Player.Time(hh:mm:ss)")))
					self.querylist[mode][index][3] = str(timeToSecs(xbmc.getInfoLabel("Player.Duration(hh:mm:ss)")))

				self.querylist[mode][index][0] = 1

			xbmc.sleep(30)




	def renderBackground(self, mode, index):
		color = self.querylist[mode][index][2]
		if color != self.renderlist[mode][index][3]:
			bkgsurface = pygame.Surface((self.display_w, self.display_h)).convert()
			bkgsurface.fill(hexToRGB(self.querylist[mode][index][2]))
			bkgpos = bkgsurface.get_rect()
			bkgpos.x = 0
			bkgpos.y = 0
			self.renderlist[mode][index][0] = 1
			self.renderlist[mode][index][1] = bkgsurface
			self.renderlist[mode][index][2] = bkgpos
			self.renderlist[mode][index][3] = color



	def renderText(self, scrollmode, txtfont, size, color, xpos, cx, ypos, cy, mode, index):
		text = self.querylist[mode][index][2]
		if text != self.renderlist[mode][index][3]:
			if txtfont == 'none':
				font = pygame.font.Font(None, size)
			else:
				font = pygame.font.Font(txtfont, size)
			txtsurface = font.render(text, 1, color).convert_alpha()
			# save the whole surface, even it is larger then the max_width
			# so we will need it later, if the text does not change
			self.renderlist[mode][index][4] = txtsurface
			self.renderlist[mode][index][3] = text
		else:
			txtsurface = self.renderlist[mode][index][4]

		# if the txtsurface width is too large
		if (cx == 1 and txtsurface.get_width() > self.display_w + 20) or \
			(cx == 0 and txtsurface.get_width() > (self.display_w - abs(xpos) + 10)):

			# surface is centered in x, so max_width is equal the display width
			# else, max_width is the display width less the given xpos
			if cx == 1:
				xpos = 0
				max_width = self.display_w
			else:
				max_width = self.display_w - abs(xpos)

			# directionx = saved direction of x-scrolling (1 or -1) from scrolllist
			# scrollstep = direction_x * scrollspeed from settings
			# oldposition = saved last position from scrolllist
			direction_x = self.scrolllist[mode][index][0]
			scrollstep = direction_x * self.scrollspeed
			oldposition = self.scrolllist[mode][index][1]

#			xbmc_log(xbmc.LOGNOTICE, '  %s %s' % (str(oldposition), str(scrollstep)))

			if scrollmode == 'leftright':
				if (oldposition + scrollstep) > (txtsurface.get_width() - max_width):
					newposition = txtsurface.get_width() - max_width
					direction_x *= -1  # change direction
				elif oldposition + scrollstep < 0:
					newposition = 0
					direction_x *= -1  # change direction
				else:
					newposition = oldposition + scrollstep
				location = (newposition, 0)
				size = (max_width, txtsurface.get_height())
				txtsurface = txtsurface.subsurface(pygame.Rect(location, size))
				txtpos = txtsurface.get_rect()

			elif scrollmode == 'marquee':
				span = 50
				bSurface = False
				if (oldposition + scrollstep) > txtsurface.get_width() + span:
					newposition = 0
					location = (newposition, 0)
					size = (max_width, txtsurface.get_height())
					txtsurface = txtsurface.subsurface(pygame.Rect(location, size))
				elif (oldposition + scrollstep) > (txtsurface.get_width() - max_width):
					newposition = oldposition + scrollstep
					asurface_width = txtsurface.get_width() - newposition
					location = (newposition, 0)
					size = (asurface_width, txtsurface.get_height())
					atxtsurface = txtsurface.subsurface(pygame.Rect(location, size))
					if (max_width - asurface_width) > span:
						bsurface_width = max_width - asurface_width - span
						location = (0, 0)
						size = (bsurface_width, txtsurface.get_height())
						btxtsurface = txtsurface.subsurface(pygame.Rect(location, size))
						bSurface = True
					# create a new surface to blit the text surface(s)
					txtsurface = pygame.Surface((max_width, txtsurface.get_height()), pygame.SRCALPHA, 32)
					txtsurface = txtsurface.convert_alpha()
					txtsurface.blit(atxtsurface, (0, 0))
					if bSurface:
						txtsurface.blit(btxtsurface, ((max_width - bsurface_width), 0))
				else:
					newposition = oldposition + scrollstep
					location = (newposition, 0)
					size = (max_width, txtsurface.get_height())
					txtsurface = txtsurface.subsurface(pygame.Rect(location, size))


			self.scrolllist[mode][index][0] = direction_x
			self.scrolllist[mode][index][1] = newposition

			txtpos = txtsurface.get_rect()


			if cx == 0:
				if xpos < 0:
					txtpos.x = self.display_w - txtsurface.get_width() + xpos
				else:
					txtpos.x = xpos
			else:
				txtpos.x = 0

		else:
			txtpos = txtsurface.get_rect()
			if cx == 0:
				if xpos < 0:
					txtpos.x = self.display_w - txtsurface.get_width() + xpos
				else:
					txtpos.x = xpos
			else:
				txtpos.centerx = xpos

		if cy == 0:
			if ypos < 0:
				txtpos.y = self.display_h - txtsurface.get_height() + ypos
			else:
				txtpos.y = ypos
		else:
			txtpos.centery = ypos


		self.renderlist[mode][index][0] = 1
		self.renderlist[mode][index][1] = txtsurface
		self.renderlist[mode][index][2] = txtpos


	def renderImage(self, border, bordercolor, xpos, cx, ypos, cy, resx, resy, mode, index):
		if self.querylist[mode][index][3] == 'noimage':
			self.renderlist[mode][index][0] = 0
		else:
			imagepath = self.querylist[mode][index][2]
			if imagepath != self.renderlist[mode][index][3]:
				if self.querylist[mode][index][3] == 'url':
					imagefile = io.BytesIO(urlopen(imagepath).read())
				elif self.querylist[mode][index][3] == 'local':
					imagefile = imagepath

				imgsurface = pygame.image.load(imagefile)
				if resx > 0 and resy > 0:
					# aspact_scale() from helper.py
					imgsurface = pygame.transform.scale(imgsurface, aspect_scale(imgsurface, (resx, resy)))
				elif resx > 0 and resy == 0:
					scale_factor = resx / float(imgsurface.get_width())
					imgsurface = pygame.transform.scale(imgsurface, (resx, int(scale_factor * imgsurface.get_height())))
				elif resx == 0 and resy > 0:
					scale_factor = resy / float(imgsurface.get_height())
					imgsurface = pygame.transform.scale(imgsurface, (int(scale_factor * imgsurface.get_width()), resy))


				imgsurface = imgsurface.convert_alpha()

				imgpos = imgsurface.get_rect()

				if border > 0:
					imgborder = pygame.Rect(imgpos)
					pygame.draw.rect(imgsurface, bordercolor, imgpos, border)


				if cx == 0:
					if xpos < 0:
						imgpos.x = self.display_w - imgsurface.get_width() + xpos
					else:
						imgpos.x = xpos
				else:
					imgpos.centerx = xpos

				if cy == 0:
					if ypos < 0:
						imgpos.y = self.display_h - imgsurface.get_height() + ypos
					else:
						imgpos.y = ypos
				else:
					imgpos.centery = ypos

				self.renderlist[mode][index][0] = 1
				self.renderlist[mode][index][1] = imgsurface
				self.renderlist[mode][index][2] = imgpos
				self.renderlist[mode][index][3] = imagepath



	def renderProgressbar(self, width, height, barcolor, progresscolor, border, bordercolor, xpos, cx, ypos, cy, mode, index):

		playtime = int(self.querylist[mode][index][2])
		duration = int(self.querylist[mode][index][3])

		if playtime != self.renderlist[mode][index][3]:
			rectsurface = pygame.Surface((width, height)).convert()
			rectpos = rectsurface.get_rect()

			progbar = pygame.Rect(0, 0, width, height)
			progbar.x = 0
			progbar.y = 0


			if cx == 0:
				if xpos < 0:
					rectpos.x = self.display_w - width + xpos
				else:
					rectpos.x = xpos
			else:
				rectpos.centerx = xpos

			if cy == 0:
				if ypos < 0:
					rectpos.y = self.display_h - height + ypos
				else:
					rectpos.y = ypos
			else:
				rectpos.centery = ypos

			if (playtime > 0 and duration > 0):
				percent = int(( 1. * progbar.width / duration ) * playtime)
			else:
				percent = 0

			progbar_done = pygame.Rect(progbar)
			progbar_done.width = percent
			pygame.draw.rect(rectsurface, barcolor, progbar )
			pygame.draw.rect(rectsurface, progresscolor, progbar_done )
			if border > 0:
				pygame.draw.rect(rectsurface, bordercolor, progbar, border)

			self.renderlist[mode][index][0] = 1
			self.renderlist[mode][index][1] = rectsurface
			self.renderlist[mode][index][2] = rectpos
			self.renderlist[mode][index][3] = playtime



	def surfaceRenderingThread(self):
		xbmc_log(xbmc.LOGDEBUG, 'Thread to render the surfaces was started successfully')
		while self.surfaceRendering:
			mode = self.mode
			xbmc.sleep(50)
			for index in range(0, len(self.tftmodeslist[mode])):
#				xbmc_log(xbmc.LOGNOTICE, 'RenderList: %s' % self.tftmodeslist[mode][index][0])
#				xbmc_log(xbmc.LOGNOTICE, '  queried: %s %s %s %s' % (self.querylist[mode][index][0], self.querylist[mode][index][1], self.querylist[mode][index][2], self.querylist[mode][index][3]))
				if self.querylist[mode][index][0] == 1:
					func = self.tftmodeslist[mode][index][0]
					values = self.tftmodeslist[mode][index][3:]
					values.extend([mode, index])
					getattr(self, func)(*values)

#				xbmc_log(xbmc.LOGNOTICE, '  rendered: %s %s %s %s' % (self.renderlist[mode][index][0], self.renderlist[mode][index][1], self.renderlist[mode][index][2], self.renderlist[mode][index][3]))



	def drawFrame(self, mode):
		# blit the rendered surfaces on the background
		for index in range(0, len(self.tftmodeslist[mode])):
			if self.renderlist[mode][index][0] == 1 and self.querylist[mode][index][1] == 'visible':
				self.background.blit(self.renderlist[mode][index][1], self.renderlist[mode][index][2])



	def drawDebugInfo(self, infostring, xpos):
		font = pygame.font.Font(None, 36)
		infosurface = font.render(infostring, 1, (255, 165, 0)).convert_alpha()
		infopos = infosurface.get_rect()
		if xpos < 0:
			infopos.x = self.display_w - infosurface.get_width() + xpos
		else:
			infopos.x = xpos
		infopos.y = self.display_h - infosurface.get_height() - 2
		backgroundsurface = pygame.Surface(infosurface.get_size()).convert()
		backgroundsurface.fill((0, 0, 0))
		self.background.blit(backgroundsurface, infopos)
		self.background.blit(infosurface, infopos)



	def run(self):

		monitor = MyMonitor(update_settings = self.readSettings)
		set_startscreenstarttime = True

		# run the event loop
		while not monitor.abortRequested():

			self.clock.tick(self.fps)

			if glob.addonDebug:
				starttime = time.time()

			if self.displaystartscreen:
				if set_startscreenstarttime:
					startscreenstart = time.time()
					set_startscreenstarttime = False
				else:
					if startscreenstart + self.startscreentime < time.time():
						self.displaystartscreen = False
						set_startscreenstarttime = True

			self.drawFrame(self.mode)

			# show info on display, if activated
			if glob.addonDebug:
				if self.debug_show_fps:
					fpsstring = "FPS: {:.2f}".format(self.clock.get_fps())
					self.drawDebugInfo(fpsstring, 2)
				if self.debug_show_wid:
					widstring = "WinID: " + str(self.windowid)
					self.drawDebugInfo(widstring, -2)

			# blit the background on a screen and flip the display
			self.screen.blit(self.background, (0, 0))
			pygame.display.flip()

			if glob.addonDebug and self.debug_log_tpf:
				xbmc_log(xbmc.LOGDEBUG, 'NEW FRAME: %s\tTime:%s' % (modes[self.mode], str(time.time() - starttime)))
				xbmc_log(xbmc.LOGDEBUG, 'Time: %s' % str(self.clock.get_time()))

			if monitor.waitForAbort(0.005):
				break


		if self.dimactivated:
			self.pwm.stop()

		self.stopSurfaceRenderingThread()
		self.stopQueryDataThread()

if (__name__ == "__main__"):
	xbmc_log(xbmc.LOGNOTICE, 'Version %s running on %s' %(__addonversion__, distro))
	TFT()
	xbmc_log(xbmc.LOGNOTICE, 'Closing')
	pygame.quit()
	GPIO.cleanup()
	sys.exit(0)

