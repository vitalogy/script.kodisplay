from layout import LayoutList

class Lists():

	def __init__(self, distro, display_w, display_h):
		self.currentmode = 0
		self.layoutlist = LayoutList(distro, display_w, display_h)

	def createLists(self):
		if not self.layoutlist.xmlToList():
			return False

		# create a list that holds the layout information from TFT.xml
		self.layout = self.layoutlist.returnLayoutList()

		# create a list for holding the data queried from kodi
		self.query = [[[0 for k in range(0, 4)] for j in range(0, len(self.layout[i]))] for i in range(0, len(self.layout))]

		# create a list for holding render information (surfaces, positions)
		self.render = [[[0 for k in range(0, 5)] for j in range(0, len(self.layout[i]))] for i in range(0, len(self.layout))]

		# create a list for holding scroll information
		# if the width of a text surface greater then display width, put the scroll informations in this list
		self.scroll = [[[1 for k in range(0, 2)] for j in range(0, len(self.layout[i]))] for i in range(0, len(self.layout))]

		return True
