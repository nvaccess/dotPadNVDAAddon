# A part of the DotPad NVDA add-on.
# A part of the DotPad NVDA add-on.
# Copyright (C) 2022 NV Access Limited.
# this code is licensed under the GNU General Public License version 2.


import math
import ctypes
import time
import wx
import core
from .pyDotPad import DotPad, DotPadError, DotPadErrorCode
import core
import globalPluginHandler
import tones
from scriptHandler import script, getLastScriptRepeatCount
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
	BarChart,
	ScrollableChart,
	LineChart,
		drawBrailleCells,
)
from .brailleUtils import translateTextToBraille


class DotPadChartDialog(SettingsDialog):
	title = "DotPad Chart"

	def __init__(self, parent, globalPlugin, minVal, maxVal, datasets, xAxisLabel, yAxisLabel):
		self._globalPlugin = globalPlugin
		self._minVal = minVal
		self._maxVal = maxVal
		self._datasets = datasets
		self._xAxisLabel = xAxisLabel
		self._yAxisLabel = yAxisLabel
		super().__init__(parent)

	def makeSettings(self,settingsSizer):
		lastChart = self._globalPlugin.curChart
		settingsSizerHelper = guiHelper.BoxSizerHelper(self, sizer=settingsSizer)
		caption = f"Vertical represents {self._yAxisLabel}, horizontal represents {self._xAxisLabel}"
		settingsSizerHelper.addItem(wx.StaticText(self, label=caption))
		self._chartTypes = [
			(BarChart, "Bar chart: discrete data in columns which can be scrolled"),
			(LineChart, "Line chart: A continuous trend line over a set of values"),
		]
		self.chartTypesControl = settingsSizerHelper.addLabeledControl("Chart type", wx.Choice, choices=[x[1] for x in self._chartTypes])
		index = 0
		if lastChart:
			lastChartType = type(lastChart)
			try:
				index = [x[0] for x in self._chartTypes].index(lastChartType)
			except ValueError:
				pass
		self.chartTypesControl.SetSelection(index)
		self.showVerticalRulerCheckBox = wx.CheckBox(self, label="Show vertical ruler")
		self.showVerticalRulerCheckBox.SetValue(lastChart.showVerticalRuler if lastChart else True)
		settingsSizerHelper.addItem(self.showVerticalRulerCheckBox)
		self.showHorizontalRulerCheckBox = wx.CheckBox(self, label="Show horizontal ruler")
		self.showHorizontalRulerCheckBox.SetValue(lastChart.showHorizontalRuler if lastChart else True)
		settingsSizerHelper.addItem(self.showHorizontalRulerCheckBox)
		self.datasetCheckboxes = {}
		for datasetName, dataSetVals in self._datasets.items():
			datasetCheckBox = wx.CheckBox(self, label=f"Show {datasetName} dataset")
			if not lastChart or datasetName in lastChart.datasets:
				datasetCheckBox.SetValue(True)
			self.datasetCheckboxes[datasetName] = datasetCheckBox
			settingsSizerHelper.addItem(datasetCheckBox)

	def postInit(self):
		self.chartTypesControl.SetFocus()

	def onOk(self, evt):
		ChartType = self._chartTypes[self.chartTypesControl.GetSelection()][0]
		showVerticalRuler = self.showVerticalRulerCheckBox.GetValue()
		showHorizontalRuler = self.showHorizontalRulerCheckBox.GetValue()
		datasets = {
			name: self._datasets[name]
			for name,checkbox in self.datasetCheckboxes.items()
			if checkbox.GetValue()
		}
		dp = self._globalPlugin.ensureDotPad()
		if not dp:
			return
		self._globalPlugin.curChart = ChartType(dp.hPixelCount, dp.vPixelCount, self._minVal, self._maxVal, datasets, showVerticalRuler=showVerticalRuler, showHorizontalRuler=showHorizontalRuler)
		dp.resetDataBuffer()
		self._globalPlugin.curChart.draw(dp.setDotInDataBuffer)
		self._globalPlugin._outputDataBuffer(dp)
		super().onOk(evt)


class DotPadConnectionDialog(SettingsDialog):
	title = "DotPad Connection"

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
	curChart = None

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
		if keyCode == 0:
			core.callLater(0, self.scroll, back=True)
		else:
			core.callLater(0, self.scroll, back=False)

	def scroll(self, back=False):
		if not isinstance(self.curChart, ScrollableChart):
			ui.message("Nothing to scroll")
			return
		scrollFunc = self.curChart.scrollBack if back else self.curChart.scrollForward
		if not scrollFunc():
			ui.message("No more data")
			return
		dp = self._dp
		dp.resetDataBuffer()
		self.curChart.draw(dp.setDotInDataBuffer)
		self._outputDataBuffer(dp)

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
					gui.mainFrame._popupSettingsDialog(DotPadConnectionDialog,self)
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

	def _outputDataBuffer(self, dp, doFullRefresh=False):
		if not doFullRefresh:
			doFullRefresh = getLastScriptRepeatCount() > 0
		tones.beep(440, 60)
		try:
			dp.outputDataBuffer(doFullRefresh)
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

	def drawChart(self,minVal, maxVal, datasets, yAxisLabel, xAxisLabel):
		gui.mainFrame._popupSettingsDialog(DotPadChartDialog,self, minVal, maxVal, datasets, xAxisLabel, yAxisLabel)


	@script(gesture="kb:control+NVDA+f8")
	def script_showSettings(self, gesture):
		wx.CallAfter(gui.mainFrame._popupSettingsDialog,DotPadConnectionDialog,self)
