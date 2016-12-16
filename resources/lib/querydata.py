import os
import time
import threading
import Queue
from urlparse import urlparse
import xbmc

from helper import *
import config as glob
from lognotify import xbmc_log
from modes import *

oldMenu = ''
oldSubMenu = ''
navTimer = time.time()



class QueryDataThread(threading.Thread):

	def __init__(self, settings, lists):
		threading.Thread.__init__(self)
		self.abort = False
		self.navtimeout = settings.navtimeout
		self.lists = lists
		self.layoutlist = lists.layout
		self.querylist = lists.query
		self.renderlist = lists.render

	def stop(self):
		self.abort = True
		xbmc_log(xbmc.LOGDEBUG, 'Thread to query data had been ask to stop')

	def run(self):
		xbmc_log(xbmc.LOGDEBUG, 'Thread to query data was started successfully')

		while not self.abort:

			if self.isNavigation():
				self.mode = KODISPLAY_MODE.NAVIGATION
			elif xbmc.getCondVisibility("PVR.IsPlayingTV"):
				self.mode = KODISPLAY_MODE.PVRTV
			elif xbmc.getCondVisibility("PVR.IsPlayingRadio"):
				self.mode = KODISPLAY_MODE.PVRRADIO
			elif xbmc.getCondVisibility('Player.HasVideo') and len(xbmc.getInfoLabel("VideoPlayer.TVShowTitle")):
				self.mode = KODISPLAY_MODE.TVSHOW
			elif xbmc.getCondVisibility('Player.HasVideo'):
				self.mode = KODISPLAY_MODE.VIDEO
			elif xbmc.getCondVisibility('Player.HasAudio'):
				self.mode = KODISPLAY_MODE.MUSIC
			elif xbmc.getCondVisibility('System.ScreenSaverActive'):
				self.mode = KODISPLAY_MODE.SCREENSAVER
			else:
				self.mode = KODISPLAY_MODE.GENERAL

			self.lists.currentmode = self.mode
			mode = self.mode

			for index in range(0, len(self.layoutlist[mode])):
				if self.layoutlist[mode][index][1] == 'visible' or xbmc.getCondVisibility(self.layoutlist[mode][index][1]):
					self.querylist[mode][index][1] = 'visible'
				else:
					self.querylist[mode][index][1] = 'hide'

				if self.layoutlist[mode][index][0] == 'renderBackground':
					if self.layoutlist[mode][index][2] != self.querylist[mode][index][2]:
						self.querylist[mode][index][2] = self.layoutlist[mode][index][2]
				elif self.layoutlist[mode][index][0] == 'renderText':
					text = self.layoutlist[mode][index][2].strip().decode('utf-8')
					# get real text, if the variable text is a infolabel
					if text.lower().find('$info') >= 0:
						text = xbmc.getInfoLabel(text).strip().decode('utf-8')
						# remove special character from infolabel text
						for char in '()[]{}*':
							text = text.replace(char,'').strip()
					self.querylist[mode][index][2] = text
				elif self.layoutlist[mode][index][0] == 'renderImage':
					imagepath = self.layoutlist[mode][index][2]
					# get real imagepath, if the variable imagepath is a infolabel
					if imagepath.lower().find('$info') >= 0:
						imagepath = xbmc.getInfoLabel(imagepath)
						# if needed, let translate the path
						if imagepath.startswith('special://') >= 0:
							imagepath = xbmc.translatePath(imagepath)

					if imagepath:
						if os.path.isfile(imagepath):
							self.querylist[mode][index][3] = 'local'
						elif self.urlValidator(imagepath):
							self.querylist[mode][index][3] = 'url'
						else:
							self.querylist[mode][index][3] = 'noimage'
							if imagepath != self.renderlist[mode][index][3]:
								xbmc_log(xbmc.LOGWARNING, '%s from %s  getting %s - this is not an local path, neither a url' % (mode, self.layoutlist[mode][index][2], imagepath))
								self.renderlist[mode][index][3] = imagepath
					else:
						self.querylist[mode][index][3] = 'noimage'

					if imagepath != self.renderlist[mode][index][3]:
						self.renderlist[mode][index][0] = 0
						self.querylist[mode][index][2] = imagepath

				elif self.layoutlist[mode][index][0] == 'renderProgressbar':
					# timeToSecs from helper.py
					self.querylist[mode][index][2] = str(timeToSecs(xbmc.getInfoLabel("Player.Time(hh:mm:ss)")))
					self.querylist[mode][index][3] = str(timeToSecs(xbmc.getInfoLabel("Player.Duration(hh:mm:ss)")))

				self.querylist[mode][index][0] = 1

			xbmc.sleep(20)

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

	def urlValidator(self, url):
		try:
			result = urlparse(url)
			if result.scheme and result.netloc and result.path:
				return True
			else:
				return False
		except:
			return False
