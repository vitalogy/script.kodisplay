import time
import xbmc
import xbmcgui
import config as glob

modes = 'startscreen', 'general', 'navigation', 'music', 'video', 'pvr', 'picture', 'weather', 'screensaver'

class TFT_MODE:
	STARTSCREEN = 0
	GENERAL     = 1
	NAVIGATION  = 2
	MUSIC       = 3
	VIDEO       = 4
	PVR         = 5
	PICTURE     = 6
	WEATHER     = 7
	SCREENSAVER = 8
	MAX_MODES   = 9

class WINDOW_IDS:
	WINDOW_MAINMENU              = 10000
	WINDOW_PROGRAM               = 10001
	WINDOW_OPTION                = 10004
	WINDOW_SYSTEMINFO            = 10007
	WINDOW_WEATHER               = 12600
	WINDOW_PVR                   = 10601
	WINDOW_PVR_MAX               = 10699
	WINDOW_VIDEOS                = 10006
	WINDOW_VIDEO_FILES           = 10024
	WINDOW_VIDEO_NAV             = 10025
	WINDOW_VIDEO_PLAYLIST        = 10028
	WINDOW_MUSIC                 = 10005
	WINDOW_MUSIC_PLAYLIST        = 10500
	WINDOW_MUSIC_FILES           = 10501
	WINDOW_MUSIC_NAV             = 10502
	WINDOW_MUSIC_PLAYLIST_EDITOR = 10503
	WINDOW_PICTURES              = 10002
	WINDOW_DIALOG_VOLUME_BAR     = 10104
	WINDOW_DIALOG_KAI_TOAST      = 10107



def playingSomething():
	player = "stopped"
	if xbmc.getCondVisibility("Player.Playing"):
		player = "playing"
	elif xbmc.getCondVisibility("Player.Paused"):
		player = "paused"
	elif xbmc.getCondVisibility("Player.Forwarding"):
		player = "forwarding"
	elif xbmc.getCondVisibility("Player.Rewinding"):
		player = "rewindig"

	return player



def getWinMode():
	ret = ''

	WindowID = int(xbmcgui.getCurrentWindowId())
	if WindowID >= WINDOW_IDS.WINDOW_PVR and WindowID <= WINDOW_IDS.WINDOW_PVR_MAX:
		ret = TFT_MODE.PVR
	elif WindowID in [WINDOW_IDS.WINDOW_VIDEOS, WINDOW_IDS.WINDOW_VIDEO_FILES,
					WINDOW_IDS.WINDOW_VIDEO_NAV, WINDOW_IDS.WINDOW_VIDEO_PLAYLIST]:
		ret = TFT_MODE.VIDEO
	elif WindowID in [WINDOW_IDS.WINDOW_MUSIC, WINDOW_IDS.WINDOW_MUSIC_PLAYLIST,
					WINDOW_IDS.WINDOW_MUSIC_FILES, WINDOW_IDS.WINDOW_MUSIC_NAV,
					WINDOW_IDS.WINDOW_MUSIC_PLAYLIST_EDITOR]:
		ret = TFTMODE.MUSIC
	elif WindowID == WINDOW_IDS.WINDOW_PICTURES:
		ret = TFT_MODE.PICTURE
	elif WindowID == WINDOW_IDS.WINDOW_WEATHER:
		ret = TFT_MODE.WEATHER

	return (ret, str(WindowID))


def isNavigation(navtimeout):
	ret = False

	menu = xbmc.getInfoLabel("$INFO[System.CurrentWindow]")
	subMenu = xbmc.getInfoLabel("$INFO[System.CurrentControl]")

	if menu != glob.oldMenu or subMenu != glob.oldSubMenu or (glob.navTimer + navtimeout) > time.time():
		ret = True
		if menu != glob.oldMenu or subMenu != glob.oldSubMenu:
			glob.navTimer = time.time()
		glob.oldMenu = menu
		glob.oldSubMenu = subMenu

	return ret

