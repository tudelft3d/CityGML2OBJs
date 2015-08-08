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

import matplotlib as mpl
import matplotlib.pyplot as plt

#-- Resource: http://matplotlib.org/examples/api/colorbar_only.html
plt.rc('text', usetex=True)
plt.rc('font', family='serif')
#-- Make a figure and axes with dimensions as desired
fig = plt.figure(figsize=(8,1))
ax1 = fig.add_axes([0.05, 0.80, 0.9, 0.15])

#-- Bounds
vmin = 350
vmax = 1300

#-- Colormap
cmap = mpl.cm.afmhot
norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)

cb1 = mpl.colorbar.ColorbarBase(ax1, cmap=cmap,
                                   norm=norm,
                                   orientation='horizontal')

#-- Label on the axis
cb1.set_label(r"Annual solar irradiation [kWh/m$^{2}$/year]")


cmap = mpl.colors.ListedColormap(['r', 'g', 'b', 'c'])
cmap.set_over('0.25')
cmap.set_under('0.75')

bounds = [1, 2, 4, 7, 8]
norm = mpl.colors.BoundaryNorm(bounds, cmap.N)

#-- Change the last tick label
labels = [item.get_text() for item in cb1.ax.get_xticklabels()]
li = 0
for l in labels:
	# labels[li] = r"$"+str(l)+"$"
	labels[li] = r""+str(l)
	li += 1
labels[-1] = r"$\geq "+str(vmax) + "$"
cb1.ax.set_xticklabels(labels)

#-- Output
plt.savefig('colorbar.pdf', transparent=True)
plt.savefig('colorbar.png', dpi=600, transparent=True)
plt.show()