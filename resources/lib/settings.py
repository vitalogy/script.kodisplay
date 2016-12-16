import xbmcaddon

import config as glob



class Settings:

	def __init__(self, distro, display_w, display_h):
		self.addon = xbmcaddon.Addon()
		self.distro = distro
		self.display_w = display_w
		self.display_h = display_h

	def readSettings(self):
		self.fps = int(self.addon.getSetting('fps'))
		self.navtimeout = int(self.addon.getSetting('navtimeout'))
		self.scrollspeed = int(self.addon.getSetting('scrollspeed'))
		self.debug_show_fps = True if self.addon.getSetting('showfps') == 'true' else False
		self.debug_show_wid = True if self.addon.getSetting('showwindowid') == 'true' else False
		glob.addonDebug = True if self.addon.getSetting('addondebug') == 'true' else False
		self.debug_log_tpf = True if self.addon.getSetting('timeperframe') == 'true' else False
