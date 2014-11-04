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

import markup3dmodule
import polygon3dmodule
from lxml import etree
import os
import argparse
import glob
import numpy as np

#-- ARGUMENTS
# -i -- input directory (it will read and convert ALL CityGML files in a directory)
# -o -- output directory (it will output the generated OBJs in that directory in the way that Delft.gml becomes Delft.obj)
#-- SETTINGS of the converter (can be combined):
# -s 0 (default) -- converts all geometries in one class in one file under the same object (plain OBJ file).
# -s 1 -- differentiate between semantics, output each semantic class as one file, e.g. Delft-WallSurface.obj. Please note that in this case the grouped "plain" OBJ is not generated.
# if no thematic boundaries are found, this option is ignored.
# -g 0 (default) -- keeps all objects in the same bin.
# -g 1 -- it creates one object for every building.
# -a 1 or 2 or 3 -- this is a very custom setting for adding the texture based on attributes, here you can see the settings for my particular case of the solar radiation. By default it is off.

#-- Name spaces
ns_citygml="http://www.opengis.net/citygml/2.0"

ns_gml = "http://www.opengis.net/gml"
ns_bldg = "http://www.opengis.net/citygml/building/2.0"
ns_xsi="http://www.w3.org/2001/XMLSchema-instance"
ns_xAL="urn:oasis:names:tc:ciq:xsdschema:xAL:2.0"
ns_xlink="http://www.w3.org/1999/xlink"
ns_dem="http://www.opengis.net/citygml/relief/2.0"

nsmap = {
    None : ns_citygml,
    'gml': ns_gml,
    'bldg': ns_bldg,
    'xsi' : ns_xsi,
    'xAL' : ns_xAL,
    'xlink' : ns_xlink,
    'dem' : ns_dem
}

#-- Text to be printed at the beginning of each OBJ
header = """# Converted from CityGML to OBJ with CityGML2OBJs.
# Conversion tool developed by Filip Biljecki, TU Delft <fbiljecki@gmail.com>, see more at Github:
# https://github.com/tudelft3d/CityGML2OBJs
#

"""

def get_index(point, list_vertices, shift=0):
    """Index the vertices.
    The third option is for incorporating a local index (building-level) to the global one (dataset-level)."""
    global vertices
    """Unique identifier and indexer of vertices."""
    if point in list_vertices:
        return list_vertices.index(point) + 1 + shift, list_vertices
    else:
        list_vertices.append(point)
        return list_vertices.index(point) + 1 + shift, list_vertices

def write_vertices(list_vertices, cla):
    """Write the vertices in the OBJ format."""
    global vertices_output
    for each in list_vertices:
        vertices_output[cla].append("v" + " " + str(each[0]) + " " + str(each[1]) + " " + str(each[2]) + "\n")

def poly_to_obj(poly, cl, material=None):
    """Main conversion function of one polygon to one or more faces in OBJ,
    in a specific semantic class. Supports assigning a material."""
    global local_vertices
    global vertices
    global face_output
    #-- Decompose the polygon into exterior and interior
    e, i = markup3dmodule.polydecomposer(poly)
    #-- Points forming the exterior LinearRing
    epoints = markup3dmodule.GMLpoints(e[0])
    #-- LinearRing(s) forming the interior
    irings = []
    for iring in i:
        irings.append(markup3dmodule.GMLpoints(iring))
    #-- If the polygon validation option is enabled
    if VALIDATION:
        #-- Check the polygon
        valid = polygon3dmodule.isPolyValid(epoints, False)
        if valid:
            for iring in irings:
                if not polygon3dmodule.isPolyValid(iring, False):
                    valid = False
        #-- If everything is valid send them to the Delaunay triangulation
        if valid:
            t = polygon3dmodule.triangulation(epoints, irings)
            #-- Process the triangles
            for tri in t:
                #-- Face marker
                f = "f "
                #-- For each point in the triangle (face) get the index "v" or add it to the index
                for ep in range(0, len(tri)):
                    v, local_vertices[cl] = get_index(tri[ep], local_vertices[cl], len(vertices[cl]))
                    f += str(v) + " "
                #-- Add the material
                if material:
                    face_output[cl].append("usemtl " + str(mtl(material, min_value, max_value, res)) + str("\n"))
                #-- Store all together
                face_output[cl].append(f + "\n")
        else:
            #-- Oops
            print "\t\t!! Detected an invalid polygon. Skipping..."
    else:
        #-- Do the same, but without the validation
        t = polygon3dmodule.triangulation(epoints, irings)
        for tri in t:
            f = "f "
            for ep in range(0, len(tri)):
                v, local_vertices[cl] = get_index(tri[ep], local_vertices[cl], len(vertices[cl]))
                f += str(v) + " "   
            if material:
                face_output[cl].append("usemtl " + str(mtl(material, min_value, max_value, res)) + str("\n"))
            face_output[cl].append(f + "\n")

#-- Parse command-line arguments
PARSER = argparse.ArgumentParser(description='Convert a CityGML to OBJ.')
PARSER.add_argument('-i', '--directory',
    help='Directory containing CityGML file(s).', required=True)
PARSER.add_argument('-o', '--results',
    help='Directory where the OBJ file(s) should be written.', required=True)
PARSER.add_argument('-s', '--semantics',
    help='Write one OBJ (0) or multiple OBJ per semantic class (1). 0 is default.', required=False)
PARSER.add_argument('-g', '--grouping',
    help='Writes all buildings in one group (0) or multiple groups (1). 0 is default.', required=False)
PARSER.add_argument('-a', '--attribute',
    help='Creates a texture regarding the value of an attribute of the surface. No material is default.', required=False)
PARSER.add_argument('-v', '--validation',
    help='Validates polygons, and if they are not valid give a warning and skip them. No validation is default.', required=False)
ARGS = vars(PARSER.parse_args())
DIRECTORY = ARGS['directory']
RESULT = ARGS['results']

SEMANTICS = ARGS['semantics']
if SEMANTICS == '1':
    SEMANTICS = True
elif SEMANTICS == '0':
    SEMANTICS = False
else:
    SEMANTICS = False

OBJECTS = ARGS['grouping']
if OBJECTS == '1':
    OBJECTS = True
elif OBJECTS == '0':
    OBJECTS = False
else:
    OBJECTS = False

ATTRIBUTE = ARGS['attribute']
if ATTRIBUTE == '1':
    ATTRIBUTE = 1
elif ATTRIBUTE == '2':
    ATTRIBUTE = 2
elif ATTRIBUTE == '3':
    ATTRIBUTE = 3
elif ATTRIBUTE == '0':
    ATTRIBUTE = False
else:
    ATTRIBUTE = False

VALIDATION = ARGS['validation']
if VALIDATION == '1':
    VALIDATION = True
elif VALIDATION == '0':
    VALIDATION = False
else:
    VALIDATION = False

#-----------------------------------------------------------------
#-- Attribute stuff

#-- Number of classes (colours)
res = 101
#-- Configuration
#-- Color the surfaces based on the normalised kWh/m^2 value <irradiation>. The plain OBJ will be coloured for the total irradiation.
if ATTRIBUTE == 1:
    min_value = 0#234.591880403
    max_value = 1500#1389.97943395
elif ATTRIBUTE == 2:
    min_value = 157.0136575
    max_value = 83371.4359245
elif ATTRIBUTE == 3:
    min_value = 24925.0
    max_value = 103454.0

#-- Statistic parameter
atts = []

#-- Colouring function
def mtl(att, min_value, max_value, res):
    """Finds the corresponding material."""
    ar = np.linspace(0, 1, res).tolist()
    #-- Get rid of floating point errors
    for i in range(0, len(ar)):
        ar[i] = round(ar[i], 4)
    #-- Normalise the attribute
    v = float(att) / (max_value-min_value)
    #-- Get the material
    assigned_material = min(ar, key=lambda x:abs(x-v))
    return str(assigned_material)
#-----------------------------------------------------------------

#-- Start of the program
print "CityGML2OBJ. Searching for CityGML files..."

#-- Find all CityGML files in the directory
os.chdir(DIRECTORY)
for f in glob.glob("*.gml"):
    FILENAME = f[:f.rfind('.')]
    FULLPATH = DIRECTORY + f

    #-- Reading and parsing the CityGML file(s)
    CITYGML = etree.parse(FULLPATH)
    #-- Getting the root of the XML tree
    root = CITYGML.getroot()
    #-- Empty lists for cityobjects and buildings
    cityObjects = []
    buildings = []

    #--  This denotes the dictionaries in which the surfaces are put.
    output = {}
    vertices_output = {}
    face_output = {}

    #-- This denotes the dictionaries in which all surfaces are put. It is later ignored in the semantic option was invoked.
    output['All'] = []
    output['All'].append(header)
    if ATTRIBUTE:
        output['All'].append("mtllib colormap.mtl\n")
    vertices_output['All'] = []
    face_output['All'] = []

    #-- If the semantic option was invoked, this part adds additional dictionaries.
    if SEMANTICS:
        #-- Easy to modify list of thematic boundaries
        semanticSurfaces = ['GroundSurface', 'WallSurface', 'RoofSurface', 'ClosureSurface', 'CeilingSurface', 'InteriorWallSurface', 'FloorSurface', 'OuterCeilingSurface', 'OuterFloorSurface', 'Door', 'Window']
        for semanticSurface in semanticSurfaces:
            output[semanticSurface] = []
            output[semanticSurface].append(header)
            #-- Add the material library
            if ATTRIBUTE:
                output[semanticSurface].append("mtllib colormap.mtl\n")
            vertices_output[semanticSurface] = []
            face_output[semanticSurface] = []


    #-- Directory of vertices (indexing)
    vertices = {}
    vertices['All'] = []
    if SEMANTICS:
        for semanticSurface in semanticSurfaces:
            vertices[semanticSurface] = []

    #-- Find all instances of cityObjectMember and put them in a list
    for obj in root.getiterator('{%s}cityObjectMember'% ns_citygml):
        cityObjects.append(obj)

    print FILENAME

    if len(cityObjects) > 0:

        #-- Report the progress and contents of the CityGML file
        print "\tThere are", len(cityObjects), "cityObject(s) in this CityGML file."
        #-- Store each building separately
        for cityObject in cityObjects:
            for child in cityObject.getchildren():
                if child.tag == '{%s}Building' %ns_bldg:
                    buildings.append(child)

        print "\tAnalysing buildings and extracting the geometry..."

        #-- Count the buildings
        b_counter = 0

        #-- Do each building separately
        for b in buildings:

            #-- Build the local list of vertices to speed up the indexing
            local_vertices = {}
            local_vertices['All'] = []
            if SEMANTICS:
                for semanticSurface in semanticSurfaces:
                    local_vertices[semanticSurface] = []


            #-- Increment the building counter
            b_counter += 1

            #-- If the object option is on, get the name for each building or create one
            if OBJECTS:
                ob = b.xpath("@g:id", namespaces={'g' : ns_gml})
                if not ob:
                    ob = b_counter
                else:
                    ob = ob[0]
            
            #-- Print progress for large files every 1000 buildings.
            if b_counter > 0 and b_counter % 1000 == 0:
                print str(b_counter) + "\t...",

            #-- Add the object identifier
            if OBJECTS:
                face_output['All'].append('o ' + str(ob) + '\n')

            #-- Add the attribute for the building
            if ATTRIBUTE:
                for ch in b.getchildren():
                    if ch.tag == "{%s}yearlyIrradiation" %ns_citygml:
                        bAttVal = float(ch.text)

            #-- OBJ with all surfaces in the same bin
            polys = markup3dmodule.polygonFinder(b)
            #-- Process each surface
            for poly in polys:
                if ATTRIBUTE:
                    poly_to_obj(poly, 'All', bAttVal)
                    if ATTRIBUTE == 3:
                        atts.append(bAttVal)
                else:
                    poly_to_obj(poly, 'All')
                    
            #-- Semantic decomposition, with taking special care about the openings
            if SEMANTICS:
                #-- First take care about the openings since they can mix up
                openings = []
                openingpolygons = []
                for child in b.getiterator():
                        if child.tag == '{%s}opening' %ns_bldg:
                            openings.append(child)
                            for o in child.findall('.//{%s}Polygon' %ns_gml):
                                openingpolygons.append(o)

                #-- Process each opening
                for o in openings:
                    for child in o.getiterator():
                        if child.tag == '{%s}Window' %ns_bldg or child.tag == '{%s}Door' %ns_bldg:
                            if child.tag == '{%s}Window' %ns_bldg:
                                t = 'Window'
                            else:
                                t = 'Door'
                            polys = markup3dmodule.polygonFinder(o)
                            for poly in polys:
                                poly_to_obj(poly, t)

                #-- Process other thematic boundaries
                for cl in output:
                    cls = []
                    for child in b.getiterator():
                        if child.tag == '{%s}%s' % (ns_bldg, cl):
                            cls.append(child)
                    #-- Is this the first feature of this object?
                    firstF = True
                    for feature in cls:
                        #-- If it is the first feature, print the object identifier
                        if OBJECTS and firstF:
                            face_output[cl].append('o ' + str(ob) + '\n')
                            firstF = False
                        #-- This is not supposed to happen, but just to be sure...
                        if feature.tag == '{%s}Window' %ns_bldg or feature.tag == '{%s}Door' %ns_bldg:
                            continue
                        #-- Find all polygons in this semantic boundary hierarchy
                        for p in feature.findall('.//{%s}Polygon' %ns_gml):
                            if ATTRIBUTE == 1 or ATTRIBUTE == 2:
                                #-- Flush the previous value
                                attVal = None
                                if cl == 'RoofSurface':
                                    #print p.xpath("//@c:irradiation", namespaces={'c' : ns_citygml})
                                    #-- Silly way but it works, as I can't get the above xpath to work for some reason
                                    for ch in p.getchildren():
                                        if ATTRIBUTE == 1:
                                            if ch.tag == "{%s}irradiation" %ns_citygml:
                                                attVal = float(ch.text)
                                                atts.append(attVal)
                                        elif ATTRIBUTE == 2:
                                            if ch.tag == "{%s}totalIrradiation" %ns_citygml:
                                                attVal = float(ch.text)
                                                atts.append(attVal)
                            elif ATTRIBUTE == 3:
                                attVal = None
                                if cl == 'RoofSurface':
                                    attVal = bAttVal
                            else:
                                #-- If the attribute option is off, pass no material
                            	attVal = None
                            found_opening = False
                            for optest in openingpolygons:
                                if p == optest:
                                    found_opening = True
                                    break
                            #-- If there is an opening skip it
                            if found_opening:
                                pass
                            else:
                                #-- Finally process the polygon
                                poly_to_obj(p, cl, attVal)

            #-- Merge the local list of vertices to the global
            for cl in local_vertices:
                for vertex in local_vertices[cl]:
                    vertices[cl].append(vertex)

        print "\tExtraction done. Sorting geometry and writing file(s)."

        #-- Write the OBJ(s)
        os.chdir(RESULT)
        #-- Theme by theme
        for cl in output:
            write_vertices(vertices[cl], cl)
            output[cl].append("\n" + ''.join(vertices_output[cl]))
            output[cl].append("\n" + ''.join(face_output[cl]))
            if cl == 'All':
                adj_suffix = ""
            else:
                adj_suffix = "-" + str(cl)
            if len(vertices[cl]) > 0:
                with open(RESULT + FILENAME +  str(adj_suffix) + ".obj", "w") as obj_file:
                    obj_file.write(''.join(output[cl]))

        print "\tFile(s) written. Conversion successful."

        #-- Print the range of attributes. Useful for defining the range of the colorbar.
        if ATTRIBUTE:
            print '\tRange of attributes:', min(atts), '--', max(atts)

    else:
        print "\tThere is a problem with this file: no cityObjects have been found. Please check if the file complies to CityGML 2.0 (version 1.0 is not supported)."