# A part of the DotPad NVDA add-on.
# Copyright (C) 2022 NV Access Limited.
# this code is licensed under the GNU General Public License version 2.


from enum import IntEnum
import ctypes
import winGDI


user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32


class StretchMode(IntEnum):
	BLACKONWHITE = 1
	WHITEONBLACK = 2
	HALFTONE = 4

def captureImage(srcX: int, srcY: int, srcWidth: int, srcHeight: int, bufferWidth: int, bufferHeight: int, stretchMode: StretchMode=StretchMode.HALFTONE) -> ctypes.Array:
	"""
	Captures an image from a part of the screen, resizing to fit the required size, while still maintaining the original aspect ratio.
	"""
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


def findMeanBrightnessThreshold(image: ctypes.Array, x: int, y: int, blur: int=1):
	"""
	Calculates a suitable brightness threshold at which a pixel could be considered white in a monochrome image, using the mean brightness of the surrounding pixels.
	"""
	imageHeight = len(image)
	imageWidth = len(image[0])
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

def getMonochromePixelUsingLocalBrightnessThreshold(image, x, y, blur=4):
	"""
	Fetches a monochrome pixel from an RGB image, using the local mean brightness to calculate a suitable brightness threshold.
	"""
	threshold = findMeanBrightnessThreshold(image, x, y, blur)
	px = rgbPixelBrightness(image[y][x])
	return px >= threshold
