import ctypes
from .pyDotPad import DotPad320, DotPadError, DotPadErrorCode
import globalPluginHandler
from scriptHandler import script
import ui
import api
import gui
import winGDI

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

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

	def __init__(self):
		super().__init__()

	def getDotPad(self):
		if not hasattr(self, '_dp'):
			self._dp = DotPad320(3)
		return self._dp

	def showNavigatorObject(self, isWhiteOnBlack=False):
		try:
			dp = self.getDotPad()
		except DotPadError as e:
			import tones; tones.beep(550,50)
			ui.message(f"DotPad error: {e.code.name}")
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
				threshold = findMeanBrightness(image, dp.hPixelCount, dp.vPixelCount, x, y, blur=3)
				pixel = rgbPixelBrightness(image[y][x])
				isWhite = pixel >= threshold
				isRaised = isWhite if isWhiteOnBlack else not isWhite
				if isRaised:
					dp.setDotInDataBuffer(x, y)
		try:
			dp.outputDataBuffer()
		except DotPadError as e:
			import tones; tones.beep(550,50)
			if e.code == DotPadErrorCode.DISPLAY_IN_PROGRESS:
				ui.message("Dot pad busy")
			else:
				ui.message(f"DotPad error: {e.code.name}")

	@script(gesture="kb:NVDA+f8")
	def script_shownavigatorObject_blackOnWhite(self, gesture):
		self.showNavigatorObject()

	@script(gesture="kb:shift+NVDA+f8")
	def script_shownavigatorObject_whiteOnBlack(self, gesture):
		self.showNavigatorObject(isWhiteOnBlack=True)
