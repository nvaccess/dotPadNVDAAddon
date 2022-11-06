# A part of the DotPad NVDA add-on.
# Copyright (C) 2022 NV Access Limited.
# this code is licensed under the GNU General Public License version 2.


import math
import ctypes
import time
import wx
from .pyDotPad import DotPad, DotPadError, DotPadErrorCode
import core
import globalPluginHandler
import tones
from scriptHandler import script
import ui
import config
import api
import gui
from gui.settingsDialogs import SettingsDialog
from gui import guiHelper
import hwPortUtils
from .imageUtils import StretchMode, captureImage, getMonochromePixelUsingLocalBrightnessThreshold
from .dataUtils import (
	transposeValuesInDataset,
	scaleValuesInDataset,
	flipValuesInDataset,
	resizeDataset,
	drawContinuousDataset,
	drawDiscreteDataset,
	drawViewport,
	drawBrailleCells,
)
from .brailleUtils import translateTextToBraille


class DotPadDialog(SettingsDialog):
	title = "DotPad Settings"

	def __init__(self, parent, globalPlugin):
		self._globalPlugin = globalPlugin
		super().__init__(parent)

	def makeSettings(self,settingsSizer):
		conf = config.conf[self._globalPlugin._configName]
		settingsSizerHelper = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		curPort = conf['port']
		self._possiblePorts = [x['port'] for x in hwPortUtils.listComPorts()]
		self._possiblePorts.insert(0, "[Not set]")
		if not curPort:
			index = 0
		else:
			try:
				index = self._possiblePorts.index(curPort)
			except ValueError:
				# Port no longer exists, but list it as missing
				index = 1
				self._possiblePorts.insert(index, f"{curPort} (missing)")
		self.portList = settingsSizerHelper.addLabeledControl("Dot Pad COM port", wx.Choice, choices=self._possiblePorts)
		self.portList.SetSelection(index)

	def postInit(self):
		self.portList.SetFocus()

	def onOk(self, evt):
		index = self.portList.GetSelection()
		if index != 0:
			port = self._possiblePorts[index].split(' ')[0]
			try:
				self._globalPlugin.initDotPad(port)
			except (DotPadError, RuntimeError) as e:
				gui.messageBox(f"{e}", "Error")
				self.portList.SetFocus()
				return
		else:
			self._globalPlugin.terminateDotPad()
			port = ""
		conf = config.conf[self._globalPlugin._configName]
		conf['port'] = port
		super().onOk(evt)


class GlobalPlugin(globalPluginHandler.GlobalPlugin):

	curInstance = None

	_configName = 'addon_dotPad'
	_configSpec = {
		'port': 'string(default="")',
	}

	def __init__(self):
		super().__init__()
		config.conf.spec[self._configName] = self._configSpec
		self._dp = None
		self.__class__.curInstance = self

	def terminateDotPad(self):
		""" Turminates the DotPad connection if it exists."""
		self._dp = None

	def initDotPad(self, port: str, wait: bool=False):
		"""
		Initialises the connection to the DotPad, replacing any previous connection.
		@param wait: when true, blocks the caller for a sufficient amount of time to allow the dotPad device to initialize.
		"""
		portNum = int(port[3:])
		if self._dp:
			self.terminateDotPad()
		self._dp = DotPad(portNum, self.dpCallback)
		if wait:
			time.sleep(3)
		return self._dp

	def dpCallback(self, keyCode):
		# a semi-tone scale with the keys!
		import tones; tones.beep(440 * (2 ** (keyCode / 12)),50)

	def ensureDotPad(self):
		"""
		Ensures that the DotPad is initialized, displaying appropriate UI on errors.
		"""
		if self._dp:
			return self._dp
		conf = config.conf[self._configName]
		port = conf['port']
		if not port:
			# Not configured yet
			def handlePortConfig():
				res = gui.messageBox(
					"Port not configured. Would you like to open Dotpad settings? After configuring the port,  try performing this action again.",
					"DotPad",
					style=wx.YES | wx.NO | wx.ICON_WARNING
				)
				if res == wx.YES:
					gui.mainFrame._popupSettingsDialog(DotPadDialog,self)
			wx.CallAfter(handlePortConfig)
			return None
		ui.message("Initializing DotPad...")
		try:
			self.initDotPad(port, wait=True)
		except (DotPadError, RuntimeError) as e:
			wx.CallAfter(gui.messageBox,f"{e}", "DotPad Error")
			return None
		return self._dp

	def showNavigatorObject(self, isWhiteOnBlack=False):
		location = api.getNavigatorObject().location
		self.displayScreenLocation(location, isWhiteOnBlack=isWhiteOnBlack)

	def displayScreenLocation(self, location, isWhiteOnBlack=False):
		dp = self.ensureDotPad()
		if not dp:
			return
		stretchMode = StretchMode.WHITEONBLACK if isWhiteOnBlack else StretchMode.BLACKONWHITE
		image, (left, top, width, height) = captureImage(location.left, location.top, location.width, location.height, dp.hPixelCount, dp.vPixelCount, stretchMode=stretchMode)
		dp.resetDataBuffer()
		for y in range(top, top+height):
			for x in range(left, left + width):
				isWhite = getMonochromePixelUsingLocalBrightnessThreshold(image, x, y, blur=3)
				isRaised = isWhite if isWhiteOnBlack else not isWhite
				if isRaised:
					dp.setDotInDataBuffer(x, y)
		self._outputDataBuffer(dp)

	def _outputDataBuffer(self, dp):
		tones.beep(440, 60)
		try:
			dp.outputDataBuffer()
		except DotPadError as e:
			if e.code == DotPadErrorCode.DISPLAY_DATA_UNCHANGED:
				pass  # already displayed
			if e.code == DotPadErrorCode.DISPLAY_IN_PROGRESS:
				tones.beep(220,50)
				ui.message("Dot pad busy")
				return
		tones.beep(880, 60)
		ui.message("Done")



	@script(gesture="kb:NVDA+f8")
	def script_shownavigatorObject_blackOnWhite(self, gesture):
		self.showNavigatorObject()

	@script(gesture="kb:shift+NVDA+f8")
	def script_shownavigatorObject_whiteOnBlack(self, gesture):
		self.showNavigatorObject(isWhiteOnBlack=True)

	@script(gesture="kb:shift+NVDA+f7")
	def script_drawSineWave(self, gesture):
		dp = self.ensureDotPad()
		if not dp:
			return
		dp.resetDataBuffer()
		x, y, width, height, xCount, yCount = drawViewport(dp.setDotInDataBuffer, 0, 0, dp.hPixelCount, dp.vPixelCount, -1, 1, xCount=10, lockAspect=False)
		count = 100
		points = [math.sin((math.pi*2)*(x/count)) for x in range(count)]
		drawContinuousDataset(dp.setDotInDataBuffer, x, y, width, height, -1, 1.1, points)
		self._outputDataBuffer(dp)

	def drawChart(self,minY, maxY, points, yAxisLabel=None, xAxisLabel=None, xLabels=None, discrete=True): 
		dp = self.ensureDotPad()
		if not dp:
			return
		dp.resetDataBuffer()
		x, y, width, height, xCount, yCount = drawViewport(dp.setDotInDataBuffer, 0, 0, dp.hPixelCount, dp.vPixelCount, minY, maxY, xCount=len(points), xLabels=xLabels)
		drawDiscreteDataset(dp.setDotInDataBuffer, x, y, width, height, minY, maxY, points, space=2)
		textList = []
		if yAxisLabel:
			textList.append(yAxisLabel)
		if xAxisLabel:
			textList.append(f"by {xAxisLabel}")
		text = " ".join(textList)
		brailleCells = translateTextToBraille(text)
		drawBrailleCells(dp.setDotInDataBuffer, 0, dp.vPixelCount - 3, brailleCells)
		self._outputDataBuffer(dp)

	@script(gesture="kb:control+NVDA+f8")
	def script_showSettings(self, gesture):
		wx.CallAfter(gui.mainFrame._popupSettingsDialog,DotPadDialog,self)
