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

import math
import markup3dmodule
from lxml import etree
import copy
import triangle
import numpy as np

def getAreaOfGML(poly, height=True):
    """Function which reads <gml:Polygon> and returns its area.
    The function also accounts for the interior and checks for the validity of the polygon."""
    exteriorarea = 0.0
    interiorarea = 0.0
    #-- Decompose the exterior and interior boundary
    e, i = markup3dmodule.polydecomposer(poly)
    #-- Extract points in the <gml:LinearRing> of <gml:exterior>
    epoints =  markup3dmodule.GMLpoints(e[0])
    if isPolyValid(epoints):
        if height:
            exteriorarea += get3DArea(epoints)
        else:
            exteriorarea += get2DArea(epoints)
    for idx, iring in enumerate(i):
        #-- Extract points in the <gml:LinearRing> of <gml:interior>
        ipoints = markup3dmodule.GMLpoints(iring)
        if isPolyValid(ipoints):
            if height:
                interiorarea += get3DArea(ipoints)
            else:
                interiorarea += get2DArea(ipoints)
    #-- Account for the interior
    area = exteriorarea - interiorarea
    #-- Area in dimensionless units (coordinate units)
    return area

#-- Validity of a polygon ---------
def isPolyValid(polypoints, output=True):
    """Checks if a polygon is valid. Second option is to supress output."""
    #-- Number of points of the polygon (including the doubled first/last point)
    npolypoints = len(polypoints)
    #-- Assume that it is valid, and try to disprove the assumption
    valid = True
    #-- Check if last point equal
    if polypoints[0] != polypoints[-1]:
        if output:
            print "A degenerate polygon. First and last points do not match."
        valid = False
    #-- Check if it has at least three points
    if npolypoints < 4: #-- Four because the first point is doubled as the last one in the ring
        if output:
            print "A degenerate polygon. The number of points is smaller than 3."
        valid = False
    #-- Check if the points are planar
    if not isPolyPlanar(polypoints):
        if output:
            print "A degenerate polygon. The points are not planar."
        valid = False
    #-- Check if the polygon does not have self-intersections
    #-- Disabled, something doesn't work here, will work on this later.
    #if not isPolySimple(polypoints):
    #    print "A degenerate polygon. The edges are intersecting."
    #    valid = False
    return valid


def isPolyPlanar(polypoints):
    """Checks if a polygon is planar."""
    #-- Normal of the polygon from the first three points
    normal = unit_normal(polypoints[0], polypoints[1], polypoints[2])
    #-- Number of points
    npolypoints = len(polypoints)
    #-- Tolerance
    eps = 0.01
    #-- Assumes planarity
    planar = True
    for i in range (3, npolypoints):
        vector = [polypoints[i][0] - polypoints[0][0], polypoints[i][1] - polypoints[0][1], polypoints[i][2] - polypoints[0][2]]
        if math.fabs(dot(vector, normal)) > eps:
            planar = False
    return planar

def isPolySimple(polypoints):
    """Checks if the polygon is simple, i.e. it does not have any self-intersections.
    Inspired by http://www.win.tue.nl/~vanwijk/2IV60/2IV60_exercise_3_answers.pdf"""
    npolypoints = len(polypoints)
    #-- Check if the polygon is vertical, i.e. a projection cannot be made.
    #-- First copy the list so the originals are not modified
    temppolypoints = copy.deepcopy(polypoints)
    newpolypoints = copy.deepcopy(temppolypoints)
    #-- If the polygon is vertical
    if math.fabs(unit_normal(temppolypoints[0], temppolypoints[1], temppolypoints[2])[2]) < 10e-6:
        vertical = True
    else:
        vertical = False
    #-- We want to project the vertical polygon to the XZ plane
    #-- If a polygon is parallel with the YZ plane that will not be possible
    YZ = True
    for i in range(1, npolypoints):
        if temppolypoints[i][0] != temppolypoints[0][0]:
            YZ = False
            continue
    #-- Project the plane in the special case
    if YZ:
        for i in range(0, npolypoints):
            newpolypoints[i][0] = temppolypoints[i][1]
            newpolypoints[i][1] = temppolypoints[i][2]
    #-- Project the plane
    elif vertical:
        for i in range(0, npolypoints):
            newpolypoints[i][1] = temppolypoints[i][2]
    else:
        pass #-- No changes here
    #-- Check for the self-intersection edge by edge
    for i in range(0, npolypoints-3):
        if i == 0:
            m = npolypoints - 3
        else:
            m = npolypoints - 2
        for j in range (i + 2, m):
            if intersection(newpolypoints[i], newpolypoints[i+1], newpolypoints[j%npolypoints], newpolypoints[(j+1)%npolypoints]):
                return False
    return True

def intersection(p, q, r, s):
    """Check if two line segments (pq and rs) intersect. Computation is in 2D.
    Inspired by http://www.win.tue.nl/~vanwijk/2IV60/2IV60_exercise_3_answers.pdf"""

    eps = 10e-6

    V = [q[0] - p[0], q[1] - p[1]]
    W = [r[0] - s[0], r[1] - s[1]]

    d = V[0]*W[1] - W[0]*V[1]

    if math.fabs(d) < eps:
        return False
    else:
        return True
#------------------------------------------


#-- Area and other handy computations
def det(a):
    """Determinant of matrix a."""
    return a[0][0]*a[1][1]*a[2][2] + a[0][1]*a[1][2]*a[2][0] + a[0][2]*a[1][0]*a[2][1] - a[0][2]*a[1][1]*a[2][0] - a[0][1]*a[1][0]*a[2][2] - a[0][0]*a[1][2]*a[2][1]

def unit_normal(a, b, c):
    """Unit normal vector of plane defined by points a, b, and c."""
    x = det([[1,a[1],a[2]],
             [1,b[1],b[2]],
             [1,c[1],c[2]]])
    y = det([[a[0],1,a[2]],
             [b[0],1,b[2]],
             [c[0],1,c[2]]])
    z = det([[a[0],a[1],1],
             [b[0],b[1],1],
             [c[0],c[1],1]])
    magnitude = (x**2 + y**2 + z**2)**.5
    if magnitude == 0.0:
        raise SyntaxWarning("The normal of the polygon has no magnitude. Check the polygon. The most common cause for this are two identical and sequential points.")
    return (x/magnitude, y/magnitude, z/magnitude)

def dot(a, b):
    """Dot product of vectors a and b."""
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2]

def cross(a, b):
    """Cross product of vectors a and b."""
    x = a[1] * b[2] - a[2] * b[1]
    y = a[2] * b[0] - a[0] * b[2]
    z = a[0] * b[1] - a[1] * b[0]
    return (x, y, z)

def get3DArea(polypoints):
    """Function which reads the list of coordinates and returns its area.
    The code has been borrowed from http://stackoverflow.com/questions/12642256/python-find-area-of-polygon-from-xyz-coordinates"""
    #-- Compute the area
    total = [0, 0, 0]
    for i in range(len(polypoints)):
        vi1 = polypoints[i]
        if i is len(polypoints)-1:
            vi2 = polypoints[0]
        else:
            vi2 = polypoints[i+1]
        prod = cross(vi1, vi2)
        total[0] += prod[0]
        total[1] += prod[1]
        total[2] += prod[2]
    result = dot(total, unit_normal(polypoints[0], polypoints[1], polypoints[2]))
    return math.fabs(result*.5)


def get2DArea(polypoints):
    """Reads the list of coordinates and returns its projected area (disregards z coords)."""
    flatpolypoints = copy.deepcopy(polypoints)
    for p in flatpolypoints:
        p[2] = 0.0
    return get3DArea(flatpolypoints)


def getNormal(polypoints):
    """Get the normal of the first three points of a polygon. Assumes planarity."""
    return unit_normal(polypoints[0], polypoints[1], polypoints[2])


def getAngles(normal):
    """Get the azimuth and altitude from the normal vector."""
    #-- Convert from polar system to azimuth
    azimuth = 90 - math.degrees(math.atan2(normal[1], normal[0]))
    if azimuth >= 360.0:
        azimuth -= 360.0
    elif azimuth < 0.0:
        azimuth += 360.0
    t = math.sqrt(normal[0]**2 + normal[1]**2)
    if t == 0:
        tilt = 0.0
    else:
        tilt = 90 - math.degrees(math.atan(normal[2] / t)) #0 for flat roof, 90 for wall
    tilt = round(tilt, 3)

    return azimuth, tilt

def GMLstring2points(pointstring):
    """Convert list of points in string to a list of points. Works for 3D points."""
    listPoints = []
    #-- List of coordinates
    coords = pointstring.split()
    #-- Store the coordinate tuple
    assert(len(coords) % 3 == 0)
    for i in range(0, len(coords), 3):
        listPoints.append([float(coords[i]), float(coords[i+1]), float(coords[i+2])])
    return listPoints


def smallestPoint(list_of_points):
    "Finds the smallest point from a three-dimensional tuple list."
    smallest = []
    #-- Sort the points
    sorted_points = sorted(list_of_points, key=lambda x: (x[0], x[1], x[2]))
    #-- First one is the smallest one
    smallest = sorted_points[0]
    return smallest

def highestPoint(list_of_points, a=None):
    "Finds the highest point from a three-dimensional tuple list."
    highest = []
    #-- Sort the points
    sorted_points = sorted(list_of_points, key=lambda x: (x[0], x[1], x[2]))
    #-- Last one is the highest one
    if a is not None:
        equalZ = True
        for i in range(-1, -1 * len(list_of_points), -1):
            if equalZ:
                highest = sorted_points[i]
                if highest[2] != a[2]:
                    equalZ = False
                    break
            else:
                break
    else:
        highest = sorted_points[-1]
    return highest

def centroid(list_of_points):
    """Returns the centroid of the list of points."""
    sum_x = 0
    sum_y = 0
    sum_z = 0
    n = float(len(list_of_points))
    for p in list_of_points:
        sum_x += float(p[0])
        sum_y += float(p[1])
        sum_z += float(p[2])
    return [sum_x / n, sum_y / n, sum_z / n]

def plane(a,b,c):
    """Returns the equation of a three-dimensional plane in space by entering the three coordinates of the plane."""
    p_a = (b[1]-a[1])*(c[2]-a[2])-(c[1]-a[1])*(b[2]-a[2])
    p_b = (b[2]-a[2])*(c[0]-a[0])-(c[2]-a[2])*(b[0]-a[0])
    p_c = (b[0]-a[0])*(c[1]-a[1])-(c[0]-a[0])*(b[1]-a[1])
    p_d = -1*(p_a * a[0] + p_b * a[1] + p_c * a[2])
    return p_a, p_b, p_c, p_d

def get_height(plane, x, y):
    """Get the missing coordinate from the plane equation and the partial coordinates."""
    p_a, p_b, p_c, p_d = plane
    z = (-p_a*x - p_b*y - p_d)/p_c
    return z

def get_y(plane, x, z):
    """Get the missing coordinate from the plane equation and the partial coordinates."""
    p_a, p_b, p_c, p_d = plane
    y = (-p_a*x - p_c*z - p_d)/p_b
    return y

def compare_normals(n1, n2):
    """Compares if two normals are equal or opposite. Takes into account a small tolerance to overcome floating point errors."""
    tolerance = 0.0001
    #-- Assume equal and prove otherwise
    equal = True
    #-- i
    if math.fabs(n1[0] - n2[0]) > tolerance:
        equal = False
    #-- j
    elif math.fabs(n1[1] - n2[1]) > tolerance:
        equal = False
    #-- k
    elif math.fabs(n1[2] - n2[2]) > tolerance:
        equal = False
    return equal

def reverse_vertices(vertices):
    """Reverse vertices. Useful to reorient the normal of the polygon."""
    reversed_vertices = []
    nv = len(vertices)
    for i in range(nv-1, -1, -1):
        reversed_vertices.append(vertices[i])
    return reversed_vertices

def triangulation(e, i):
    """Triangulate the polygon with the exterior and interior list of points. Works only for convex polygons.
    Assumes planarity. Projects to a 2D plane and goes back to 3D."""
    vertices = []
    holes = []
    segments = []
    index_point = 0

    #-- Slope computation points
    a = [[], [], []]
    b = [[], [], []]
    for ip in range(len(e)-1):
        vertices.append(e[ip])
        if a == [[], [], []] and index_point == 0:
            a = [e[ip][0], e[ip][1], e[ip][2]]
        if index_point > 0 and (e[ip] != e[ip-1]):
            if b == [[], [], []]:
                b = [e[ip][0], e[ip][1], e[ip][2]]
        if ip == len(e) - 2:
            segments.append([index_point, 0])
        else:
            segments.append([index_point, index_point+1])
        index_point += 1
    for hole in i:
        first_point_in_hole = index_point
        for p in range(len(hole)-1):
            if p == len(hole)-2:
                segments.append([index_point, first_point_in_hole])
            else:
                segments.append([index_point, index_point+1])
            index_point += 1
            vertices.append(hole[p])
        holes.append(centroid(hole[:-1]))

    #-- Project to 2D since the triangulation cannot be done in 3D with the library that is used
    npolypoints = len(vertices)
    nholes = len(holes)
    #-- Check if the polygon is vertical, i.e. a projection cannot be made.
    #-- First copy the list so the originals are not modified
    temppolypoints = copy.deepcopy(vertices)
    newpolypoints = copy.deepcopy(vertices)
    tempholes = copy.deepcopy(holes)
    newholes = copy.deepcopy(holes)
    #-- Compute the normal of the polygon for detecting vertical polygons and
    #-- for the correct orientation of the new triangulated faces
    #-- If the polygon is vertical
    normal = unit_normal(temppolypoints[0], temppolypoints[1], temppolypoints[2])
    if math.fabs(normal[2]) < 10e-6:
        vertical = True
    else:
        vertical = False
    #-- We want to project the vertical polygon to the XZ plane
    #-- If a polygon is parallel with the YZ plane that will not be possible
    YZ = True
    for i in range(1, npolypoints):
        if temppolypoints[i][0] != temppolypoints[0][0]:
            YZ = False
            continue
    #-- Project the plane in the special case
    if YZ:
        for i in range(0, npolypoints):
            newpolypoints[i][0] = temppolypoints[i][1]
            newpolypoints[i][1] = temppolypoints[i][2]
        for i in range(0, nholes):
            newholes[i][0] = tempholes[i][1]
            newholes[i][1] = tempholes[i][2]
    #-- Project the plane
    elif vertical:
        for i in range(0, npolypoints):
            newpolypoints[i][1] = temppolypoints[i][2]
        for i in range(0, nholes):
            newholes[i][1] = tempholes[i][2]
    else:
        pass #-- No changes here

    #-- Drop the last point (identical to first)
    for p in newpolypoints:
        p.pop(-1)

    #-- If there are no holes
    if len(newholes) == 0:
        newholes = None
    else:
        for h in newholes:
            h.pop(-1)

    #-- Plane information (assumes planarity)
    a = e[0]
    b = e[1]
    c = e[2]
    #-- Construct the plane
    pl = plane(a, b, c)
 
    #-- Prepare the polygon to be triangulated
    poly = {'vertices' : np.array(newpolypoints), 'segments' : np.array(segments), 'holes' : np.array(newholes)}
    #-- Triangulate
    t = triangle.triangulate(poly, "pQjz")
    #-- Get the triangles and their vertices
    tris = t['triangles']
    vert = t['vertices'].tolist()
    #-- Store the vertices of each triangle in a list
    tri_points = []
    for tri in tris:
        tri_points_tmp = []
        for v in tri.tolist():
            vert_adj = [[], [], []]
            if YZ:
                vert_adj[0] = temppolypoints[0][0]
                vert_adj[1] = vert[v][0]
                vert_adj[2] = vert[v][1]
            elif vertical:
                vert_adj[0] = vert[v][0]            
                vert_adj[2] = vert[v][1]
                vert_adj[1] = get_y(pl, vert_adj[0], vert_adj[2])
            else:
                vert_adj[0] = vert[v][0]
                vert_adj[1] = vert[v][1]
                vert_adj[2] = get_height(pl, vert_adj[0], vert_adj[1])
            tri_points_tmp.append(vert_adj)
        tri_normal = unit_normal(tri_points_tmp[0], tri_points_tmp[1], tri_points_tmp[2])
        if compare_normals(normal, tri_normal):
            tri_points.append(tri_points_tmp)
        else:
            tri_points_tmp = reverse_vertices(tri_points_tmp)
            tri_points.append(tri_points_tmp)
    return tri_points