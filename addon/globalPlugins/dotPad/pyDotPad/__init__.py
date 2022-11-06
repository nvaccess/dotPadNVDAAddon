# A part of the DotPad NVDA add-on.
# Copyright (C) 2022 NV Access Limited.
# this code is licensed under the GNU General Public License version 2.


import time
import threading
import os
from typing import Optional, Callable
import weakref
import sys
import os
import time
import ctypes
from . import dotPadSdk

DotPadErrorCode = dotPadSdk.DotPadErrorCode
DotPadError = dotPadSdk.DotPadError

class Singleton:

	_instanceRef  = None

	@classmethod
	def _getInstance(cls):
		if not cls._instanceRef:
			return None
		return cls._instanceRef()

	def _registerInstance(self):
		cls = type(self)
		if cls._getInstance():
			raise RuntimeError(f"Only one instance of {type(self).__name__} can exist at a time")
		cls._instanceRef = weakref.ref(self)

	def __init__(self):
		self._registerInstance()


class DotPad(Singleton):

	cellHeight: int = 4
	cellWidth: int = 2

	deviceSizes = {
		b'DotPad320A': (30,10, 20),
	}

	hCellCount: int 
	vCellCount: int
	bCellCount: int
	_initialized = False

	@classmethod
	def _displayCallback(cls):
		instance = cls._getInstance()
		if instance:
			instance._displayDoneEvent.set()

	def __init__(self, portNum: int, keyCallback: Optional[Callable[[int],None]]=None):
		super().__init__()
		self.keyCallback = keyCallback
		self._cDisplayCallback = dotPadSdk.DisplayCallbackType(self._displayCallback)
		dotPadSdk.registerDisplayCallback(self._cDisplayCallback)
		self._displayDoneEvent = threading.Event()
		self._displayDoneEvent.clear()
		oldCwd = os.getcwd()
		os.chdir(os.path.dirname(__file__))
		try:
			dotPadSdk.init(portNum)
		finally:
			os.chdir(oldCwd)
		self._initialized = True
		deviceName = self.deviceName
		try:
			self.hCellCount, self.vCellCount, self.bCellCount = self.deviceSizes[deviceName]
		except KeyError:
			raise RuntimeError(f"Unknown device {deviceName}")
		self.hPixelCount = self.hCellCount * self.cellWidth
		self.vPixelCount = self.vCellCount * self.cellHeight
		self.resetDataBuffer()
		if keyCallback is not None:
			self._cKeyCallback = dotPadSdk.KeyCallbackType(keyCallback)
			dotPadSdk.registerKeyCallback(self._cKeyCallback)
		print(f"deviceName: {self.deviceName}, hwVersion: {self.hwVersion}, fwVersion: {self.fwVersion}")

	@property
	def deviceName(self):
		return dotPadSdk.getDeviceName()

	@property
	def hwVersion(self):
		return dotPadSdk.getHwVersion()

	@property
	def fwVersion(self):
		return dotPadSdk.getFwVersion()

	def resetDataBuffer(self):
		self._data = ctypes.c_buffer(self.hCellCount * self.vCellCount)

	def setDotInDataBuffer(self, x: int, y: int):
		if x < 0 or x >= self.hPixelCount or y < 0 or y >= self.vPixelCount:
			return
		vCellIndex = int(y / self.cellHeight)
		hCellIndex = int(x / self.cellWidth)
		cellIndex = (vCellIndex * self.hCellCount) + hCellIndex
		bit = (y % self.cellHeight) + ((x % self.cellWidth) * self.cellHeight)
		self._data[cellIndex] = ord(self._data[cellIndex]) | 2**bit

	def outputDataBuffer(self) -> bool:
		self._displayDoneEvent.clear()
		dotPadSdk.displayData(self._data, self.hCellCount * self.vCellCount)
		self._displayDoneEvent.wait(5)

	def __del__(self):
		if self._initialized:
			for count in range(5):
				try:
					dotPadSdk.deinit()
				except DotPadError as e:
					if e.code is DotPadErrorCode.DISPLAY_IN_PROGRESS:
						time.sleep(1)
						continue
					elif e.code is DotPadErrorCode.DOT_PAD_COULD_NOT_INIT:
						return  # Now deinitialized or was never initialized
					raise
