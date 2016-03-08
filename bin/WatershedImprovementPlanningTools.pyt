import os, sys, shutil, arcpy
import traceback, time

def log(message):
    arcpy.AddMessage(message)
    with file(sys.argv[0]+".log", 'a') as logFile:
        logFile.write("%s:\t%s\n" % (time.asctime(), message))
    
class Toolbox(object):
    def __init__(self):
        self.label = "WIP tools"
        self.alias = ""
        self.tools = [TopoHydro, ImpCov, Runoff]
        
class TopoHydro(object):
    def __init__(self):
        self.label = "Topography and Hydrology Analysis"
        self.description = "Establishes the watershed and stream network"
        self.canRunInBackground = False
        
        arcpy.env.Workspace = self.Workspace = os.path.split(__file__)[0]
        log("Workspace = " + arcpy.env.Workspace)
        arcpy.env.overwriteOutput = True       

    def getParameterInfo(self):
        """Define parameter definitions"""
        
        param0 = arcpy.Parameter(
            displayName="Input Digital Elevation Model",
            name="DEM",
            datatype="DERasterDataset",
            parameterType="Required",
            direction="Input",
            multiValue=False)  
            
        param1 = arcpy.Parameter(
            displayName="Analysis Mask",
            name="Mask",
            datatype="DEFeatureClass",
            parameterType="Optional",
            direction="Input",
            multiValue=False)  
        
        param2 = arcpy.Parameter(
            displayName="Threshold accumulation for Stream formation (acres)",
            name="StreamFormation",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input",
            multiValue=False)  
        
        params = [ param0, param1, param2 ]
        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return
            
    def execute(self, parameters, messages):
        try:
# Local variables:
DEM__2_ = "DEM"
demraster = "C:\\lab06\\Lab06Data.gdb\\demraster"
AnalysisMask = "AnalysisMask"
maskras = "C:\\lab06\\Lab06Data.gdb\\maskras"
Output_drop_raster = ""
DEM = "DEM"
flowdirras = "C:\\lab06\\Lab06Data.gdb\\flowdirras"
accuras = "C:\\lab06\\Lab06Data.gdb\\accuras"
weighed = "C:\\lab06\\Lab06Data.gdb\\weighed"
reclassifed = "C:\\lab06\\Lab06Data.gdb\\reclassifed"
feature = "C:\\lab06\\Lab06Data.gdb\\feature"

# Process: Fill
arcpy.gp.Fill_sa(DEM__2_, demraster, "")

# Process: Polygon to Raster
tempEnvironment0 = arcpy.env.snapRaster
arcpy.env.snapRaster = "DEM"
arcpy.PolygonToRaster_conversion(AnalysisMask, "mask", maskras, "CELL_CENTER", "NONE", "140")
arcpy.env.snapRaster = tempEnvironment0

# Process: Flow Direction
tempEnvironment0 = arcpy.env.mask
arcpy.env.mask = maskras
arcpy.gp.FlowDirection_sa(demraster, flowdirras, "NORMAL", Output_drop_raster)
arcpy.env.mask = tempEnvironment0

# Process: Flow Accumulation
arcpy.gp.FlowAccumulation_sa(flowdirras, accuras, "", "FLOAT")

# Process: Raster Calculator
arcpy.gp.RasterCalculator_sa("\"%accuras%\"*1600/43560", weighed)

# Process: Reclassify
arcpy.Reclassify_3d(weighed, "Value", "0 100 NODATA;100 22532.634765625 1", reclassifed, "DATA")

# Process: Stream to Feature
arcpy.gp.StreamToFeature_sa(reclassifed, flowdirras, feature, "SIMPLIFY")

            log("Parameters are %s, %s, %s" % (parameters[0].valueAsText, parameters[1].valueAsText, parameters[2].valueAsText))
        except Exception as err:
            log(traceback.format_exc())
            log(err)
            raise err
        return

class ImpCov(object):
    def __init__(self):
        self.label = "Imperviousness Analysis"
        self.description = "Impervious area contributions"
        self.canRunInBackground = False
        
        arcpy.env.Workspace = self.Workspace = os.path.split(__file__)[0]
        log("Workspace = " + arcpy.env.Workspace)
        arcpy.env.overwriteOutput = True       

    def getParameterInfo(self):
        """Define parameter definitions"""
        
        param0 = arcpy.Parameter(
            displayName="Impervious Areas",
            name="ImperviousAreas",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input",
            multiValue=False)  
            
        param1 = arcpy.Parameter(
            displayName="Lakes",
            name="Lakes",
            datatype="DEFeatureClass",
            parameterType="Optional",
            direction="Input",
            multiValue=False)  
        
        params = [ param0, param1 ]
        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return
            
    def execute(self, parameters, messages):
        try:
# Local variables:
Impervious = "Impervious"
Impervious__2_ = "Impervious"
task3imper = "C:\\lab06\\Lab06Data.gdb\\task3imper"
block = "C:\\lab06\\Lab06Data.gdb\\block"
aggre = "C:\\lab06\\Lab06Data.gdb\\aggre"
maskras = "maskras"
flowdirras = "C:\\lab06\\Lab06Data.gdb\\flowdirras"
aggre__2_ = "C:\\lab06\\Lab06Data.gdb\\aggre"
task3accum = "C:\\lab06\\Lab06Data.gdb\\task3accum"
accuras = "accuras"
percentage = "C:\\lab06\\Lab06Data.gdb\\percentage"
task3reclassify = "C:\\lab06\\Lab06Data.gdb\\task3reclassify"
reclassifed = "C:\\lab06\\Lab06Data.gdb\\reclassifed"
task3times = "C:\\lab06\\Lab06Data.gdb\\task3times"
task3streamtoraster = "C:\\lab06\\Lab06Data.gdb\\task3streamtoraster"

# Process: Feature to Raster
arcpy.FeatureToRaster_conversion(Impervious__2_, "LENGTH", task3imper, "4")

# Process: Block Statistics
arcpy.gp.BlockStatistics_sa(task3imper, block, "Rectangle 10 10 CELL", "SUM", "DATA")

# Process: Aggregate
arcpy.gp.Aggregate_sa(block, aggre, "10", "MEAN", "EXPAND", "DATA")

# Process: Flow Accumulation
arcpy.gp.FlowAccumulation_sa(flowdirras, task3accum, aggre__2_, "FLOAT")

# Process: Divide
arcpy.gp.Divide_sa(task3accum, accuras, percentage)

# Process: Reclassify
arcpy.Reclassify_3d(percentage, "Value", "0 10 1;10 20 2;20 30 3;30 40 4;40 50 5;50 60 6;60 70 7;70 80 8;80 90 9;90 100 10", task3reclassify, "DATA")

# Process: Times
arcpy.gp.Times_sa(task3reclassify, reclassifed, task3times)

# Process: Stream to Feature
arcpy.gp.StreamToFeature_sa(task3times, flowdirras, task3streamtoraster, "SIMPLIFY")

# Local variables:
task3times = "task3times"
flowaccu = "flowaccu"
accuras = "accuras"
percentage = "percentage"
task4inter2 = "C:\\lab06\\Lab06Data.gdb\\task4inter2"
task4urbaninter2 = "C:\\lab06\\Lab06Data.gdb\\task4urbaninter2"
task4inter5 = "C:\\lab06\\Lab06Data.gdb\\task4inter5"
task4urbaninter5 = "C:\\lab06\\Lab06Data.gdb\\task4urbaninter5"
task4inter10 = "C:\\lab06\\Lab06Data.gdb\\task4inter10"
task4urbaninter10 = "C:\\lab06\\Lab06Data.gdb\\task4urbaninter10"
task4inter25 = "C:\\lab06\\Lab06Data.gdb\\task4inter25"
task4urbaninter25 = "C:\\lab06\\Lab06Data.gdb\\task4urbaninter25"
task4inter50 = "C:\\lab06\\Lab06Data.gdb\\task4inter50"
task4urbaninter50 = "C:\\lab06\\Lab06Data.gdb\\task4urbaninter50"
task4inter100 = "C:\\lab06\\Lab06Data.gdb\\task4inter100"
task4urbaninter100 = "C:\\lab06\\Lab06Data.gdb\\task4urbaninter100"

# Process: Raster Calculator
arcpy.gp.RasterCalculator_sa("144*(Power((\"%accuras%\"*1600/27880000),0.691))", task4inter2)

# Process: Raster Calculator (7)
arcpy.gp.RasterCalculator_sa("28.5*(Power((\"%accuras%\"*1600/27880000),0.390))*(Power(\"%percentage%\",0.436))*(Power(\"%task4inter2%\",0.338))", task4urbaninter2)

# Process: Raster Calculator (2)
arcpy.gp.RasterCalculator_sa("248*(Power((\"%accuras%\"*1600/27880000),0.670))", task4inter5)

# Process: Raster Calculator (8)
arcpy.gp.RasterCalculator_sa("28.5*(Power((\"%accuras%\"*1600/27880000),0.390))*(Power(\"%percentage%\",0.436))*(Power(\"%task4inter5%\",0.338))", task4urbaninter5)

# Process: Raster Calculator (3)
arcpy.gp.RasterCalculator_sa("334*(Power((\"%accuras%\"*1600/27880000),0.665))", task4inter10)

# Process: Raster Calculator (9)
arcpy.gp.RasterCalculator_sa("28.5*(Power((\"%accuras%\"*1600/27880000),0.390))*(Power(\"%percentage%\",0.436))*(Power(\"%task4inter10%\",0.338))", task4urbaninter10)

# Process: Raster Calculator (4)
arcpy.gp.RasterCalculator_sa("467*(Power((\"%accuras%\"*1600/27880000),0.655))", task4inter25)

# Process: Raster Calculator (10)
arcpy.gp.RasterCalculator_sa("28.5*(Power((\"%accuras%\"*1600/27880000),0.390))*(Power(\"%percentage%\",0.436))*(Power(\"%task4inter25%\",0.338))", task4urbaninter25)

# Process: Raster Calculator (5)
arcpy.gp.RasterCalculator_sa("581*(Power((\"%accuras%\"*1600/27880000),0.650))", task4inter50)

# Process: Raster Calculator (11)
arcpy.gp.RasterCalculator_sa("28.5*(Power((\"%accuras%\"*1600/27880000),0.390))*(Power(\"%percentage%\",0.436))*(Power(\"%task4inter50%\",0.338))", task4urbaninter50)

# Process: Raster Calculator (6)
arcpy.gp.RasterCalculator_sa("719*(Power((\"%accuras%\"*1600/27880000),0.643))", task4inter100)

# Process: Raster Calculator (12)
arcpy.gp.RasterCalculator_sa("28.5*(Power((\"%accuras%\"*1600/27880000),0.390))*(Power(\"%percentage%\",0.436))*(Power(\"%task4inter100%\",0.338))", task4urbaninter100)

            log("Parameters are %s, %s" % (parameters[0].valueAsText, parameters[1].valueAsText))
        except Exception as err:
            log(traceback.format_exc())
            log(err)
            raise err
        return
        
class Runoff(object):
    def __init__(self):
        self.label = "Runoff Calculations"
        self.description = "Calculation of standard storm flows via USGS regression equations"
        self.canRunInBackground = False
        
        arcpy.env.Workspace = self.Workspace = os.path.split(__file__)[0]
        log("Workspace = " + arcpy.env.Workspace)
        arcpy.env.overwriteOutput = True       

    def getParameterInfo(self):
        """Define parameter definitions"""
        
        param0 = arcpy.Parameter(
            displayName="Curve Number",
            name="Landuse",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input",
            multiValue=False)  
        
        params = [ param0 ]
        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return
            
    def execute(self, parameters, messages):
        try:
            log("Parameter is %s" % (parameters[0].valueAsText))
        except Exception as err:
            log(traceback.format_exc())
            log(err)
            raise err
        return
		
