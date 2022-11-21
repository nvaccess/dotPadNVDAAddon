# A part of the DotPad NVDA add-on.
# A part of the DotPad NVDA add-on.
# Copyright (C) 2022 NV Access Limited.
# this code is licensed under the GNU General Public License version 2.


from typing import List, Tuple, Optional, Dict
import math
from .brailleUtils import (
	drawBrailleCells,
	translateTextToBraille,
	brailleCellWidth
)


def transposeValuesInDataset(values: List[float], amount: float) -> None:
	for index in range(len(values)):
		values[index] += amount

def scaleValuesInDataset(values: List[float], amount: float) -> None:
	for index in range(len(values)):
		values[index] *= amount

def flipValuesInDataset(values: List[float], maxVal: float) -> None:
	for index in range(len(values)):
		values[index] = maxVal - values[index]

def resizeDataset(values: List[float], newSize: int) -> None:
	scale = newSize / len(values)
	lastNewIndex = 0
	lastNewVal = values[0]
	oldSize = len(values)
	for oldIndex in range(1, oldSize):
		newIndex = int(oldIndex * scale)
		oldIndex = (0 - oldSize) + oldIndex
		if scale < 1:
				if newIndex == lastNewIndex:
					values[newIndex] = (values[oldIndex - 1] + values[oldIndex]) / 2
					del values[oldIndex]
		elif scale > 1:
			newVal = values[oldIndex]
			newIndexDelta = newIndex - lastNewIndex
			valDelta = newVal - lastNewVal
			subValues = []
			for subNewIndex in range(1, newIndexDelta):
				subNewVal = lastNewVal + (valDelta * (subNewIndex / newIndexDelta))
				subValues.append(subNewVal)
			subValues.append(newVal)
			values[oldIndex:oldIndex + 1] = subValues
			lastNewVal = newVal
		lastNewIndex = newIndex

def drawContinuousDataset(func_drawDot, destX: int, destY: int, destWidth: int, destHeight: int, minY: float, maxY: float, values: List[float], fillBelowCurve=False):
	if fillBelowCurve:
		origfunc_drawDot = func_drawDot
		func_drawDot = lambda x, y: drawLine(origfunc_drawDot,x, y, destHeight - y, vertical=True)
	yRange = (maxY - minY)
	yScale = destHeight / yRange
	resizeDataset(values, destWidth)
	transposeValuesInDataset(values, minY * -1)
	scaleValuesInDataset(values, yScale)
	flipValuesInDataset(values, destHeight - 1)
	lastY = None
	for x, y in enumerate(values):
		x += destX
		y += destY
		y = int(round(y))
		if lastY is not None:
			for subY in range(min(lastY, y), max(lastY, y)):
				if subY == lastY:
					continue
				func_drawDot(x, int(subY))
		func_drawDot(x, int(y))
		lastY = y

def drawDiscreteDataset(func_drawDot, destX: int, destY: int, destWidth: int, destHeight: int, minY: float, maxY: float, values: List[float], barWidth: int, colWidth: int):
	yRange = (maxY - minY)
	yScale = destHeight / yRange
	transposeValuesInDataset(values, minY * -1)
	scaleValuesInDataset(values, yScale)
	flipValuesInDataset(values, destHeight)
	lastY = None
	for index in range(len(values)):
		x = destX + (index * colWidth)
		y = destY + int(values[index])
		for subY in range(y, destHeight):
			drawLine(func_drawDot, x, subY, barWidth, vertical=False)

def drawHorizontalRuler(func_drawDot, x: int, y: int, colStartOffset: int, colEndOffset: int, spacing: int):
	labels = generateAZColumnLabels(colStartOffset, colEndOffset)
	deltaX = 0
	deltaY = 0
	drawLine(func_drawDot, x, y, (len(labels) * spacing) + 1, vertical=False)
	deltaX +=2 
	deltaY += 2
	for label in labels:
		cells = translateTextToBraille(label, brailleTable='en-us-comp8.ctb')
		drawBrailleCells(func_drawDot, x + deltaX, y + deltaY, cells)
		deltaX += spacing
	return deltaX, deltaY + 3

def drawVerticalRuler(func_drawDot, x: int, y: int, minY: int, maxY: int, yCount: int, spacing: int=3):
	labels = generateYValueLabels(minY, maxY, yCount)
	deltaX = 0
	deltaY = 0 
	labels.reverse()
	for label in labels:
		cells = translateTextToBraille(label, brailleTable='en-us-comp8.ctb')
		deltaX = max(deltaX, len(cells) * brailleCellWidth)
		drawBrailleCells(func_drawDot, x, y + deltaY + 1, cells)
		deltaY += spacing
		func_drawDot(x + deltaX, (y + deltaY - 1))
	deltaX += 1
	drawLine(func_drawDot, x + deltaX, y, (len(labels) * spacing), vertical=True)
	return deltaX + 1, deltaY - 1

def drawLine(func_drawDot, x: int, y: int, length: int, vertical=False):
	for index in range(length):
		if vertical:
			func_drawDot(x, y + index)
		else:
			func_drawDot(x + index, y)

def generateYValueLabels(minY: float, maxY: float, yCount: int) -> List[str]:
	yRange = maxY - minY
	yStep = yRange / yCount
	yValues = [minY + (yStep * index) for index in range(yCount)]
	# Calculate the maximum amount of decimal places needed
	maxDecimalPlaces = max(
		len(format(x, 'g').partition('.')[2]) for x in yValues
	)
	maxDecimalPlaces = min(maxDecimalPlaces, 1)
	formatSpec = f".{maxDecimalPlaces}f"
	yLabels = [format(val,formatSpec) for val in yValues]
	# Right-justify all the values
	maxYLabelLen = max(len(label) for label in yLabels)
	yLabels = [label.rjust(maxYLabelLen) for label in yLabels]
	# Change the decimal point (dot) into a tick as that takes up less space in Braille 
	yLabels = [label.replace(".", "'") for label in yLabels]
	return yLabels

def generateAZColumnLabel(colNum: int):
	charList = []
	while True:
		div, remainder = divmod(colNum, 26)
		ch = chr(97 + remainder)
		charList.insert(0, ch)
		if div == 0: 
			break
		colNum = div - 1
	return "".join(charList)

def generateAZColumnLabels(start: int, end: int) -> List[str]:
	return [generateAZColumnLabel(x) for x in range(start, end)]


class DotBuffer:

	width: int
	height: int
	dots: List[Tuple[int,int]]

	def __init__(self):
		self.dots = []
		self.width = 0
		self.height = 0

	def setDot(self, x, y):
		self.dots.append((x, y))
		if self.width <= x:
			self.width = x + 1
		if self.height <= y:
			self.height = y + 1

	def draw(self, func_drawDot):
		for x, y in self.dots:
			func_drawDot(x, y)


class cached_property(property):

	def __get__(self, inst, owner):
		name = self.fget.__name__
		if name in inst.__dict__:
			return inst.__dict__[name]
		val = super().__get__(inst, owner)
		inst.__dict__[name] = val
		return val


class Chart:

	rowHeight = 4
	minColWidth = 4
	colStartOffset = 0

	@cached_property
	def numTotalCols(self):
		return len(list(self.datasets.values())[0])

	@cached_property
	def colEndOffset(self):
		return self.numTotalCols

	@cached_property
	def plotHeight(self):
		if self.showHorizontalRuler:
			return self.destHeight - self.rowHeight
		else:
			return self.destHeight

	plotY = 0

	@cached_property
	def plotX(self):
		if self.showVerticalRuler:
			return self.verticalRuler.width
		else:
			return 0

	@cached_property
	def plotWidth(self):
		return self.destWidth - self.plotX

	@cached_property
	def colWidth(self):
		numDatasets = len(self.datasets)
		minColWidth = self.minColWidth
		totalPlotWidth = minColWidth * self.numTotalCols
		if totalPlotWidth < self.plotWidth:
			colWidth = self.plotWidth // self.numTotalCols
		else:
			colWidth = minColWidth
		return colWidth

	@cached_property
	def valStep(self):
		return self.plotHeight // self.rowHeight

	@cached_property
	def normalizedMinVal(self):
		return self.minVal

	@cached_property
	def normalizedMaxVal(self):
		# if not already, increases maxVal until the range is a multiple of valStep
		valRange = self.maxVal - self.minVal
		valStep = self.valStep
		valRangeModStep = valRange % valStep
		if valRangeModStep > 0:
			valRange += (valStep - (valRangeModStep))
			maxVal = self.minVal + valRange
			return maxVal
		return self.maxVal

	def __init__(self, destWidth: int, destHeight: int, minVal: float, maxVal: float, datasets: Dict[str,List[float]], showVerticalRuler=True, showHorizontalRuler=True):
		self.showVerticalRuler = showVerticalRuler
		self.showHorizontalRuler = showHorizontalRuler
		self.datasets = datasets
		self.destWidth = destWidth
		self.destHeight = destHeight
		self.minVal = minVal
		self.maxVal = maxVal

	@cached_property
	def verticalRuler(self):
		ruler = DotBuffer()
		ruler.width, ruler.height = drawVerticalRuler(ruler.setDot, 0, 0, self.normalizedMinVal, self.normalizedMaxVal, self.valStep, self.rowHeight)
		return ruler

	def draw(self, func_drawDot):
		if self.showVerticalRuler:
			self.verticalRuler.draw(func_drawDot)
		if self.showHorizontalRuler:
			drawHorizontalRuler(func_drawDot, self.plotX, (self.plotY + self.plotHeight) - 1, self.colStartOffset, self.colEndOffset, self.colWidth)
		self.drawPlot(func_drawDot)


class ScrollableChart(Chart):

	@cached_property
	def minColWidth(self):
		minColWidth = super().minColWidth
		if self.showHorizontalRuler:
			largestLabel = generateAZColumnLabel(self.numTotalCols - 1)
			labelColWidth = (len(largestLabel) * brailleCellWidth) + len(largestLabel)
			minColWidth = max(minColWidth, labelColWidth)
		return minColWidth

	@cached_property
	def maxVisibleCols(self):
		return self.plotWidth // self.colWidth

	@property
	def colEndOffset(self):
		return min(self.colStartOffset + self.maxVisibleCols, self.numTotalCols)

	def scrollForward(self):
		if self.colEndOffset == self.numTotalCols:
			return False
		for x in range(self.maxVisibleCols):
			self.colStartOffset += 1
			if self.colEndOffset == self.numTotalCols:
				break
		return True

	def scrollBack(self):
		if self.colStartOffset == 0:
			return False
		for x in range(self.maxVisibleCols):
			self.colStartOffset -= 1
			if self.colStartOffset == 0:
				break
		return True


class BarChart(ScrollableChart):

	barWidth = 2
	barGap = 1

	@cached_property
	def colGap(self):
		numDatasets = len(self.datasets)
		if numDatasets > 1:
			return 2
		else:
			return 1

	@cached_property
	def minColWidth(self):
		numDatasets = len(self.datasets)
		minColWidth = super().minColWidth
		minColWidthWithBars = ((self.barWidth + self.barGap) * numDatasets) + self.colGap
		minColWidth = max(minColWidth, minColWidthWithBars)
		return minColWidth

	def drawPlot(self, func_drawDot):
		for index, dataset in enumerate(self.datasets.values()):
			xOffset = 2 + (self.barWidth + self.barGap) * index
			drawDiscreteDataset(func_drawDot, self.plotX + xOffset, self.plotY, self.plotWidth, self.plotHeight, self.normalizedMinVal, self.normalizedMaxVal, dataset[self.colStartOffset:self.colEndOffset], self.barWidth, self.colWidth)


class LineChart(Chart):

	def drawPlot(self, func_drawDot):
		for index, dataset in enumerate(self.datasets.values()):
			drawContinuousDataset(func_drawDot, self.plotX, self.plotY, self.plotWidth, self.plotHeight, self.normalizedMinVal, self.normalizedMaxVal, dataset)
