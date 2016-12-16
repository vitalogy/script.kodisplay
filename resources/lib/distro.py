import os
import ConfigParser

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
