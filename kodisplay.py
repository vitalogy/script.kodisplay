import os
import sys
import stat
import time
import threading
import io
import xbmc
import xbmcaddon
import xbmcgui   # for window id

__addon__         = xbmcaddon.Addon()
__addonversion__  = __addon__.getAddonInfo('version')
__addonid__       = __addon__.getAddonInfo('id')
__addonname__     = __addon__.getAddonInfo('name')
__path__          = __addon__.getAddonInfo('path')
__icon__          = os.path.join(__path__, 'icon.png')
__lib__           = os.path.join(__path__, 'resources', 'lib')

sys.path.append(__lib__)

from distro import getDistroName
from settings import Settings
from lists import Lists
from querydata import QueryDataThread
from surfacerender import SurfaceRenderingThread
from lognotify import *
from helper import *


distro = getDistroName()
if distro == "LibreELEC":
	from ctypes import *
	cdll.LoadLibrary(os.path.join(__lib__, 'SDL', 'libSDL.so'))
	cdll.LoadLibrary(os.path.join(__lib__, 'SDL', 'libSDL_image.so'))
	cdll.LoadLibrary(os.path.join(__lib__, 'SDL', 'libSDL_ttf.so'))
	__addon__.setSetting(id="enable_bootsplash", value="true")
else:
	__addon__.setSetting(id="enable_bootsplash", value="false")

sdldriver = __addon__.getSetting('sdldriver')
if sdldriver == "none":
	__addon__.openSettings()
	counter = 0
	while __addon__.getSetting('sdldriver') == "none":
		xbmc.sleep(1000)
		counter += 1
		if counter == 90:  # wait 90 sec, while the user is setup kodisplay
			sys.exit(1)
	sdldriver = __addon__.getSetting('sdldriver')

os.environ["SDL_VIDEODRIVER"] = sdldriver

if sdldriver == "fbcon":
	sdlfbdev = __addon__.getSetting('fbdev')
	# check device is a character device and the correct device permission (writeable)
	if not os.path.exists(sdlfbdev):
		text = __addon__.getLocalizedString(32500)
		notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
		xbmc_log(xbmc.LOGWARNING, 'Device %s does not exist!' %sdlfbdev)
		sys.exit(1)
	if not stat.S_ISCHR(os.stat(sdlfbdev).st_mode):
		text = __addon__.getLocalizedString(32500)
		notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
		xbmc_log(xbmc.LOGWARNING, 'Device %s is not a chracter device!' %sdlfbdev)
		sys.exit(1)
	if not os.access(sdlfbdev, os.W_OK):
		text = __addon__.getLocalizedString(32500)
		notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
		xbmc_log(xbmc.LOGWARNING, 'Device %s is not writeable!' %sdlfbdev)
		sys.exit(1)

	os.environ["SDL_FBDEV"] = sdlfbdev

# try to import pygame
try:
	import pygame
	from pygame.locals import *
except:
	text = __addon__.getLocalizedString(32502)
	notify(__addonname__, text, 10000, __icon__, xbmc.LOGWARNING)
	xbmc_log(xbmc.LOGWARNING, 'Importing pygame failed!')
	sys.exit(1)



class MyMonitor(xbmc.Monitor):

	def __init__(self, *args, **kwargs):
		xbmc.Monitor.__init__(self)
		self.update_settings = kwargs['update_settings']
		xbmc_log(xbmc.LOGDEBUG, 'Monitor initalized')

	def onSettingsChanged(self):
		self.update_settings()



class Display():

	def __init__(self):
		pygame.display.init()
		pygame.font.init()
		pygame.mouse.set_visible(False)
		self.distro = distro
		self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
		self.clock = pygame.time.Clock()
		self.background = pygame.Surface(self.screen.get_size()).convert()
		self.display_w = pygame.display.Info().current_w
		self.display_h = pygame.display.Info().current_h
		xbmc_log(xbmc.LOGNOTICE, 'Version %s is running on %s' %(__addonversion__, self.distro))
		xbmc_log(xbmc.LOGNOTICE, 'Resolution: ' + str(self.display_w) + 'x' + str(self.display_h))
		if self.setupKodisplay():
			self.run()

	def startThreads(self):
		self.srth = SurfaceRenderingThread(pygame, self.settings, self.lists)
		self.qdth = QueryDataThread(self.settings, self.lists)
		self.srth.start()
		self.qdth.start()

	def stopThreads(self):
		self.srth.stop()
		self.qdth.stop()
		self.srth.join()
		self.qdth.join()

	def updateSettings(self):
		xbmc_log(xbmc.LOGNOTICE, 'Settings changed, perform update')
		self.stopThreads()
		if self.setupKodisplay():
			xbmc_log(xbmc.LOGNOTICE, 'Settings updated')
		else:
			xbmc_log(xbmc.LOGWARNING, 'Updating settings has failed!')

	def setupKodisplay(self):
		self.settings = Settings(self.distro, self.display_w, self.display_h)
		self.settings.readSettings()
		self.lists = Lists(self.distro, self.display_w, self.display_h)
		if self.lists.createLists():
			self.startThreads()
			return True
		else:
			return False

	def drawFrame(self, mode):
		# blit the rendered surfaces on the background
		for index in range(0, len(self.lists.layout[mode])):
			if self.lists.render[mode][index][0] == 1 and self.lists.query[mode][index][1] == 'visible':
				self.background.blit(self.lists.render[mode][index][1], self.lists.render[mode][index][2])

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
		monitor = MyMonitor(update_settings = self.updateSettings)

		# run the event loop
		while not monitor.abortRequested():

			self.clock.tick(self.settings.fps)

			if glob.addonDebug:
				starttime = time.time()

			currentmode = self.lists.currentmode
			self.drawFrame(currentmode)

			# show info on display, if activated
			if self.settings.debug_show_fps:
				fpsstring = "FPS: {:.2f}".format(self.clock.get_fps())
				self.drawDebugInfo(fpsstring, 2)
			if self.settings.debug_show_wid:
				self.windowid = int(xbmcgui.getCurrentWindowId())
				widstring = "WinID: " + str(self.windowid)
				self.drawDebugInfo(widstring, -2)

			# blit the background on a screen and flip the display
			self.screen.blit(self.background, (0, 0))
			pygame.display.flip()

			if glob.addonDebug and self.settings.debug_log_tpf:
				xbmc_log(xbmc.LOGDEBUG, 'NEW FRAME: %s\tTime:%s' % (currentmode, str(time.time() - starttime)))
				xbmc_log(xbmc.LOGDEBUG, 'Time: %s' % str(self.clock.get_time()))

			if monitor.waitForAbort(0.0001):
				break

		self.stopThreads()

if (__name__ == "__main__"):
	Display()
	xbmc_log(xbmc.LOGNOTICE, 'Closing')
#	del settings
	pygame.quit()
	sys.exit(0)

