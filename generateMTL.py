#!/usr/bin/python
# -*- coding: utf-8 -*-

# The MIT License (MIT)

# This code is part of the CityGML2OBJs package

# Copyright (c) 2014 
# Filip Biljecki
# Delft University of Technology
# fbiljecki@gmail.com

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import numpy as np
import matplotlib.cm as cm

#-- Number of classes of the colormap
no_values = 101

#-- Select the colormap and get its RGB values for each of the classes
colormap = cm.get_cmap("afmhot", no_values) # http://matplotlib.org/examples/color/colormaps_reference.html
colormap_vals = colormap(np.arange(no_values)).tolist()

#-- This is the MTL file
mtlcontents = ""

#-- Class by class... MTL!
for i in range(0, no_values):
	b = float(i)/100
	mtlcontents += "newmtl " + str(b) + "\n"
	mtlcontents += "Ka " + str(colormap_vals[i][0]) + " " + str(colormap_vals[i][1]) + " " + str(colormap_vals[i][2]) + "\n"
	mtlcontents += "Kd " + str(colormap_vals[i][0]) + " " + str(colormap_vals[i][1]) + " " + str(colormap_vals[i][2]) + "\n"
#-- Write the MTL
with open("colormap.mtl", "w") as mtl_file:
                mtl_file.write(mtlcontents)