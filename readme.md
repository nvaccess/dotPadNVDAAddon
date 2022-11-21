# DotPad NVDA Add-on

This prototype add-on for NVDA adds support for the DotPad tactile graphical display from Dot Inc.
Currently this add-on supports displaying the screen image at the NVDA navigator object, and also displaying charts in Excel.

# Copyright and License
This add-on is copyright (C) 2022 NV Access Limited.
This add-on is licensed under the GNU General Public License version 2.

## Key Commands
* control+NVDA+f8: Open DotPad settings. Allows you to tell NVDA which COM port the DotPad is connected to.
* NVDA+f8: Displays the black on white image at the NVDA navigator object.
* shift+NvDA+f8: displays the white on black image at the NVDA navigator object.
* NVDA+f6: when focused on a chart in Excel, displays the chart on the Dotpad, after asking the user for some chart preferences fia a dialog box.

## Tutorial
1. Start NVDA.
2. Install this add-on, restarting NVDA.
3. Open the DotPad settings with control+NVDA+f8, choose the appropriate COM port and press OK.
4. Visit https://www.nvaccess.org/ in a web browser.
5. Move to the 'Home' link on the navbar.
6. Press NVDA+f8 to display the link on the DotPad. After a few seconds you should be able to feel the printed word 'Home'.
7. On the same page, move to the Google logo graphic.
8. Press NVDA+f8 to display the Google logo on the DotPad. After a few seconds you should be able to feel the Google logo.
9. Press Windows+m to minimise all Windows and focus the Desktop.
10. Highlight a Desktop icon of your choice E.g. Zoom
11. Press shift+NVDA+f8 to display the icon on the DotPad. Note that we use shift+NVDA+f8 (white on black) here as most icons are generally light image/text on a dark background. After a few seconds you should be able to feel the icon on the DotPad.
12. Open Excel and focus a chart.
13. Press NVDA+f6 to present the Dotpad Chart dialog. Choose your desired settings, such as chart type (bar or line), which rulers to show, and which datasets to include, and press okay for the chart to be displayed on the Dotpad.

## Image processing details
When the add-on captures a part of the screen, it resizes the image to fit on the DotPad, ensuring the aspect ratio of the original image is maintained.
If the image is expected to be black on white, it tries to keep black pixels at the expense of white pixels, and the opposite for white on black. this ensures that thin lines are not removed when shrinking. 
As the dotpad can only show a monochrome image (I.e. raised dots for white, no dots for black), a suitable threshold must be found to choose how bright something should be to be classed as white. this add-on currently uses a very basic local mean threshold approach where by the average brightness is calculated for  a  block of 7 by 7  pixels around the pixel in question, and then this value is used as the threshold. this approach ensures that changes can be shown even if lighting changes across the image.

## Chart details
this add-on can present Excel charts on the Dotpad.
Charts are displayed with an optional vertical ruler on the left with values going up, an optional horizontal ruler across the bottom with column letter labels starting at 'a', and a plot area that can show the data either as bars or as a trend line.
### Bar charts
 Bar charts show their data as solid columns, each column being the height of its respective value. 
If the chart is showing more than one series of data at once, then columns from each series are grouped closely together next to eachother.
Some charts may be too wide to fit on the Dotpad display. It is possible to scroll forward or back with the Dotpad buttons to see more of the chart.
### Line charts
A line chart shows one continuous line that represents the trend of the chart. Line charts are made to fit entirely within the Dotpad display allowing the user to view the full trend without having to scroll.
 