# A part of the DotPad NVDA add-on.
# A part of the DotPad NVDA add-on.
# Copyright (C) 2022 NV Access Limited.
# this code is licensed under the GNU General Public License version 2.


from typing import List, Optional
from .brailleUtils import (
	drawBrailleCells,
	translateTextToBraille,
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

def drawDiscreteDataset(func_drawDot, destX: int, destY: int, destWidth: int, destHeight: int, minY: float, maxY: float, values: List[float], space: int=1):
	yRange = (maxY - minY)
	yScale = destHeight / yRange
	transposeValuesInDataset(values, minY * -1)
	scaleValuesInDataset(values, yScale)
	flipValuesInDataset(values, destHeight)
	colWidth = int(destWidth / len(values))
	lastY = None
	for index in range(len(values)):
		x = destX + (index * colWidth)
		y = int(values[index])
		func_drawDot(x, y)
		for subY in range(y + 1, destHeight):
			drawLine(func_drawDot, x, subY, 2, vertical=False)

def drawHorizontalRuler(func_drawDot, x: int, y: int, labels: List[str], spacing: int):
	deltaX = 0
	deltaY = 0
	drawLine(func_drawDot, x, y, (len(labels) * spacing) + 1, vertical=False)
	deltaY += 2
	for label in labels:
		cells = translateTextToBraille(label, brailleTable='en-us-comp8.ctb')
		drawBrailleCells(func_drawDot, x + deltaX, y + deltaY, cells)
		deltaX += spacing

def drawVerticalRuler(func_drawDot, x: int, y: int, labels: List[str], spacing: int):
	deltaX = 0
	deltaY = 0 
	labels.reverse()
	for label in labels:
		cells = translateTextToBraille(label, brailleTable='en-us-comp8.ctb')
		deltaX = max(deltaX, len(cells) *3)
		drawBrailleCells(func_drawDot, x, y + deltaY, cells)
		deltaY += spacing
		func_drawDot(x + deltaX, (y + deltaY - 1))
	deltaX += 1
	drawLine(func_drawDot, x + deltaX, y, (len(labels) * spacing), vertical=True)
	return deltaX + 1

def drawLine(func_drawDot, x: int, y: int, length: int, vertical=False):
	for index in range(length):
		if vertical:
			func_drawDot(x, y + index)
		else:
			func_drawDot(x + index, y)

def generateYValueLabels(minY: float, maxY: float, yCount: int) -> List[str]:
	yRange = maxY - minY
	yStep = yRange / yCount
	yLabels = [format(minY + (yStep * index),'g') for index in range(yCount)]
	yLabels = [label.replace(".", "'") for label in yLabels]
	maxYLabelLen = max(len(label) for label in yLabels)
	yLabels = [label.rjust(maxYLabelLen) for label in yLabels]
	return yLabels

def generateDefaultXLabels(count: int) -> List[str]:
	return [chr(x + 97) for x in range(count)]

def drawViewport(func_drawDot, x: int, y: int, width: int, height: int, minY: float, maxY: float, xCount: int=0, xLabels: Optional[List[str]]=None, yCount: int=0, lockAspect=False, left=True, bottom=True, hGridlines=False, vGridlines=False):
	if xLabels:
		if not xCount:
			xCount = len(xLabels)
		elif len(xLabels) != xCount:
			raise ValueError("xLabels length is not xCount")
	x += 1
	innerX = x
	innerY = y
	innerWidth = width
	innerHeight = height
	innerWidth -= 1
	if bottom:
		innerHeight -= 5
	vSpacing = 3
	maxYCount = 10
	if yCount is 0:
		yCount = maxYCount
	else:
		yCount = min(yCount, maxYCount)
		vSpacing = int(innerHeight / yCount)
		assert vSpacing >= 3
	if left:
		yLabels = generateYValueLabels(minY, maxY, yCount)
		rulerWidth = drawVerticalRuler(func_drawDot, x, innerY, yLabels, vSpacing)
		innerX += rulerWidth
		innerWidth -= rulerWidth
	hSpacing = 3
	maxXCount = int(innerWidth / hSpacing)
	if xCount is 0:
		xCount = maxXCount
	else:
		xCount = min(xCount, maxXCount)
		hSpacing = int(innerWidth / xCount)
		assert hSpacing >= 3
	innerWidth -= innerWidth % xCount
	innerHeight -= innerHeight % yCount
	if lockAspect:
		hSpacing = vSpacing
		innerWidth = xCount * hSpacing
	if bottom:
		if xLabels:
			# We can only show the first letter
			xLabels = [label[0].lower() for label in xLabels]
		else:
			xLabels = generateDefaultXLabels(xCount)
		drawHorizontalRuler(func_drawDot, innerX, (innerY + innerHeight) - 1, xLabels, hSpacing)
	if vGridlines:
		for deltaX in range(1, xCount + 1):
			drawLine(func_drawDot, innerX + (deltaX * hSpacing) - 1, innerY, innerHeight, vertical=True)
	if hGridlines:
		for deltaY in range(1, yCount):
			drawLine(func_drawDot, innerX, (innerY + (deltaY * vSpacing)) - 1, innerWidth + 2, vertical=False)
	return (innerX, innerY, innerWidth, innerHeight, xCount, yCount)
