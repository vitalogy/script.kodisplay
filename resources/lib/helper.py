import os
import xbmc
import time
import string
import traceback
import subprocess
import ConfigParser
import config as glob




# from http://stackoverflow.com/questions/1265665/python-check-if-a-string-represents-an-int-without-using-try-except
def isInteger(v):
    v = str(v).strip()
    return v=='0' or (v if v.find('..') > -1 else v.lstrip('-+').rstrip('0').rstrip('.')).isdigit()




def timeToSecs(time):
	t = time.split(':')
	if t == '':
		return 0

	try:
		ret = int(t[0]) * 3600 + int(t[1]) * 60 + int(t[2])
	except:
		ret = 0

	return ret




def isColorHex(value):
	hex_digits = set("0123456789abcdef")

	lv = len(value)
	if lv == 7 and value.startswith('#'):
		value = value.lstrip('#')
		for char in value:
			if not (char.lower() in hex_digits):
				return False
	else:
		return False

	return True

# from http://stackoverflow.com/questions/4296249/how-do-i-convert-a-hex-triplet-to-an-rgb-tuple-and-back
def hexToRGB(value):
	value = value.lstrip('#')
	lv = len(value)
	return tuple(int(value[i:i+lv/3], 16) for i in range(0, lv, lv/3))




# from http://www.pygame.org/pcr/transform_scale/
def aspect_scale(img,(bx,by)):
	""" Scales 'img' to fit into box bx/by.
	This method will retain the original image's aspect ratio """
	ix,iy = img.get_size()
	if ix > iy:
		# fit to width
		scale_factor = bx/float(ix)
		sy = scale_factor * iy
		if sy > by:
			scale_factor = by/float(iy)
			sx = scale_factor * ix
			sy = by
		else:
			sx = bx
	else:
		# fit to height
		scale_factor = by/float(iy)
		sx = scale_factor * ix
		if sx > bx:
			scale_factor = bx/float(ix)
			sx = bx
			sy = scale_factor * iy
		else:
			sy = by

	return (int(sx), int(sy))




class FakeSecHead(object):
	def __init__(self, fp):
		self.fp = fp
		self.sechead = '[section]\n'

	def readline(self):
		if self.sechead:
			try:
				return self.sechead
			finally:
				self.sechead = None
		else:
			return self.fp.readline()

def getDistroName():
	parser = ConfigParser.SafeConfigParser()
	file = '/etc/os-release'
	distro = 'Linux'
	if os.path.isfile(file):
		parser.readfp(FakeSecHead(open(file)))
		d = parser.get('section', 'NAME')
		distro = d.replace("\"", "")
	return distro







""" https://github.com/LibreELEC/service.libreelec.settings
   	taken from oe.py and modified
       Copyright (C) 2009-2013 Stephan Raue (stephan@openelec.tv)
   	   Copyright (C) 2013 Lutz Fiebach (lufie@openelec.tv)

	xbmc.LOGDEBUG   = 0
	xbmc.LOGINFO    = 1
	xbmc.LOGNOTICE  = 2
	xbmc.LOGWARNING = 3
	xbmc.LOGERROR   = 4
	xbmc.LOGSEVERE  = 5
	xbmc.LOGFATAL   = 6
	xbmc.LOGNONE    = 7
"""

def xbmc_log(level, text):
	if glob.addonDebug and level == 0:
		xbmc.log('# KoDisplay [DEBUG] -- ' + text, 2)
	else:
		xbmc.log('# KoDisplay -- ' + text, level)

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



def execute(command_line, get_result=0):
	try:
		xbmc_log(xbmc.LOGDEBUG, 'execute command: ' + command_line)
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
		xbmc_log(xbmc.LOGDEBUG, 'executed command has been finshed successfully')
	except Exception, e:
		xbmc_log(xbmc.LOGERROR, 'executed command :: ' + command_line + ' :: with ERROR: (' + repr(e) + ')')





