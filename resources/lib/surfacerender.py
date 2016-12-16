import threading
import io
from urllib2 import urlopen
import xbmc

from lognotify import xbmc_log
from helper import *



class SurfaceRenderingThread(threading.Thread):

	def __init__(self, pygame, settings, lists):
		threading.Thread.__init__(self)
		self.abort = False
		self.pygame = pygame
		self.settings = settings
		self.lists = lists
		self.layoutlist = lists.layout
		self.querylist = lists.query
		self.renderlist = lists.render
		self.scrolllist = lists.scroll

	def stop(self):
		self.abort = True
		xbmc_log(xbmc.LOGDEBUG, 'Thread to render the surfaces had been ask to stop')

	def run(self):
		xbmc_log(xbmc.LOGDEBUG, 'Thread to render the surfaces was started successfully')
		while not self.abort:
			xbmc.sleep(20)
			mode = self.lists.currentmode
			for index in range(0, len(self.layoutlist[mode])):
				if self.querylist[mode][index][0] == 1:
					func = self.layoutlist[mode][index][0]
					values = self.layoutlist[mode][index][3:]
					values.extend([mode, index])
					getattr(self, func)(*values)

	def renderBackground(self, mode, index):
		color = self.querylist[mode][index][2]
		if color != self.renderlist[mode][index][3]:
			bkgsurface = self.pygame.Surface((self.settings.display_w, self.settings.display_h)).convert()
			bkgsurface.fill(hexToRGB(self.querylist[mode][index][2]))
			bkgpos = bkgsurface.get_rect()
			bkgpos.x = 0
			bkgpos.y = 0
			self.renderlist[mode][index][0] = 1
			self.renderlist[mode][index][1] = bkgsurface
			self.renderlist[mode][index][2] = bkgpos
			self.renderlist[mode][index][3] = color

	def renderText(self, scrollmode, offset, txtfont, size, color, xpos, cx, ypos, cy, mode, index):
		text = self.querylist[mode][index][2]
		if text != self.renderlist[mode][index][3]:
			if txtfont == 'none':
				font = self.pygame.font.Font(None, size)
			else:
				font = self.pygame.font.Font(txtfont, size)
			txtsurface = font.render(text, 1, color).convert_alpha()
			# save the whole surface, even it is larger then the max_width
			# so we will need it later, if the text does not change
			self.renderlist[mode][index][4] = txtsurface
			self.renderlist[mode][index][3] = text
		else:
			txtsurface = self.renderlist[mode][index][4]

		# if the txtsurface width is too large
		if (cx == 1 and txtsurface.get_width() > self.settings.display_w + 20) or \
			(cx == 0 and txtsurface.get_width() > (self.settings.display_w - abs(xpos) + 10)):

			# surface is centered in x, so max_width is equal the display width
			# else, max_width is the display width less the given xpos
			if cx == 1:
				xpos = 0
				max_width = self.settings.display_w
			else:
				max_width = self.settings.display_w - abs(xpos)

			# directionx = saved direction of x-scrolling (1 or -1) from scrolllist
			# scrollstep = direction_x * scrollspeed from settings
			# oldposition = saved last position from scrolllist
			direction_x = self.scrolllist[mode][index][0]
			scrollstep = direction_x * self.settings.scrollspeed
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
				txtsurface = txtsurface.subsurface(self.pygame.Rect(location, size))
				txtpos = txtsurface.get_rect()

			elif scrollmode == 'marquee':
				bSurface = False
				if (oldposition + scrollstep) > txtsurface.get_width() + offset:
					newposition = 0
					location = (newposition, 0)
					size = (max_width, txtsurface.get_height())
					txtsurface = txtsurface.subsurface(self.pygame.Rect(location, size))
				elif (oldposition + scrollstep) > (txtsurface.get_width() - max_width):
					newposition = oldposition + scrollstep
					asurface_width = txtsurface.get_width() - newposition
					location = (newposition, 0)
					size = (asurface_width, txtsurface.get_height())
					atxtsurface = txtsurface.subsurface(self.pygame.Rect(location, size))
					if (max_width - asurface_width) > offset:
						bsurface_width = max_width - asurface_width - offset
						location = (0, 0)
						size = (bsurface_width, txtsurface.get_height())
						btxtsurface = txtsurface.subsurface(self.pygame.Rect(location, size))
						bSurface = True
					# create a new surface to blit the text surface(s)
					txtsurface = self.pygame.Surface((max_width, txtsurface.get_height()), self.pygame.SRCALPHA, 32)
					txtsurface = txtsurface.convert_alpha()
					txtsurface.blit(atxtsurface, (0, 0))
					if bSurface:
						txtsurface.blit(btxtsurface, ((max_width - bsurface_width), 0))
				else:
					newposition = oldposition + scrollstep
					location = (newposition, 0)
					size = (max_width, txtsurface.get_height())
					txtsurface = txtsurface.subsurface(self.pygame.Rect(location, size))

			self.scrolllist[mode][index][0] = direction_x
			self.scrolllist[mode][index][1] = newposition

			txtpos = txtsurface.get_rect()

			if cx == 0:
				if xpos < 0:
					txtpos.x = self.settings.display_w - txtsurface.get_width() + xpos
				else:
					txtpos.x = xpos
			else:
				txtpos.x = 0

		else:
			self.scrolllist[mode][index][1] = 0
			txtpos = txtsurface.get_rect()
			if cx == 0:
				if xpos < 0:
					txtpos.x = self.settings.display_w - txtsurface.get_width() + xpos
				else:
					txtpos.x = xpos
			else:
				txtpos.centerx = xpos

		if cy == 0:
			if ypos < 0:
				txtpos.y = self.settings.display_h - txtsurface.get_height() + ypos
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

				imgsurface = self.pygame.image.load(imagefile)
				if resx > 0 and resy > 0:
					# aspact_scale() from helper.py
					imgsurface = self.pygame.transform.scale(imgsurface, aspect_scale(imgsurface, (resx, resy)))
				elif resx > 0 and resy == 0:
					scale_factor = resx / float(imgsurface.get_width())
					imgsurface = self.pygame.transform.scale(imgsurface, (resx, int(scale_factor * imgsurface.get_height())))
				elif resx == 0 and resy > 0:
					scale_factor = resy / float(imgsurface.get_height())
					imgsurface = self.pygame.transform.scale(imgsurface, (int(scale_factor * imgsurface.get_width()), resy))

				imgsurface = imgsurface.convert_alpha()
				imgpos = imgsurface.get_rect()

				if border > 0:
					imgborder = self.pygame.Rect(imgpos)
					self.pygame.draw.rect(imgsurface, bordercolor, imgpos, border)

				if cx == 0:
					if xpos < 0:
						imgpos.x = self.settings.display_w - imgsurface.get_width() + xpos
					else:
						imgpos.x = xpos
				else:
					imgpos.centerx = xpos

				if cy == 0:
					if ypos < 0:
						imgpos.y = self.settings.display_h - imgsurface.get_height() + ypos
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
			rectsurface = self.pygame.Surface((width, height)).convert()
			rectpos = rectsurface.get_rect()
			progbar = self.pygame.Rect(0, 0, width, height)
			progbar.x = 0
			progbar.y = 0

			if cx == 0:
				if xpos < 0:
					rectpos.x = self.settings.display_w - width + xpos
				else:
					rectpos.x = xpos
			else:
				rectpos.centerx = xpos

			if cy == 0:
				if ypos < 0:
					rectpos.y = self.settings.display_h - height + ypos
				else:
					rectpos.y = ypos
			else:
				rectpos.centery = ypos

			if (playtime > 0 and duration > 0):
				percent = int(( 1. * progbar.width / duration ) * playtime)
			else:
				percent = 0

			progbar_done = self.pygame.Rect(progbar)
			progbar_done.width = percent
			self.pygame.draw.rect(rectsurface, barcolor, progbar )
			self.pygame.draw.rect(rectsurface, progresscolor, progbar_done )
			if border > 0:
				self.pygame.draw.rect(rectsurface, bordercolor, progbar, border)

			self.renderlist[mode][index][0] = 1
			self.renderlist[mode][index][1] = rectsurface
			self.renderlist[mode][index][2] = rectpos
			self.renderlist[mode][index][3] = playtime
