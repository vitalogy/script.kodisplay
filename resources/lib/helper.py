# inspired by oe.py from service.libreelec.settings
#      Copyright (C) 2009-2013 Stephan Raue (stephan@openelec.tv)
#      Copyright (C) 2013 Lutz Fiebach (lufie@openelec.tv)


import os
import xbmc
import traceback
import subprocess


def dbg_log(source, text, level=4):
	if level == 0 and os.environ.get('DEBUG', 'no') == 'no':
		return
	xbmc.log('## KoDisplay Addon ## ' + source + ' ## ' + text, level)
	if level == 4:
		xbmc.log(traceback.format_exc(), level)


def notify(title, message, time=5000, icon='icon'):
	try:
		dbg_log('::notify', 'enter_function', 0)
		msg = 'Notification("%s", "%s", %d, "%s")' % (
			title,
			message[0:64],
			time,
			icon,
			)
		xbmc.executebuiltin(msg)
		dbg_log('::notify', 'exit_function', 0)
	except Exception, e:
		dbg_log('::notify', 'ERROR: (' + repr(e) + ')')


def execute(command_line, get_result=0):
	try:
		dbg_log('::execute', 'enter_function', 0)
		dbg_log('::execute::command: ', command_line, 0)
		if get_result == 0:
			process = subprocess.Popen(command_line, shell=True, close_fds=True)
			process.wait()
		else:
			result = ''
			process = subprocess.Popen(command_line, shell=True, close_fds=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
			process.wait()
			for line in process.stdout.readlines():
				result = result + line
			return result
		dbg_log('::execute', 'exit_function', 0)
	except Exception, e:
		dbg_log('::execute', 'ERROR: (' + repr(e) + ')')
