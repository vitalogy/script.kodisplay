import os
import xbmc
import time
import string
import traceback
import subprocess




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
