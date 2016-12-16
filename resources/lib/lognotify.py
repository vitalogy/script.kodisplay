import xbmc
import config as glob

"""	xbmc.LOGDEBUG   = 0
	xbmc.LOGINFO    = 1
	xbmc.LOGNOTICE  = 2
	xbmc.LOGWARNING = 3
	xbmc.LOGERROR   = 4
	xbmc.LOGSEVERE  = 5
	xbmc.LOGFATAL   = 6
	xbmc.LOGNONE    = 7
"""

def xbmc_log(level, message):
	if glob.addonDebug and level == 0:
		xbmc.log('# KoDisplay [DEBUG] -- ' + message, 2)
	else:
		xbmc.log('# KoDisplay -- ' + message, level)

	if level == 4:
		xbmc.log(traceback.format_exc(), level)


def notify(title, message, time, icon, level=0):
	try:
		#xbmc_log(level, message)
		msg = 'Notification("%s", "%s", %d, "%s")' % (
			title,
			message[0:64],
			time,
			icon,
			)
		xbmc.executebuiltin(msg)
	except Exception, e:
		xbmc_log(xbmc.LOGERROR, 'Notification ERROR: (' + repr(e) + ')')
