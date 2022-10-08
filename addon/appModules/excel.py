# A part of the DotPad NVDA add-on.
# Copyright (C) 2015 - 2022 NV Access Limited.
# this code is licensed under the GNU General Public License version 2.

from globalPlugins.dotPad import GlobalPlugin
import api
import UIAHandler
from logHandler import log
import controlTypes
import NVDAObjects.window._msOfficeChart as msOfficeChart
from NVDAObjects.window import Window


try:
	from nvdaBuiltin.appModules import excel as BaseAppModule
except ImportError:
	import appModuleHandler as BaseAppModule

class ChartEmbosser(Window):

	def script_embossChart(self,gesture):
		focus=api.getFocusObject()
		valuesList=[]
		discrete=focus.officeChartObject.chartType not in (msOfficeChart.xl3DLine, msOfficeChart.xlLine, msOfficeChart.xlLineMarkers, msOfficeChart.xlLineMarkersStacked, msOfficeChart.xlLineMarkersStacked100, msOfficeChart.xlLineStacked, msOfficeChart.xlLineStacked100)
		sr=focus.officeChartObject.seriesCollection()
		if isinstance(focus,msOfficeChart.OfficeChartElementSeries):
			item = sr.item(focus.arg1)
		else:
			item = sr.item(1)
		valuesList = list(item.values)
		try:
			valueLabels = list(item.xValues)
		except:
			valueLabels = None
		print(f"valueLabels {valueLabels}")
		yAxisLabel = None
		xAxisLabel = None
		if focus.officeChartObject.HasAxis(msOfficeChart.xlValue):
			yAxis=focus.officeChartObject.axes(msOfficeChart.xlValue)
			minY = yAxis.minimumScale
			maxY = yAxis.maximumScale
			if yAxis.HasTitle:
				yAxisLabel = yAxis.AxisTitle.Text
		else:
			minY = min(valuesList)
			maxY = max(valuesList)
		if focus.officeChartObject.HasAxis(msOfficeChart.xlCategory):
			xAxis=focus.officeChartObject.axes(msOfficeChart.xlCategory)
			if xAxis.HasTitle:
				xAxisLabel = xAxis.AxisTitle.Text
		GlobalPlugin.curInstance.drawChart(minY, maxY, valuesList, xAxisLabel=xAxisLabel, yAxisLabel=yAxisLabel, xLabels=valueLabels, discrete=discrete)

	__gestures={
		"kb:NVDA+f6":"embossChart",
	}

class AppModule(BaseAppModule.AppModule):

	def event_gainFocus(self, obj, nextHandler):
		# There is a strange gainFocus on a dead object when moving around charts.
		# Ignore it.
		if not obj.role:
			return
		nextHandler()

	def chooseNVDAObjectOverlayClasses(self,obj,clsList):
		if isinstance(obj,msOfficeChart.OfficeChart) or isinstance(obj,msOfficeChart.OfficeChartElementBase):
			clsList.insert(0,ChartEmbosser)
