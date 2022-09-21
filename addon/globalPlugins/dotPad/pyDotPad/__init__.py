import sys
import os
import time
import ctypes
from . import dotPadSdk

DotPadErrorCode = dotPadSdk.DotPadErrorCode

class DotPadError(Exception):
	def __init__(self, code: DotPadErrorCode):
		self.code = code

class DotPad320:

	cellHeight = 4
	cellWidth = 2
	hCellCount = 30
	vCellCount = 10
	writeDelay = 3

	def __init__(self, portNum: int):
		self.cellCount = self.vCellCount * self.hCellCount
		self.hPixelCount = self.hCellCount * self.cellWidth
		self.vPixelCount = self.vCellCount * self.cellHeight
		self.resetDataBuffer()
		res = dotPadSdk.init(portNum)
		if res != DotPadErrorCode.NONE:
			raise DotPadError(res)
		time.sleep(3)

	def resetDataBuffer(self):
		self._data = ctypes.c_buffer(self.cellCount)

	def setDotInDataBuffer(self, x: int, y: int):
		vCellIndex = int(y / self.cellHeight)
		hCellIndex = int(x / self.cellWidth)
		cellIndex = (vCellIndex * self.hCellCount) + hCellIndex
		bit = (y % self.cellHeight) + ((x % self.cellWidth) * self.cellHeight)
		self._data[cellIndex] = ord(self._data[cellIndex]) | 2**bit

	def outputDataBuffer(self) -> bool:
		res = dotPadSdk.display_data(self._data, self.cellCount)
		if res != DotPadErrorCode.NONE:
			raise DotPadError(res)

	def __del__(self):
		dotPadSdk.deinit()
