import ctypes
import time
import wx
from .pyDotPad import DotPad320, DotPadError, DotPadErrorCode
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
import winGDI

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

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
			except DotPadError as e:
				gui.messageBox(f"{e.code.name}", "Error")
				self.portList.SetFocus()
				return
		else:
			self._globalPlugin.terminateDotPad()
			port = ""
		conf = config.conf[self._globalPlugin._configName]
		conf['port'] = port
		super().onOk(evt)

BLACKONWHITE = 1
WHITEONBLACK = 2
HALFTONE = 4

def captureImage(srcX, srcY, srcWidth, srcHeight, bufferWidth, bufferHeight, stretchMode=HALFTONE):
	# Get a device context for the screen
	screenDC = user32.GetDC(0)
	# Create a memory device context and load a new bitmap for drawing on
	memDC = gdi32.CreateCompatibleDC(screenDC)
	memBitmap = gdi32.CreateCompatibleBitmap(screenDC, bufferWidth, bufferHeight)
	gdi32.SelectObject(memDC, memBitmap)
	# Calculate a rectangle for the destination image that fits within the required bounds
	# But maintains the source aspect ratio
	srcAspectRatio = srcWidth / srcHeight
	bufferAspectRatio = bufferWidth / bufferHeight
	ratio = max(srcWidth / bufferWidth, srcHeight / bufferHeight)
	destWidth = int(srcWidth / ratio)
	destHeight = int(srcHeight / ratio)
	# Calculate the coordinates within the destination to place the image so that it will be centered
	destX = int((bufferWidth - destWidth) / 2)
	destY = int((bufferHeight - destHeight) / 2)
	# Copy the image at the requested coordinates from the screen into our bitmap
	# Appropriately resizing and positioning the image, using the requested stretch mode
	# E.g. keeping black pixels at the expense of white, for a black on white image
	gdi32.SetStretchBltMode(memDC, stretchMode)
	gdi32.StretchBlt(memDC, destX, destY, destWidth, destHeight, screenDC, srcX, srcY, srcWidth, srcHeight, winGDI.SRCCOPY)
	# Create a BitmapInfo struct defining the format of the pixels we would like to read from our bitmap.
	# I.e. Non-encoded RGB.
	bmInfo=winGDI.BITMAPINFO()
	bmInfo.bmiHeader.biSize = ctypes.sizeof(bmInfo)
	bmInfo.bmiHeader.biWidth = bufferWidth
	bmInfo.bmiHeader.biHeight = bufferHeight * -1
	bmInfo.bmiHeader.biPlanes = 1
	bmInfo.bmiHeader.biBitCount = 32
	bmInfo.bmiHeader.biCompression = winGDI.BI_RGB
	# Create a buffer to hold the image for returning.
	buffer = ((winGDI.RGBQUAD * bufferWidth) * bufferHeight)()
	# Copy the image from the bitmap into the buffer.
	gdi32.GetDIBits(memDC, memBitmap, 0, bufferHeight, buffer, ctypes.byref(bmInfo), winGDI.DIB_RGB_COLORS);
	# Return the buffer, plus the bounds of the image within
	return buffer, (destX, destY, destWidth, destHeight)

def findMeanBrightness(image, imageWidth, imageHeight, x, y, blur=1):
	surroundingPixels = []
	left = int(x - blur)
	right = int(x + blur + 1)
	top = int(y - blur)
	bottom = int(y + blur + 1)
	for i in range(top, bottom):
		for j in range(left, right):
			if i < 0 or i >= imageHeight or j < 0 or j >= imageWidth:
				surroundingPixels.append(0)
			else:
				surroundingPixels.append(rgbPixelBrightness(image[i][j]))
	threshold = sum(surroundingPixels) / len(surroundingPixels)
	return threshold

def rgbPixelBrightness(p):
	"""Converts a RGBQUAD pixel in to  one grey-scale brightness value."""
	return int((0.3*p.rgbBlue)+(0.59*p.rgbGreen)+(0.11*p.rgbRed))

class GlobalPlugin(globalPluginHandler.GlobalPlugin):

	_configName = 'addon_dotPad'
	_configSpec = {
		'port': 'string(default="")',
	}

	def __init__(self):
		super().__init__()
		config.conf.spec[self._configName] = self._configSpec
		self._dp = None

	def terminateDotPad(self):
		self._dp = None

	def initDotPad(self, port, wait=False):
		portNum = int(port[3:])
		if self._dp:
			self.terminateDotPad()
		self._dp = DotPad320(portNum)
		if wait:
			time.sleep(3)
		return self._dp

	def ensureDotPad(self):
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
		except DotPadError as e:
			wx.CallAfter(gui.messageBox,f"{e.code.name}", "DotPad Error")
			return None
		return self._dp

	def showNavigatorObject(self, isWhiteOnBlack=False):
		dp = self.ensureDotPad()
		if not dp:
			return
		location = api.getNavigatorObject().location
		stretchMode = WHITEONBLACK if isWhiteOnBlack else BLACKONWHITE
		image, (left, top, width, height) = captureImage(location.left, location.top, location.width, location.height, dp.hPixelCount, dp.vPixelCount, stretchMode=stretchMode)
		dp.resetDataBuffer()
		for y in range(dp.vPixelCount):
			if y < top or y >= (top + height):
				continue
			for x in range(dp.hPixelCount):
				if x < left or x >= (left + width):
					continue
				threshold = findMeanBrightness(image, dp.hPixelCount, dp.vPixelCount, x, y, blur=4)
				pixel = rgbPixelBrightness(image[y][x])
				isWhite = pixel >= threshold
				isRaised = isWhite if isWhiteOnBlack else not isWhite
				if isRaised:
					dp.setDotInDataBuffer(x, y)
		try:
			dp.outputDataBuffer()
		except DotPadError as e:
			if e.code == DotPadErrorCode.DISPLAY_IN_PROGRESS:
				tones.beep(220,50)
				ui.message("Dot pad busy")
			else:
				wx.CallAfter(gui.messageBox,f"{e.code.name}", "DotPad Error")
			return
		ui.message("Displaying on DotPad")
		tones.beep(440, 50)
		core.callLater(1000, tones.beep, 660, 50)
		core.callLater(2000, tones.beep, 880, 50)

	@script(gesture="kb:NVDA+f8")
	def script_shownavigatorObject_blackOnWhite(self, gesture):
		self.showNavigatorObject()

	@script(gesture="kb:shift+NVDA+f8")
	def script_shownavigatorObject_whiteOnBlack(self, gesture):
		self.showNavigatorObject(isWhiteOnBlack=True)

	@script(gesture="kb:control+NVDA+f8")
	def script_showSettings(self, gesture):
		wx.CallAfter(gui.mainFrame._popupSettingsDialog,DotPadDialog,self)
