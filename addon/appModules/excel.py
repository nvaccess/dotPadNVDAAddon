# A part of the DotPad NVDA add-on.
# Copyright (C) 2015 - 2022 NV Access Limited.
# this code is licensed under the GNU General Public License version 2.

from globalPlugins.dotPad import GlobalPlugin
import winUser
import api
import ui
from logHandler import log
import controlTypes
from scriptHandler import script
import NVDAObjects.window._msOfficeChart as msOfficeChart
from NVDAObjects.window import Window
from NVDAObjects.window.excel import Excel7Window


try:
	from nvdaBuiltin.appModules import excel as BaseAppModule
except ImportError:
	import appModuleHandler as BaseAppModule

class AppModule(BaseAppModule.AppModule):

	@script(gesture="kb:NVDA+f6")
	def script_embossChart(self, gesture):
		hwndFocus = winUser.getGUIThreadInfo(0).hwndFocus
		if winUser.getClassName(hwndFocus) != 'EXCEL7':
			ui.message("Not a sheet or chart")
			return
		excelWindow = Excel7Window(windowHandle=hwndFocus)
		selection = excelWindow._getSelection()
		if not isinstance(selection, (msOfficeChart.OfficeChartElementBase, msOfficeChart.OfficeChartElementList)):
			ui.message("Cannot locate chart")
			return
		chart = selection.officeChartObject
		valuesList=[]
		sr=chart.seriesCollection()
		seriesObjects = []
		for index in range(1, sr.count + 1):
			seriesObjects.append(sr.item(index))
		datasets = {item.name: list(item.values) for item in seriesObjects}
		yAxisLabel = None
		xAxisLabel = None
		if chart.HasAxis(msOfficeChart.xlValue):
			yAxis=chart.axes(msOfficeChart.xlValue)
			minY = yAxis.minimumScale
			maxY = yAxis.maximumScale
			if yAxis.HasTitle:
				yAxisLabel = yAxis.AxisTitle.Text
		else:
			minY = min(min(dataset) for dataset in datasets)
			maxY = max(max(dataset) for dataset in datasets)
		if chart.HasAxis(msOfficeChart.xlCategory):
			xAxis=chart.axes(msOfficeChart.xlCategory)
			if xAxis.HasTitle:
				xAxisLabel = xAxis.AxisTitle.Text
		GlobalPlugin.curInstance.drawChart(minY, maxY, datasets, xAxisLabel=xAxisLabel, yAxisLabel=yAxisLabel)
