# A part of the DotPad NVDA add-on.
# Copyright (C) 2022 NV Access Limited.
# this code is licensed under the GNU General Public License version 2.

import os
import louis
import louisHelper
import brailleTables
import config

brailleCellWidth = 3

dot1 = 1
dot2 = 2
dot3 = 4
dot4 = 8
dot5 = 16
dot6 = 32
dot7 = 64
dot8 = 128


brailleDotCoords = [
	# dot1
	(0, 0),
	# dot2
	(0, 1),
	# dot3
	(0, 2),
	# dot4
	(1, 0),
	# dot5
	(1, 1),
	# dot6
	(1, 2),
	# dot7
	(0, 3),
	# dot8
	(1, 3),
]


def drawBrailleCells(drawFunc, x, y, cells):
	for cell in cells:
		for dot in range(0, 8):
			if 1 << dot & cell:
				dotX, dotY = brailleDotCoords[dot]
				drawFunc(x + dotX, y + dotY)
		x += 3


def translateTextToBraille(text, brailleTable=None):
	if not brailleTable:
		brailleTable = config.conf["braille"]["translationTable"]
	return louisHelper.translate(
		[os.path.join(brailleTables.TABLES_DIR, brailleTable), "braille-patterns.cti"],
		text,
		mode=louis.dotsIO
	)[0]
