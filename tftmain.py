import os
import time
import platform
import xbmc
import xbmcaddon
import xbmcgui
from ctypes import *

__addon__        = xbmcaddon.Addon()
__addonversion__ = __addon__.getAddonInfo('version')
__addonid__      = __addon__.getAddonInfo('id')
__addonname__    = __addon__.getAddonInfo('name')
__cwd__          = __addon__.getAddonInfo('path')
__icon__         = os.path.join(__cwd__, 'icon.png')
__lib__          = os.path.join(__cwd__, 'resources', 'lib')
__media__        = os.path.join(__cwd__, 'resources', 'media')

BASE_RESOURCE_PATH = xbmc.translatePath(__lib__)
sys.path.insert(0, BASE_RESOURCE_PATH)

from const import *
from helper import *

distro = ''
display_w = 0
display_h = 0

if os.path.isdir('/usr/share/kodi/addons/service.libreelec.settings'):
	distro = 'LibreELEC'
	# running on LibreELEC
	#  1. check for existing lib.tgz (includes pygame & libSDL)
	#  2. unpack lib.tgz, then remove it
	#  3. load the needed shared libraries

	__libtgz__ = os.path.join(__lib__, 'lib.tgz')
	if os.path.exists(__libtgz__):
		notify(__addonname__, 'Extracting libs from lib.tgz', 5000, __icon__)
		execute('tar xf ' + __libtgz__ + ' -C ' + __lib__)
		execute('rm -rf ' + __libtgz__)

	cdll.LoadLibrary(os.path.join(__lib__, 'SDL', 'libSDL.so'))
	cdll.LoadLibrary(os.path.join(__lib__, 'SDL', 'libSDL_image.so'))
	cdll.LoadLibrary(os.path.join(__lib__, 'SDL', 'libSDL_ttf.so'))
else:
	distro = platform.linux_distribution()[0] or 'Linux'

try:
	import pygame
except:
	notify(__addonname__, 'Importing pygame failed', 30000, __icon__)
from pygame.locals import *

os.environ["SDL_VIDEODRIVER"] = "fbcon"
os.environ["SDL_FBDEV"] = "/dev/fb1"




class DisplayText():
	def __init__(self, text, size, color, xpos, ypos):
		self.font = pygame.font.Font(None, size)
		self.image = self.font.render(text, 1, color)
		self.textpos = self.image.get_rect()
		self.textpos.centerx = xpos
		self.textpos.centery = ypos
	def draw(self, surface):
		surface.blit(self.image, self.textpos)


class DisplayImage():
	def __init__(self, name, scale, xpos, ypos):
		self.image = pygame.image.load(name)
		image_w,image_h = self.image.get_size()
#		if image_w > display_w:
#			scale = display_w/image_w
#			self.image = pygame.transform.scale(self.image, (int(image_w*scale), int(image_h*scale)))
#		else:
		self.image = pygame.transform.scale(self.image, (int(image_w*scale), int(image_h*scale)))
		self.imagepos = self.image.get_rect()
		self.imagepos.centerx = xpos
		self.imagepos.centery = ypos
	def draw(self, surface):
		surface.blit(self.image, self.imagepos)


class TFT():
	def __init__(self):
		pygame.display.init()
		pygame.font.init()
		pygame.mouse.set_visible(False)
		self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
		TFTinfo = pygame.display.Info()
		display_w = TFTinfo.current_w
		display_h = TFTinfo.current_h

	def getWinMode(self):
		ret = ''

		WindowID = xbmcgui.getCurrentWindowId()
		if WindowID == WINDOW_IDS.WINDOW_MAINMENU:
			ret = 'TIME'
		elif WindowID == WINDOW_IDS.WINDOW_SYSTEMINFO:
			ret = 'SYSINFO'
		elif WindowID >= WINDOW_IDS.WINDOW_PVR and WindowID <= WINDOW_IDS.WINDOW_PVR_MAX:
			ret = 'PVR'
		elif WindowID in [WINDOW_IDS.WINDOW_VIDEOS, WINDOW_IDS.WINDOW_VIDEO_FILES,
						WINDOW_IDS.WINDOW_VIDEO_NAV, WINDOW_IDS.WINDOW_VIDEO_PLAYLIST]:
			ret = 'VIDEO'
		elif WindowID in [WINDOW_IDS.WINDOW_MUSIC, WINDOW_IDS.WINDOW_MUSIC_PLAYLIST,
						WINDOW_IDS.WINDOW_MUSIC_FILES, WINDOW_IDS.WINDOW_MUSIC_NAV,
						WINDOW_IDS.WINDOW_MUSIC_PLAYLIST_EDITOR]:
			ret = 'MUSIC'
		elif WindowID == WINDOW_IDS.WINDOW_PICTURES:
			ret = 'PICTURE'
		elif WindowID == WINDOW_IDS.WINDOW_WEATHER:
			ret = 'WEATHER'

		return (ret, str(WindowID))

	def getTime(self):
		ret = xbmc.getInfoLabel('System.Time(hh:mm:ss)')
		return ret

	def run(self):
		frame_rate = 5

		self.clock = pygame.time.Clock()

		self.background = pygame.Surface(self.screen.get_size())

		distrologo = __media__ + '/' + distro.lower() + '.' + 'png'
		if not os.path.isfile(distrologo):
			distrologo = __media__ + '/' + 'kodi.png'

		self.logo = DisplayImage(distrologo, 0.5, self.background.get_rect().centerx, self.background.get_rect().centery)
		self.dist = DisplayText(distro.lower(),
								30,
								COLOR.RED,
								self.background.get_rect().centerx,
								200)

		self.logo.draw(self.background)
		self.dist.draw(self.background)

		# Blit everything to the screen
		self.screen.blit(self.background, (0, 0))
		pygame.display.flip()
		time.sleep(5)

		# Event loop
		while (not xbmc.abortRequested):
			self.background = self.background.convert()
			self.background.fill(COLOR.BLACK)

			self.mode = DisplayText(self.getWinMode()[0] + '  WindowID: ' + self.getWinMode()[1],
									30,
									COLOR.RED,
									self.background.get_rect().centerx,
									50)
			self.mode.draw(self.background)
			if self.getWinMode()[0] == 'TIME':
				self.time = DisplayText(self.getTime(),
										80,
										COLOR.GREEN,
										self.background.get_rect().centerx,
										self.background.get_rect().centery)
			else:
				self.time = DisplayText(self.getTime(),
										26,
										COLOR.GREEN,
										270,
										12)
				self.dist = DisplayText(distro,
										20,
										COLOR.RED,
										self.background.get_rect().centerx,
										200)

				self.uname = DisplayText(platform.uname()[2],
										20,
										COLOR.ORANGE,
										self.background.get_rect().centerx,
										220)

				self.dist.draw(self.background)
				self.uname.draw(self.background)
			self.time.draw(self.background)

			# Blit everything to the screen
			self.screen.blit(self.background, (0, 0))
			pygame.display.flip()

			self.clock.tick(frame_rate)

		pygame.quit()

if (__name__ == "__main__"):
	TFT().run()
