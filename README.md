CityGML2OBJs
===========

![CityGML2OBJs-header-image](http://3dgeoinfo.bk.tudelft.nl/biljecki/code/img/citygml2objs-small.png)

A robust semantic-aware utility to convert CityGML data to OBJ, featuring some additional options reflected through the suffix "s" in the name of the package:

- s as in objects -- separation and storage of buildings into multiple objects in OBJ.
- semantics -- decoupling of boundary surfaces in CityGML into separate OBJs.
- see attributes from the CityGML file -- the utility converts quantitative attributes into colours to support their visualisation.
- solution for finally making use of those CityGML files (sarcasm is also an S word :-)).
- sturdy -- checks polygons for validity, considers different forms of geometry storage in GML, detects for lack of boundary surfaces, etc.


Features in more details
---------------------

+ It re-uses repeating vertices, resulting in a reduced file size and redundancy, for which CityGML is not particularly known for.
+ Validates polygon and skips them if they are not valid. Further, the tool supports multiple GML conventions for geometry (e.g. `<gml:posList>` vs `<gml:pos>`).
+ The program is capable of batch processing of multiple files saving you time.
+ Supports polygon holes by triangulating all surfaces. Besides the holes, this is done by default because some software handles OBJs only if the faces are triangulated, especially when it comes to the texture, so not only holey polygons are triangulated. OBJ does not support polygons with holes, which are common in CityGML files (`<gml:interior>`), especially in LOD3 models due to doors, windows and holes left by building installations. For the Delaunay triangulation the tool uses Jonathan Richard Shewchuk's library, through its Python bindings Triangle.
+ It can store the semantic properties, and separate files for each of the thematic class, e.g. from the file `Delft.gml` it creates files `Delft-WallSurface.obj`, `Delft-RoofSurface.obj`, ...
+ OBJ does not really support the concept of attributes, hence if the CityGML file contains an attribute, this is generally lost in the conversion. However, this converter is capable of converting a quantitative attribute to OBJ as a texture (colour) of the feature. For instance, if the attribute about the yearly solar irradiation is available for each polygon in the CityGML file, it is converted to a graphical information and attached to each polygon as a surface, so now you can easily visualise your attributes in CityGML. Please note that this is a very custom setting, and you will need to adapt the code to match your needs.


System requirements
---------------------

Python packages:

+ [Numpy](http://docs.scipy.org/doc/numpy/user/install.html) (likely already on your system)
+ [Triangle](http://dzhelil.info/triangle/). If not on your system: `easy_install triangle`
  

Optional:

+ [Matplotlib](http://matplotlib.org/users/installing.html)

CityGML requirements
---------------------

Mandatory:

+ CityGML 2.0 (1.0 doesn't work)
+ Files must end with `.gml`
+ Vertices in either `<gml:posList>` or `<gml:pos>`

Optional, but recommended:

+ `<gml:id>` for each `<bldg:Building>`
+ `<gml:id>` for each `<gml:Polygon>`


Usage and options
---------------------

### Introduction

To simply convert CityGML data into OBJ type the following command:

```
python CityGML2OBJs.py -i /path/to/CityGML/files/ -o /path/to/new/OBJ/files/
```

The tool will convert all `*.gml` it finds in that folder.

### Semantics

If you call the `-s 1` option:

```
python CityGML2OBJs.py -i /path/to/CityGML/files/ -o /path/to/new/OBJ/files/ -s 1
```

the tool will create an OBJ file for each of the boundary surfaces it encounters, e.g. `Delft.gml` containing `RoofSurface`, `WallSurface` and `GroundSurface` will result in: `Delft-RoofSurface.obj`, and so on.

Here is an example of the OBJ file representing the `WallSurface`:

![Triangulated WallSurface](http://3dgeoinfo.bk.tudelft.nl/biljecki/code/img/sem-tri-small.png)

Regardless of the semantic option, the program always outputs the plain OBJ. This is a useful approach if you load data which does not have boundary surfaces (e.g. only a bunch of solids) so you'll always get something back. The tool detects if there are no thematic boundaries, so doesn't write empty obj files, for instance, an empty `*-Window.obj` for an LOD2 model.


### Objects

CityGML is a structured format. If you call the flag `-g 1` you'll preserve the objects in the OBJ file

```
python CityGML2OBJs.py -i /path/to/CityGML/files/ -o /path/to/new/OBJ/files/ -g 1
```

For the object option the name of the object will be derived from the `<gml:id>`, if not, an ordered list will be made starting from 1, and each object will be named as an integer from 1 to *n*, where *n* is the number of objects.

So this

```
<cityObjectMember>
   <bldg:Building gml:id="ab76da5b-82d6-44ad-a670-c1f8b4f00edc">
      <bldg:boundedBy>
         <bldg:GroundSurface>
   		    ...
   ```

becomes

```
o ab76da5b-82d6-44ad-a670-c1f8b4f00edc
f 635 636 637 
f 636 635 638 
f 639 640 641
...
```



### Colour attributes

**Please note that this is an experimental feature adapted to specific settings.**

I have CityGML files with the attribute value of the solar potential (derived with Solar3Dcity, an experimental tool that I have recently developed and release soon) for each polygon. Normally these values cannot be visualised and are lost in the conversion to other formats. This tool solves this problem by normalising the quantitative attributes and colour them according to a colorbar, which is stored as a material (MTL) file.

Ancillary tools have been developed to make this feature use-friendly and visually appealing. Open each of these ancillary python files and fiddle with the values.

Generate the MTL library:

```
python generateMTL.py
```

Print a colorbar with the transparent background:

```
python plotcolorbar.py
```

Put the newly generated MTL in the directory with the CityGML data and run the utility with the option `-s 1` or `-s 2` or `-s 3`:

```
python CityGML2OBJs.py -i /path/to/CityGML/files/ -o /path/to/new/OBJ/files/ -s 1
```

Now the values of the solar potential of roof surfaces in the CityGML file are stored as textures (colours), and such can be easily visualised:

![Values from Solar3Dcity](http://3dgeoinfo.bk.tudelft.nl/biljecki/code/img/irrT-small.png)


The different options are for transfering the values of attributes between different hierarchical levels. For instance, the option 3 takes the attribute assigned to the building, and colours only the triangles representing the RoofSurface, instead of all faces representing that building. If you want to discuss this in further details to accommodate your needs, do not hesitate to contact me.

![Attributes](http://3dgeoinfo.bk.tudelft.nl/biljecki/code/img/att-uml.png)

Known limitations, important notes, and plans for enhancements
---------------------

* Other thematic classes are not supported in the semantic sense. All CityGML files I have contain only buildings, so not much use of implementing other themes. However, all geometry should be able to be converted to the plain OBJ regardless of the theme.
* The tool supports only single-LOD files. If you load a multi-LOD file, you'll get their union.
* `XLink` is not supported, nor will be because for most files it will result in duplicate geometry. 
* The tool does not support non-convex polygons in the interior, for which might happen that the centroid of a hole is outside the hole, messing up the triangulation. This is on my todo list, albeit I haven't encountered any such case, nor I can normally imagine surfaces in CityGML being non-convex.
* CityGML can be a nasty format because there may be multiple ways to store the geometry. For instance, points can be stored under `<gml:pos>` and `<gml:posList>`. Check this interesting [blog post by Even Rouault](http://erouault.blogspot.nl/2014/04/gml-madness.html). I have tried to regard all cases, so it should work for your files, but if your file cannot be parsed, let me know.

Performance
---------------------

The speed mainly depends on the invoked options and the level of detail of the data which dramatically increases the number of triangles in the OBJ, mostly due to the openings.

For the datasets I have (~100 buildings), the performance is as follows:

* LOD2 (average 13 triangles per building)
  * plain options: 0.004 seconds per building
  * plain + semantics: 0.013 seconds per building
* LOD3 (average 331 triangles per building)
  * plain options: 0.048 seconds per building
  * plain + semantics: 0.0933 seconds per building
  
LOD0 and LOD1 have roughly the same performance as LOD2. Validation of polygons does not decrease the speed.

Reports, research, and citations
---------------------

I will be very happy to hear if you find this tool useful for your workflow. If you use it and if you are writing a research publication, please contact me to give you a reference to cite (the paper under submission, so the record is dynamic).


Contact me for questions and feedback
---------------------
Filip Biljecki

Faculty of Architecture and the Built Environment

Delft University of Technology

fbiljecki@gmail.com

[http://3dgeoinfo.bk.tudelft.nl/biljecki/](http://3dgeoinfo.bk.tudelft.nl/biljecki/)



Acknowledgments
---------------------

+ [Ken Arroyo Ohori](http://www.gdmc.nl/Ken/)

+ Ravi Peters who developed a similar software [citygml2obj](https://code.google.com/p/citygml2obj/) in 2009, and gave me the permission to use the name of his software.

+ [Hugo Ledoux](http://homepage.tudelft.nl/23t4p/)

+ [Martijn Meijers](http://www.gdmc.nl/martijn/)