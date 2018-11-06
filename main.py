# Import Built-in modules
import sys

# Import Third-party modules
import maya.cmds as cmds
import maya.mel as mel
import maya.OpenMayaUI as apiUI

try:
	from PySide2.QtCore import * 
	from PySide2.QtGui import * 
	from PySide2.QtWidgets import *
	from PySide2 import __version__
	from shiboken2 import wrapInstance 
except ImportError:
	from PySide.QtCore import * 
	from PySide.QtGui import * 
	from PySide import __version__
	from shiboken import wrapInstance 

def getMayaWindow():
	"""
	Get the main Maya window as a QtGui.QMainWindow instance
	@return: QtGui.QMainWindow instance of the top level Maya windows
	"""
	ptr = apiUI.MQtUtil.mainWindow()
	if ptr is not None:
		return wrapInstance(long(ptr), QWidget)

TOOLS_DATABASE_PATH = ''

class ShelfCreatorWin(QMainWindow):

	shelf_data = {}

	def __init__(self, parent = None) :
		super(ShelfCreatorWin, self).__init__(parent)

		mainWidget = QWidget()
		mainlayout = QGridLayout()
		title = QLabel()
		title.setText("Tools browser")
		title.setStyleSheet("font-size: 16pt;")

		shelf_label = QLabel()
		shelf_label.setText("Shelf :")
		self.shelf_input = QComboBox()
		self.addshelf = QPushButton()
		self.addshelf.setText("Add shelf")
		# shelf_label.setT

		filter_label = QLabel()
		filter_label.setText("Filter :")
		self.filter_input = QLineEdit()

		self.toolsList = QListWidget()

		mainlayout.addWidget(title, 0,0,1,3)
		mainlayout.addWidget(shelf_label, 1,0)
		mainlayout.addWidget(self.shelf_input, 1,1)
		mainlayout.addWidget(self.addshelf, 1,2)
		mainlayout.addWidget(filter_label, 2,0,1,1)
		mainlayout.addWidget(self.filter_input, 2,1,1,2)
		mainlayout.addWidget(self.toolsList,3,0,1,3)
		# mainlayout.setStretch(1,1)
		mainlayout.setColumnStretch(1,1)
		mainWidget.setLayout(mainlayout)

		self.setCentralWidget(mainWidget)

		self.initUI()
		self.resize(410,621)

		# ============================
		self.shelf_input.currentIndexChanged.connect(self.refresh)
		self.addshelf.clicked.connect(self._generateShelf)

	def initUI(self):
		self.shelf_input.addItems(listShelf())
		self.refresh()

	def refresh(self):

		self.shelf_data = loadToolsData(self.currentShelf)

		for tool, data in self.shelf_data['buttons'].items():
			self._addToolToList(
				 name = tool, 
				 description = data.get('description', 'Description'), 
				 creator = data.get('creator', 'Unknow'), 
				 icon = data.get('icon', ''), 
				 command= data.get('command', 'pass'))

	def _addToolToList(self, name, description = 'Description', creator = '', icon = '', command='pass' ):

		item = QListWidgetItem()
		widget = ToolsListWidgetItem(name = name,
			description = description,
			creator = creator,
			icon = icon,
			command= command)
		item.setSizeHint(widget.sizeHint())  

		self.toolsList.addItem(item)
		self.toolsList.setItemWidget(item, widget)

	def _generateShelf(self):

		if cmds.shelfLayout(self.currentShelf, ex=1) :
			result = cmds.confirmDialog( title='Confirm',
			 message='Overwrite existing shelf?',
			 button=['Yes','No'],
			 defaultButton='Yes',
			 cancelButton='No',
			 dismissString='No' )

			if result == 'No':
				return

		createShelf(name = self.currentShelf)

		for name, attr in self.shelf_data['buttons'].items():
			if attr.get('type', '') == 'button':
				cmds.setParent( self.currentShelf )
				cmds.shelfButton(width=32, height=32, image=attr.get('icon', ''), l='', command=attr.get('command', 'pass'), dcc='pass')

	@property
	def currentShelf(self):
		return self.shelf_input.currentText()
	
class ToolsListWidgetItem(QWidget) :

	def __init__(self, name, description = 'Description', creator = '', icon = '', command='', parent = None):
		super(ToolsListWidgetItem, self).__init__(parent)

		self.command = command or 'pass'
		self.iconpath = icon or ''

		mainlayout = QGridLayout()
		# mainlayout.setSpacing(0)
		mainlayout.setMargin(0)
		mainlayout.setContentsMargins(3,3,3,3)
		self.icon = QLabel()
		self.name_label = QLabel()
		self.name_label.setStyleSheet("font-style: bold; font-size: 12pt;")
		self.description_label = QLabel()
		self.creator_label = QLabel()

		# BUTTON
		self.run_button = QPushButton()
		self.run_button.setText('Run')
		self.add_button = QPushButton()
		self.add_button.setText("Add to shelf")

		mainlayout.addWidget( self.icon, 0, 0, 3, 1, alignment = Qt.AlignHCenter )
		mainlayout.addWidget(self.name_label, 0, 1, 1,3)
		mainlayout.addWidget(self.description_label, 1, 1, 1, 3)
		mainlayout.addWidget(self.creator_label, 2, 1)

		mainlayout.addWidget(self.run_button, 2, 2)
		mainlayout.addWidget(self.add_button, 2, 3)
		mainlayout.setColumnStretch(1,1)

		self.setLayout(mainlayout)

		# ---------------------------
		self.icon.setPixmap(QPixmap(self.iconpath).scaled(56,56))
		self.name_label.setText(name)
		self.description_label.setText(description)
		self.creator_label.setText(creator)

		# ---------------------------
		self.run_button.clicked.connect(self.run)
		self.add_button.clicked.connect(self.addToShelf)

	def run(self):
		exec(self.command)

	def addToShelf(self):
		cmds.setParent(currentActiveShelf())
		cmds.shelfButton(width=32, height=32, image=self.iconpath, l='', command=self.command, dcc='pass')

	@property
	def name(self):
		return self.name_label.text()

	@property
	def description(self):
		return self.description_label.text()

	@property
	def creator(self):
		return self.creator_label.text()

def currentActiveShelf():
	return mel.eval("tabLayout -q -selectTab $gShelfTopLevel")

def createShelf(name):
	'''Checks if the shelf exists and empties it if it does or creates it if it does not.'''
	if cmds.shelfLayout(name, ex=1):
		if cmds.shelfLayout(name, q=1, ca=1):
			for each in cmds.shelfLayout(name, q=1, ca=1):
				cmds.deleteUI(each)
	else :
		cmds.shelfLayout(name, p="ShelfLayout")

def listShelf():
	return ['testNook']

def loadToolsData(shelfname):

	# TOOLS_DATABASE_PATH

	mock_data = \
	{
		"info" : {
			"name" : "testNook",
			"iconpath" : ""
		},
		"buttons": {
			"ShowMs" : {
				"type" : "button",
				"icon" : "H:/programming/Python/mayaShelfCreator/icon/sublime.png",
				"command" : "import maya.cmds as cmds\ncmds.confirmDialog(m=\"Hello world\")",
				"doubleCommand" : ""
			},
			"Test02":{
				"type" : "button",
				"icon" : "H:/programming/Python/mayaShelfCreator/icon/sublime.png",
				"command" : "",
				"doubleCommand" : ""
			}
		}
	}

	return mock_data

def run():
	win = ShelfCreatorWin(getMayaWindow())
	win.show()

if __name__ == '__main__':
	win = ShelfCreatorWin(getMayaWindow())
	win.show()
