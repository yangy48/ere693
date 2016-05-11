import os, sys, shutil, arcpy
import traceback, time
from arcpy.sa import *
from arcpy import env


arcpy.CheckOutExtension("Spatial")

DEBUGGING = False

def log(message):
    arcpy.AddMessage(message)
    with file(sys.argv[0]+".log", 'a') as logFile:
        logFile.write("%s:\t%s\n" % (time.asctime(), message))

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "Toolbox"
        self.alias = ""

        # List of tool classes associated with this toolbox
        self.tools = [TopoHydro,ImpCov,Runoff,GetNEXRAD,ScenarioAnalysis,task2analysis]



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
            
        param3 = arcpy.Parameter(
            displayName="Existing vector stream to use to modify drainage",
            name="ExistingStreams",
            datatype="DEFeatureClass",
            parameterType="Optional",
            direction="Input",
            multiValue=False)
        
        params = [ param0, param1, param2, param3 ]
        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return
            
    def execute(self, parameters, messages):
        try:
            demPath = parameters[0].valueAsText
            
            arcpy.env.extent = demPath
            arcpy.env.snapRaster = parameters[1].valueAsText
            arcpy.env.cellSize = demPath

            dem = Raster(demPath)
            fill = Fill(dem)
            flowDirection = FlowDirection(fill)
            flowAccumulation = FlowAccumulation(flowDirection,"", "FLOAT")
            reclassify = Reclassify(flowAccumulation, "Value", "0 51689 1;51689 169257 2;169257 411422 3;411422 770795 4","DATA")
            ## should set the workspace first, as geoprocessing env variable
            reclassify.save("C:/GIS/reclassify.tif")
            if DEBUGGING: flowAccumulation.save("flowaccumulation.tif") 

			
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

        param2 = arcpy.Parameter(
            displayName="Input Digital Elevation Model",
            name="DEM",
            datatype="DERasterDataset",
            parameterType="Required",
            direction="Input",
            multiValue=False)

         param3 = arcpy.Parameter(
            displayName="Analysis Mask",
            name="Mask",
            datatype="DEFeatureClass",
            parameterType="Optional",
            direction="Input",
            multiValue=False)
         
        params = [ param0, param1,param2,param3 ]
        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return
            
    def execute(self, parameters, messages):
        try:
            log("Parameters are %s, %s" % (parameters[0].valueAsText, parameters[1].valueAsText))			

            demPath = parameters[2].valueAsText
            
            arcpy.env.extent = demPath
            arcpy.env.snapRaster = parameters[3].valueAsText
            arcpy.env.cellSize = demPath

            dem = Raster(demPath)
            fill = Fill(dem)
            flowd = FlowDirection(fill)
            flowaccum = FlowAccumulation(flowd,"", "FLOAT")
            rastercalc = Times(flowaccum, 0.036730458)
            reclass = Reclassify(rastercalc, "Value", "0 6997 NODATA;6997 28312.03125 1", "DATA")

            # Local variables: define these by finding them in your workspace or getting them as tool parameters
            Impervious = parameters[0].valueAsText
	    arcpy.CalculateField_management(Impervious, "LENGTH", "1", "VB", "")
            Imper_rast = "Imper_rast"
            arcpy.FeatureToRaster_conversion(Impervious, "LENGTH", Imper_rast, "4")
            block_rast = BlockStatistics(Imper_rast, "Rectangle 10 10 CELL", "SUM", "DATA")
            agg_rast = Aggregate(block_rast, "10", "MEAN", "EXPAND", "DATA")

            imper_accum = FlowAccumulation(flowd, agg_rast, "FLOAT")
            Divide_1 = Divide(imper_accum, flowaccum)
            reclass_imperv = Reclassify(Divide_1, "Value", "0 10 1;10 20 2;20 30 3;30 40 4;40 50 5;50 60 6;60 70 7;70 80 8;80 90 9;90 100 10", "DATA")
            imper_mult = Times(reclass_imperv, reclass)		
            StreamToFeature(imper_mult, flowd, "Stream_Task3Imp", "SIMPLIFY")
            imper_mult.save("C:/GIS/imper_mult.tif") 

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
        param2 = arcpy.Parameter(
            displayName="Input Digital Elevation Model",
            name="DEM",
            datatype="DERasterDataset",
            parameterType="Required",
            direction="Input",
            multiValue=False)  
   
        param3 = arcpy.Parameter(
            displayName="Curve Number",
            name="Landuse",
            datatype="DEFeatureClass",
            #parameterType="Required",
            parameterType="Optional",
            direction="Input",
            multiValue=False)  
               
        params = [ param0, param1,param2, param3 ]
        return params

    def isLicensed(self):
        return True

    def updateParameters(self, parameters):
        return

    def updateMessages(self, parameters):
        return
            
    def execute(self, parameters, messages):
        try:
            log("Parameters are %s, %s" % (parameters[0].valueAsText, parameters[1].valueAsText))			
            ##calculate topography
            demPath = parameters[2].valueAsText
            
            arcpy.env.extent = demPath
            #arcpy.env.snapRaster = parameters[1].valueAsText
            arcpy.env.cellSize = demPath

            dem = Raster(demPath)
            fill = Fill(dem)
            flowd = FlowDirection(fill)
            flowaccum = FlowAccumulation(flowd,"", "FLOAT")
            rastercalc = Times(flowaccum, 0.036730458)
            reclass = Reclassify(rastercalc, "Value", "0 6997 NODATA;6997 28312.03125 1", "DATA")

            # Local variables: define these by finding them in your workspace or getting them as tool parameters
            Impervious = parameters[0].valueAsText
	    arcpy.CalculateField_management(Impervious, "LENGTH", "1", "VB", "")
            Imper_rast = "Imper_rast"
            arcpy.FeatureToRaster_conversion(Impervious, "LENGTH", Imper_rast, "4")
            block_rast = BlockStatistics(Imper_rast, "Rectangle 10 10 CELL", "SUM", "DATA")
            agg_rast = Aggregate(block_rast, "10", "MEAN", "EXPAND", "DATA")

            imper_accum = FlowAccumulation(flowd, agg_rast, "FLOAT")
            Divide_1= Divide(imper_accum, flowaccum)
            reclass_imperv = Reclassify(Divide_1, "Value", "0 10 1;10 20 2;20 30 3;30 40 4;40 50 5;50 60 6;60 70 7;70 80 8;80 90 9;90 100 10", "DATA")
            imper_mult = Times(reclass_imperv, reclass)		
            StreamToFeature(imper_mult, flowd, "Stream_Task3Imp", "SIMPLIFY")
        
            ##calculate runoff flow
            flowaccum_sqmi=Times(rastercalc, 0.0015625)
            recur_2=Power(flowaccum_sqmi,0.691)
            recur_5=Power(flowaccum_sqmi,0.670)
            recur_10=Power(flowaccum_sqmi,0.665)
            recur_25=Power(flowaccum_sqmi,0.655)
            recur_50=Power(flowaccum_sqmi,0.650)
            recur_100=Power(flowaccum_sqmi,0.643)
            recurq_2=Times(recur_2,144)
            recurq_5=Times(recur_5,248)
            recurq_10=Times(recur_10,334)
            recurq_25=Times(recur_25,467)
            recurq_50=Times(recur_50,581)
            recurq_100=Times(recur_100,719)
            recurqq_2=Power(recurq_2,0.338)
            recurqq_5=Power(recurq_5,0.338)
            recurqq_10=Power(recurq_10,0.338)
            recurqq_25=Power(recurq_25,0.338)
            recurqq_50=Power(recurq_50,0.338)
            recurqq_100=Power(recurq_100,0.338)
            Ia=Power(Divide_1,0.436)
            Da=Power(flowaccum_sqmi,0.390)
            Daa=Times(Da,28.5)
            Db=Times(Daa,Ia)
            recur_2I=Times(Db,recurqq_2)
            recur_5I=Times(Db,recurqq_5)
            recur_10I=Times(Db,recurqq_10)
            recur_25I=Times(Db,recurqq_25)
            recur_50I=Times(Db,recurqq_50)
            recur_100I=Times(Db,recurqq_100)

        except Exception as err:
            log(traceback.format_exc())
            log(err)
            raise err
        return

class GetNEXRAD(object):
    def __init__(self):
        self.label = "Get NEXRAD rainfall"
        self.description = "Get a raster of rainfall for a specific rain event from NEXRAD weather radar"
        self.canRunInBackground = False
        
        arcpy.env.Workspace = self.Workspace = os.path.split(__file__)[0]
        log("Workspace = " + arcpy.env.Workspace)
        arcpy.env.overwriteOutput = True       

    def getParameterInfo(self):
        """Define parameter definitions"""
        
        param0 = arcpy.Parameter(
            displayName="Start Date",
            name="startDate",
            datatype="GPDate",
            parameterType="Required",
            direction="Input",
            multiValue=False)  
        
        param1 = arcpy.Parameter(
            displayName="End Date",
            name="endDate",
            datatype="GPDate",
            parameterType="Required",
            direction="Input",
            multiValue=False)  
        
        param2 = arcpy.Parameter(
            displayName="Radar Station ID",
            name="radarID",
            datatype="GPString",
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
            log("Parameter is %s" % (parameters[0].valueAsText))
            
            # code for vector -> raster from Tyler Pitts
            lie=arcpy.CheckOutExtension ('Spatial')
            log ( lie )
            shapefiles=[]
            stormfolder=1
            while stormfolder<=4:
                #log ( 'checking folder',stormfolder )
                shapefiles=[]
                for root, dirs, files in os.walk('storm'+str(stormfolder)):
                    for file in files:
                        if file.endswith('.shp'):
                                shapefiles.append('storm'+str(stormfolder)+'/'+file)
                log ( 'done creating an array of the shapefiles' )
                log ( 'converting to rasters' )
                rasters=[]
                for x in range(len(shapefiles)):
                    #Slog ( 'converting',shapefiles[x] )
                    raster=arcpy.PolygonToRaster_conversion(shapefiles[x], 'value', 'storm'+str(stormfolder)+'/raster'+str(x), 'CELL_CENTER', 'NONE',0.00012196015)
                    rasters.append(raster)
                log ( 'completed raster conversion' )
                log ( 'calculating cell statistics' )
                maxreflect=CellStatistics (rasters, 'MAXIMUM', 'DATA')
                maxreflect.save('storm'+str(stormfolder)+'/reflect'+str(stormfolder)+'.tif')
                lowerLeft = arcpy.Point(maxreflect.extent.XMin,maxreflect.extent.YMin)
                cellSize = maxreflect.meanCellWidth
                reflectence=arcpy.RasterToNumPyArray(maxreflect)
                rows=len(reflectence)
                cols=len(reflectence[0])
                rainfallraster=numpy.zeros((rows,cols))
                for row in range(rows):
                    for col in range(cols):
                        if reflectence[row][col]<0:
                            rainfallraster[row][col]=0
                        rainfallraster[row][col]=(reflectence[row][col]/300)**(1/1.4)
                where_are_NaNs = numpy.isnan(rainfallraster)
                rainfallraster[where_are_NaNs]=0
                newraster=arcpy.NumPyArrayToRaster(rainfallraster,lowerLeft,cellSize)
                newraster.save('storm'+str(stormfolder)+'/rainfall'+str(stormfolder)+'.tif')
                stormfolder=stormfolder+1
                log ( 'completed rainfall calc' )
                #log ( 'complete with folder',stormfolder )
            log ( 'finished making max reflectance rasters' )

        except Exception as err:
            log(traceback.format_exc())
            log(err)
            raise err
        return

class ScenarioAnalysis(object):
    def __init__(self):
        self.label = "Scenario Analysis"
        self.description = "Compute a quantification of Watershed-wide Improvement based on BMP Buildout Scenario"
        self.canRunInBackground = False
        
        arcpy.env.Workspace = self.Workspace = os.path.split(__file__)[0]
        log("Workspace = " + arcpy.env.Workspace)
        arcpy.env.overwriteOutput = True       

    def getParameterInfo(self):
        """Define parameter definitions"""
        
        param0 = arcpy.Parameter(
            displayName="BMP Points",
            name="bmppts",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input",
            multiValue=False)  
        
        param1 = arcpy.Parameter(
            displayName="Status Field",
            name="statusField",
            datatype="Field",
            parameterType="Required",
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
            log("Parameter is %s" % (parameters[0].valueAsText))
            env.workspace = "C:/GIS/lab09.gdb


            ##calculate existing runoff
            Lakes = "Lakes"
            LanduseExisting = "LanduseExisting"
            Impervious = "Impervious"
            BMPs = parameters[0].valueAsText
            inFeatures = [Lakes, LanduseExisting, Impervious]
            union = "union"

            arcpy.Union_analysis (inFeatures,unionE,"ALL", "", "GAPS")

            arcpy.AddField_management("union", "TotalNitrogen", "DOUBLE")
            arcpy.AddField_management("union", "TotalPhosphorus", "DOUBLE")
            arcpy.AddField_management("union", "Sediment", "DOUBLE")
            arcpy.AddField_management("union", "Copper", "DOUBLE")
            arcpy.AddField_management("union", "FecalColiform", "DOUBLE")
            arcpy.AddField_management("union", "Zinc", "DOUBLE")    

            arcpy.SelectLayerByAttribute_management(union, "NEW_SELECTION", "Reclassify = 'Roadways'")
            arcpy.CalculateField_management(union, "TotalNitrogen", "12.2", "VB", "")
            arcpy.CalculateField_management(union, "TotalPhosphorus", "1.8", "VB", "")
            arcpy.CalculateField_management(union, "Sediment", "405", "VB", "")
            arcpy.CalculateField_management(union, "Copper", "0", "VB", "")
            arcpy.CalculateField_management(union, "Zinc", "0.1", "VB", "")
            arcpy.CalculateField_management(union, "FecalColiform", "2.8", "VB", "")


            arcpy.SelectLayerByAttribute_management(union, "NEW_SELECTION", "Reclassify in ( 'Commercial' )")
            arcpy.CalculateField_management(union, "TotalNitrogen", "14", "VB", "")
            arcpy.CalculateField_management(union, "TotalPhosphorus", "2.7", "VB", "")
            arcpy.CalculateField_management(union, "Sediment", "400", "VB", "")
            arcpy.CalculateField_management(union, "Copper", "0", "VB", "")
            arcpy.CalculateField_management(union, "Zinc", "0", "VB", "")
            arcpy.CalculateField_management(union, "FecalColiform", "8.4", "VB", "")


            arcpy.SelectLayerByAttribute_management(union, "NEW_SELECTION", "Reclassify IN ( 'Industrial' )")
            arcpy.CalculateField_management(union, "TotalNitrogen", "10.4", "VB", "")
            arcpy.CalculateField_management(union, "TotalPhosphorus", "1.9", "VB", "")
            arcpy.CalculateField_management(union, "Sediment", "372.5", "VB", "")
            arcpy.CalculateField_management(union, "Copper", "0.2", "VB", "")
            arcpy.CalculateField_management(union, "Zinc", "0.1", "VB", "")
            arcpy.CalculateField_management(union, "FecalColiform", "8.4", "VB", "")

            arcpy.SelectLayerByAttribute_management(union, "NEW_SELECTION", "Reclassify in ( 'Institutional' , 'Research Triangle Park' )")
            arcpy.CalculateField_management(union, "TotalNitrogen", "9.4", "VB", "")
            arcpy.CalculateField_management(union, "TotalPhosphorus", "0.7", "VB", "")
            arcpy.CalculateField_management(union, "Sediment", "50", "VB", "")
            arcpy.CalculateField_management(union, "Copper", "0", "VB", "")
            arcpy.CalculateField_management(union, "Zinc", "0", "VB", "")
            arcpy.CalculateField_management(union, "FecalColiform", "14.8", "VB", "")

            arcpy.SelectLayerByAttribute_management(union, "NEW_SELECTION", "Reclassify IN ( 'Parks and Open Space' , 'Agricultural' )")
            arcpy.CalculateField_management(union, "TotalNitrogen", "2.3", "VB", "")
            arcpy.CalculateField_management(union, "TotalPhosphorus", "0.1", "VB", "")
            arcpy.CalculateField_management(union, "Sediment", "10", "VB", "")
            arcpy.CalculateField_management(union, "Copper", "0", "VB", "")
            arcpy.CalculateField_management(union, "Zinc", "0", "VB", "")
            arcpy.CalculateField_management(union, "FecalColiform", "12", "VB", "")

            arcpy.SelectLayerByAttribute_management(union, "NEW_SELECTION", "Reclassify IN ( 'High Density Residential' , 'Medium Density Residential' )")
            arcpy.CalculateField_management(union, "TotalNitrogen", "11.2", "VB", "")
            arcpy.CalculateField_management(union, "TotalPhosphorus", "1.6", "VB", "")
            arcpy.CalculateField_management(union, "Sediment", "242.5", "VB", "")
            arcpy.CalculateField_management(union, "Copper", "0", "VB", "")
            arcpy.CalculateField_management(union, "Zinc", "0", "VB", "")
            arcpy.CalculateField_management(union, "FecalColiform", "30.2", "VB", "")

            arcpy.SelectLayerByAttribute_management(union, "NEW_SELECTION", "Reclassify IN( 'Very Low Density Residential' , 'Low Density Residential' )")
            arcpy.CalculateField_management(union, "TotalNitrogen", "6.4", "VB", "")
            arcpy.CalculateField_management(union, "TotalPhosphorus", "0.7", "VB", "")
            arcpy.CalculateField_management(union, "Sediment", "150", "VB", "")
            arcpy.CalculateField_management(union, "Copper", "0", "VB", "")
            arcpy.CalculateField_management(union, "Zinc", "0", "VB", "")
            arcpy.CalculateField_management(union, "FecalColiform", "16.2", "VB", "")

            arcpy.SelectLayerByAttribute_management(union, "CLEAR_SELECTION", "")

            ##Future landuse
            LanduseFuture = "LanduseFuture"

            inFeatures1 = [Lakes, LanduseFuture, Impervious]
            union_1 = "union_1"
            arcpy.Union_analysis (inFeatures1,union_1,"ALL", "", "GAPS")
            arcpy.AddField_management("union_1", "TotalNitrogen", "DOUBLE")
            arcpy.AddField_management("union_1", "TotalPhosphorus", "DOUBLE")
            arcpy.AddField_management("union_1", "Sediment", "DOUBLE")
            arcpy.AddField_management("union_1", "Copper", "DOUBLE")
            arcpy.AddField_management("union_1", "Zinc", "DOUBLE")
            arcpy.AddField_management("union_1", "FecalColiform", "DOUBLE")

            arcpy.SelectLayerByAttribute_management(union_1, "NEW_SELECTION", "Reclassify = 'Roadways'")
            arcpy.CalculateField_management(union_1, "TotalNitrogen", "12.2", "VB", "")
            arcpy.CalculateField_management(union_1, "TotalPhosphorus", "1.8", "VB", "")
            arcpy.CalculateField_management(union_1, "Sediment", "405", "VB", "")
            arcpy.CalculateField_management(union_1, "Copper", "0", "VB", "")
            arcpy.CalculateField_management(union_1, "Zinc", "0.1", "VB", "")
            arcpy.CalculateField_management(union_1, "FecalColiform", "2.8", "VB", "")


            arcpy.SelectLayerByAttribute_management(union_1, "NEW_SELECTION", "Reclassify in ( 'Commercial' )")
            arcpy.CalculateField_management(union_1, "TotalNitrogen", "14", "VB", "")
            arcpy.CalculateField_management(union_1, "TotalPhosphorus", "2.7", "VB", "")
            arcpy.CalculateField_management(union_1, "Sediment", "400", "VB", "")
            arcpy.CalculateField_management(union_1, "Copper", "0", "VB", "")
            arcpy.CalculateField_management(union_1, "Zinc", "0", "VB", "")
            arcpy.CalculateField_management(union_1, "FecalColiform", "8.4", "VB", "")


            arcpy.SelectLayerByAttribute_management(union_1, "NEW_SELECTION", "Reclassify IN ( 'Industrial' )")
            arcpy.CalculateField_management(union_1, "TotalNitrogen", "10.4", "VB", "")
            arcpy.CalculateField_management(union_1, "TotalPhosphorus", "1.9", "VB", "")
            arcpy.CalculateField_management(union_1, "Sediment", "372.5", "VB", "")
            arcpy.CalculateField_management(union_1, "Copper", "0.2", "VB", "")
            arcpy.CalculateField_management(union_1, "Zinc", "0.1", "VB", "")
            arcpy.CalculateField_management(union_1, "FecalColiform", "8.4", "VB", "")

            arcpy.SelectLayerByAttribute_management(union_1, "NEW_SELECTION", "Reclassify in ( 'Institutional' , 'Research Triangle Park' )")
            arcpy.CalculateField_management(union_1, "TotalNitrogen", "9.4", "VB", "")
            arcpy.CalculateField_management(union_1, "TotalPhosphorus", "0.7", "VB", "")
            arcpy.CalculateField_management(union_1, "Sediment", "50", "VB", "")
            arcpy.CalculateField_management(union_1, "Copper", "0", "VB", "")
            arcpy.CalculateField_management(union_1, "Zinc", "0", "VB", "")
            arcpy.CalculateField_management(union_1, "FecalColiform", "14.8", "VB", "")

            arcpy.SelectLayerByAttribute_management(union_1, "NEW_SELECTION", "Reclassify IN ( 'Parks and Open Space' , 'Agricultural' )")
            arcpy.CalculateField_management(union_1, "TotalNitrogen", "2.3", "VB", "")
            arcpy.CalculateField_management(union_1, "TotalPhosphorus", "0.1", "VB", "")
            arcpy.CalculateField_management(union_1, "Sediment", "10", "VB", "")
            arcpy.CalculateField_management(union_1, "Copper", "0", "VB", "")
            arcpy.CalculateField_management(union_1, "Zinc", "0", "VB", "")
            arcpy.CalculateField_management(union_1, "FecalColiform", "12", "VB", "")

            arcpy.SelectLayerByAttribute_management(union_1, "NEW_SELECTION", "Reclassify IN ( 'High Density Residential' , 'Medium Density Residential' )")
            arcpy.CalculateField_management(union_1, "TotalNitrogen", "11.2", "VB", "")
            arcpy.CalculateField_management(union_1, "TotalPhosphorus", "1.6", "VB", "")
            arcpy.CalculateField_management(union_1, "Sediment", "242.5", "VB", "")
            arcpy.CalculateField_management(union_1, "Copper", "0", "VB", "")
            arcpy.CalculateField_management(union_1, "Zinc", "0", "VB", "")
            arcpy.CalculateField_management(union_1, "FecalColiform", "30.2", "VB", "")

            arcpy.SelectLayerByAttribute_management(union_1, "NEW_SELECTION", "Reclassify IN( 'Very Low Density Residential' , 'Low Density Residential' )")
            arcpy.CalculateField_management(union_1, "TotalNitrogen", "6.4", "VB", "")
            arcpy.CalculateField_management(union_1, "TotalPhosphorus", "0.7", "VB", "")
            arcpy.CalculateField_management(union_1, "Sediment", "150", "VB", "")
            arcpy.CalculateField_management(union_1, "Copper", "0", "VB", "")
            arcpy.CalculateField_management(union_1, "Zinc", "0", "VB", "")
            arcpy.CalculateField_management(union_1, "FecalColiform", "16.2", "VB", "")

            arcpy.SelectLayerByAttribute_management(union_1, "CLEAR_SELECTION", "")
           
            Raster_Nitrogen = "Raster_Nitrogen"
            Raster_Phosphorus = "Raster_Phosphorus"
            Raster_Sediment = "Raster_Sediment"
            Raster_Copper = "Raster_Copper"
            Raster_Zinc = "Raster_Zinc"
            Raster_Fecal = "Raster_Fecal"
            arcpy.PolygonToRaster_conversion(union, "TotalNitrogen", Raster_Nitrogen, "CELL_CENTER", "NONE", "40")
            arcpy.PolygonToRaster_conversion(union, "TotalPhosphorus", Raster_Phosphorus, "CELL_CENTER", "NONE", "40")
            arcpy.PolygonToRaster_conversion(union, "Sediment", Raster_Sediment, "CELL_CENTER", "NONE", "40")
            arcpy.PolygonToRaster_conversion(union, "Copper", Raster_Copper, "CELL_CENTER", "NONE", "40")
            arcpy.PolygonToRaster_conversion(union, "Zinc", Raster_Zinc, "CELL_CENTER", "NONE", "40")
            arcpy.PolygonToRaster_conversion(union, "FecalColiform", Raster_Fecal, "CELL_CENTER", "NONE", "40")

            Raster_1_Nitrogen = "Raster_1_Nitrogen"
            Raster_1_Phosphorus = "Raster_1_Phosphorus"
            Raster_1_Sediment = "Raster_1_Sediment"
            Raster_1_Copper = "Raster_1_Copper"
            Raster_1_Zinc = "Raster_1_Zinc"
            Raster_1_Fecal = "Raster_1_Fecal"

            arcpy.PolygonToRaster_conversion(union_1, "TotalNitrogen", Raster_1_Nitrogen, "CELL_CENTER", "NONE", "40")
            arcpy.PolygonToRaster_conversion(union_1, "TotalPhosphorus", Raster_1_Phosphorus, "CELL_CENTER", "NONE", "40")
            arcpy.PolygonToRaster_conversion(union_1, "Sediment", Raster_1_Sediment, "CELL_CENTER", "NONE", "40")
            arcpy.PolygonToRaster_conversion(union_1, "Copper", Raster_1_Copper, "CELL_CENTER", "NONE", "40")
            arcpy.PolygonToRaster_conversion(union_1, "Zinc", Raster_1_Zinc, "CELL_CENTER", "NONE", "40")
            arcpy.PolygonToRaster_conversion(union_1, "FecalColiform", Raster_1_Fecal, "CELL_CENTER", "NONE", "40")

            BMPN = "BMPN"
            BMPP = "BMPP"
            BMPFC = "BMPFC"
            BMPCU = "BMPCU"
            BMPZn = "BMPZn"
            BMPSediment = "BMPSediment"


            arcpy.PointToRaster_conversion(BMPs, "TN_Eff_Ex", BMPN, "MOST_FREQUENT", "NONE", "40")
            arcpy.PointToRaster_conversion(BMPs, "TP_Eff_Ex", BMPP, "MOST_FREQUENT", "NONE", "40")
            arcpy.PointToRaster_conversion(BMPs, "FC_Eff_Ex", BMPFC, "MOST_FREQUENT", "NONE", "40")
            arcpy.PointToRaster_conversion(BMPs, "CU_Eff_Ex", BMPCU, "MOST_FREQUENT", "NONE", "40")
            arcpy.PointToRaster_conversion(BMPs, "Zn_Eff_Ex", BMPZn, "MOST_FREQUENT", "NONE", "40")
            arcpy.PointToRaster_conversion(BMPs, "Sed_Eff_Ex", BMPSediment, "MOST_FREQUENT", "NONE", "40")



            demPath = "DEM"
            arcpy.env.extent = demPath
            arcpy.env.cellSize = demPath
            dem = Raster(demPath)
            fill = Fill(dem)
            flowDirection = FlowDirection(fill)
            flowAccN = FlowAccumulation(flowDirection,Raster_Nitrogen, "DOUBLE")
            flowAccP = FlowAccumulation(flowDirection,Raster_Phosphorus, "DOUBLE")
            flowAccN.save("C:/GIS/flowAccN.tif")
            flowAccP.save("C:/GIS/flowAccP.tif")
            flowAccSediment = FlowAccumulation(flowDirection,Raster_Sediment, "DOUBLE")
            flowAccCopper = FlowAccumulation(flowDirection,Raster_Copper, "DOUBLE")
            flowAccSediment.save("C:/GIS/flowAccSediment.tif")
            flowAccCopper.save("C:/GIS/flowAccCopper.tif")
            flowAccZn = FlowAccumulation(flowDirection,Raster_Zinc, "DOUBLE")
            flowAccFc = FlowAccumulation(flowDirection,Raster_Fecal, "DOUBLE")
            flowAccZn.save("C:/GIS/flowAccZn.tif")
            flowAccFc.save("C:/GIS/flowAccFc.tif")

            FlowAcc2_Nitrogen = FlowAccumulation(flowDirection,Raster_1_Nitrogen, "DOUBLE")
            FlowAcc2_Phosphorus = FlowAccumulation(flowDirection,Raster_1_Phosphorus, "DOUBLE")
            FlowAcc2_Sediment = FlowAccumulation(flowDirection,Raster_1_Sediment, "DOUBLE")
            FlowAcc2_Copper = FlowAccumulation(flowDirection,Raster_1_Copper, "DOUBLE")
            FlowAcc2_Zinc = FlowAccumulation(flowDirection,Raster_1_Zinc, "DOUBLE")
            FlowAcc2_Fecal = FlowAccumulation(flowDirection,Raster_1_Fecal, "DOUBLE")

            FlowAcc2_Nitrogen_BMP = FlowAccumulation(flowDirection, BMPN, "DOUBLE")
            FlowAcc2_Phosphorus_BMP = FlowAccumulation(flowDirection, BMPP, "DOUBLE")
            FlowAcc2_Sediment_BMP = FlowAccumulation(flowDirection, BMPSediment, "DOUBLE")
            FlowAcc2_Copper_BMP = FlowAccumulation(flowDirection, BMPCU, "DOUBLE")
            FlowAcc2_Zinc_BMP = FlowAccumulation(flowDirection, BMPZn, "DOUBLE")
            FlowAcc2_Fecal_BMP = FlowAccumulation(flowDirection, BMPFC, "DOUBLE")

            maxN = Minus(692.2000122070313,FlowAcc2_Nitrogen_BMP)
            maxP = Minus(1082.5,FlowAcc2_Phosphorus_BMP)
            maxSediment = Minus(2205.800048828125,FlowAcc2_Sediment_BMP)
            maxCopper = Minus(1074,FlowAcc2_Copper_BMP)
            maxZn = Minus(1382,FlowAcc2_Zinc_BMP)
            maxFc = Minus(1503,FlowAcc2_Fecal_BMP)

            BMPdiv_N = Divide(maxN, 692.2)
            BMPdiv_P = Divide(maxP, 1082.5)
            BMPdiv_Sediment = Divide(maxSediment, 2205.8)
            BMPdiv_Copper = Divide(maxCopper, 1074)
            BMPdiv_Zn = Divide(maxZn,1382)
            BMPdiv_fc = Divide(maxFc, 1503)

            futureN = Times(FlowAcc2_Nitrogen,BMPdiv_N)
            futureP = Times(FlowAcc2_Phosphorus.BMPdiv_P)
            futureSediment = Times(FlowAcc2_Sediment,BMPdiv_Sediment)
            futureZn = Times(FlowAcc2_Zinc, BMPdiv_Zn)
            futureCopper = Times(FlowAcc2_Copper, BMPdiv_Copper)
            futureFc = Times(FlowAcc2_Fecal, BMPdiv_fc)
            
            futureN.save("C:/GIS/futureN1.tif")
            futureP.save("C:/GIS/futureP1.tif")
            futureSediment.save("C:/GIS/futureSediment1.tif")
            futureZn.save("C:/GIS/futureZn1.tif")
            futureCopper.save("C:/GIS/futureCopper.tif")
            futureFc.save("C:/GIS/futureFc.tif")
            
            log("final")
            N = Con(IsNull(flowAccN),0,Divide(futureN, flowAccN))
            P= Con(IsNull(flowAccP),0,Divide(futureP, flowAccP))
            Sediment = Con(IsNull(flowAccSediment),0,Divide(futureSediment, flowAccSediment))
            Zn = Con(IsNull(flowAccZn),0,Divide(futureZn, flowAccZn))
            Copper = Con(IsNull(flowAccCopper),0,Divide(futureCopper, flowAccCopper))
            Fc = Con(IsNull(flowAccFc),0,Divide(futureFc, flowAccFc))
            N.save("C:/GIS/N.tif")
            P.save("C:/GIS/P.tif")
            Sediment.save("C:/GIS/Sediment.tif")
            Zn.save("C:/GIS/Zn1.tif")
            Copper.save("C:/GIS/Copper1.tif")
            Fc.save("C:/GIS/Fc1.tif")
            log("reclassify")
            maxN = 1146.4
            maxP = 3889
            maxSediment = 8749
            maxFc = 299.3
            maxZn = 3685
            maxCopper = 494
            Reclass_N = Reclassify(N, "Value", "0 %f NODATA;%f %f 1;%f %f 2;%f %f 3;%f %f 4" %(0.05*maxN, 0.05*maxN, 0.1 * maxN, 0.1 * maxN, 0.25 * maxN, 0.25 * maxN, 0.5 * maxN, 0.5 * maxN, maxN), "DATA")
            Reclass_P = Reclassify(P, "Value", "0 %f NODATA;%f %f 1;%f %f 2;%f %f 3;%f %f 4" %(0.05*maxP, 0.05*maxP, 0.1 * maxP, 0.1 * maxP, 0.25 * maxP, 0.25 * maxP, 0.5 * maxP, 0.5 * maxP, maxP), "DATA")
            Reclass_Sediment = Reclassify(Sediment, "Value", "0 %f NODATA;%f %f 1;%f %f 2;%f %f 3;%f %f 4" %(0.05*maxSediment, 0.05*maxSediment, 0.1 * maxSediment, 0.1 * maxSediment, 0.25 * maxSediment, 0.25 * maxSediment, 0.5 * maxSediment, 0.5 * maxSediment, maxSediment), "DATA")
            Reclass_Fc = Reclassify(Fc, "Value", "0 %f NODATA;%f %f 1;%f %f 2;%f %f 3;%f %f 4" %(0.05*maxFc, 0.05*maxFc, 0.1 * maxFc, 0.1 * maxFc, 0.25 * maxFc, 0.25 * maxFc, 0.5 * maxFc, 0.5 * maxFc, maxFc), "DATA")
            Reclass_Zn = Reclassify(Zn, "Value", "0 %f NODATA;%f %f 1;%f %f 2;%f %f 3;%f %f 4" %(0.05*maxZn, 0.05*maxZn, 0.1 * maxZn, 0.1 * maxZn, 0.25 * maxZn, 0.25 * maxZn, 0.5 * maxZn, 0.5 * maxZn, maxZn), "DATA")
            Reclass_Copper = Reclassify(Copper, "Value", "0 %f NODATA;%f %f 1;%f %f 2;%f %f 3;%f %f 4" %(0.05*maxCopper, 0.05*maxCopper, 0.1 * maxCopper, 0.1 * maxCopper, 0.25 * maxCopper, 0.25 * maxCopper, 0.5 * maxCopper, 0.5 * maxCopper, maxCopper), "DATA")
            Stream_N = "Stream_N"
            Stream_P = "Stream_P"
            Stream_Sediment = "Stream_Sediment"
            Stream_Fc = "Stream_Fc"
            Stream_Zn = "Stream_Zn"
            Stream_Copper = "Stream_Copper"
            log("stream to feature")
            arcpy.gp.StreamToFeature_sa(Reclass_N, flowDirection, Stream_N, "SIMPLIFY")
            arcpy.gp.StreamToFeature_sa(Reclass_P, flowDirection, Stream_P, "SIMPLIFY")
            arcpy.gp.StreamToFeature_sa(Reclass_Sediment, flowDirection, Stream_Sediment, "SIMPLIFY")
            arcpy.gp.StreamToFeature_sa(Reclass_Fc, flowDirection, Stream_Fc, "SIMPLIFY")
            arcpy.gp.StreamToFeature_sa(Reclass_Zn, flowDirection, Stream_Zn, "SIMPLIFY")
            arcpy.gp.StreamToFeature_sa(Reclass_Copper, flowDirection, Stream_Copper, "SIMPLIFY")

            StreamInvPts = "StreamInvPts"

            inRasterList = " 'C:/GIS/flowAccN1.tif' flowAccN; 'C:/GIS/flowAccP1.tif' flowAccP;'C:/GIS/flowAccSediment1.tif' flowAccSediment;'C:/GIS/flowAccCopper1.tif' flowAccCopper;'C:/GIS/flowAccZn1.tif' flowAccZn;'C:/GIS/flowAccFc1.tif' flowAccFc;'C:/GIS/futureSediment1.tif' futureSediment;'C:/GIS/futureFc1.tif' futureFc;'C:/GIS/futureN1.tif' futureN;'C:/GIS/futureCopper1.tif' futureCopper;'C:/GIS/futureP1.tif' futureP;'C:/GIS/futureZn1.tif' futureZn;"


            arcpy.gp.ExtractMultiValuesToPoints_sa(StreamInvPts, inRasterList, "NONE")

            arcpy.AddField_management("StreamInvPts", "N", "DOUBLE")
            arcpy.AddField_management("StreamInvPts", "P", "DOUBLE")
            arcpy.AddField_management("StreamInvPts", "Sediment", "DOUBLE")
            arcpy.AddField_management("StreamInvPts", "Copper", "DOUBLE")
            arcpy.AddField_management("StreamInvPts", "Fc", "DOUBLE")
            arcpy.AddField_management("StreamInvPts", "Zn", "DOUBLE")
            arcpy.SelectLayerByAttribute_management(StreamInvPts, "NEW_SELECTION", "flowAccN > 0")
            arcpy.CalculateField_management(StreamInvPts, "N", "[futureN] / [flowAccN]", "VB", "")

            arcpy.SelectLayerByAttribute_management(StreamInvPts, "NEW_SELECTION", "flowAccP > 0")
            arcpy.CalculateField_management(StreamInvPts, "P", "[futureP] / [flowAccP]", "VB", "")
            arcpy.SelectLayerByAttribute_management(StreamInvPts, "NEW_SELECTION", "flowAccCopper > 0")
            arcpy.CalculateField_management(StreamInvPts, "Copper", "[futureCopper] / [flowAccCopper]", "VB", "")
            arcpy.SelectLayerByAttribute_management(StreamInvPts, "NEW_SELECTION", "flowAccZn > 0")
            arcpy.CalculateField_management(StreamInvPts, "Zn", "[futureZn] / [flowAccZn]", "VB", "")

            arcpy.SelectLayerByAttribute_management(StreamInvPts, "NEW_SELECTION", "flowAccFc = 0")
            arcpy.SelectLayerByAttribute_management(StreamInvPts, "SWITCH_SELECTION", "")
            arcpy.CalculateField_management(StreamInvPts, "Fc", "[futureFc] / [flowAccFc]", "VB", "")
            arcpy.SelectLayerByAttribute_management(StreamInvPts, "NEW_SELECTION", "flowAccSediment > 0")
            arcpy.CalculateField_management(StreamInvPts, "Sediment", "[futureSediment] / [flowAccSediment]", "VB", "")

            arcpy.SelectLayerByAttribute_management(StreamInvPts, "CLEAR_SELECTION", "")



        except Exception as err:
            log(traceback.format_exc())
            log(err)
            raise err
        return


class task2analysis(object):
    def __init__(self):
        self.label = "Test"
        self.description = "Establishes the watershed and stream network"
        self.canRunInBackground = False
        
        arcpy.env.Workspace = self.Workspace = os.path.split(__file__)[0]
        log("Workspace = " + arcpy.env.Workspace)
        arcpy.env.overwriteOutput = True       

    def getParameterInfo(self):
        """Define parameter definitions"""
        
        param0 = arcpy.Parameter(
            displayName="BMP Points",
            name="bmppts",
            datatype="DEFeatureClass",
            parameterType="Required",
            direction="Input",
            multiValue=False)  
        
        param1 = arcpy.Parameter(
            displayName="Status Field",
            name="statusField",
            datatype="Field",
            parameterType="Required",
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
            BMPpath = parameters[0].valueAsText
            BMPs = "BMPs"
            status = parameters[1].valueAsText
            arcpy.MakeFeatureLayer_management(BMPpath, BMPs)
            arcpy.SelectLayerByAttribute_management(BMPs, "NEW_SELECTION", " %s = 'TRUE'" %status)
            arcpy.PointToRaster_conversion(BMPs, "TN_Eff_Ex", BMP_TN37, "MOST_FREQUENT", "NONE", "40")

            log("Parameter is %s" % (parameters[0].valueAsText))
            Lakes = "Lakes"
            LanduseExisting = "LanduseExisting"
            Impervious = "Impervious"
            BMPs = parameters[0].valueAsText
            inFeatures = [Lakes, LanduseExisting, Impervious]
            union = "union"
            
            arcpy.Union_analysis (inFeatures,union,"ALL", "", "GAPS")

            arcpy.AddField_management("union", "TotalNitrogen", "DOUBLE")
            arcpy.AddField_management("union", "TotalPhosphorus", "DOUBLE")
            arcpy.AddField_management("union", "Sediment", "DOUBLE")
            arcpy.AddField_management("union", "Copper", "DOUBLE")
            arcpy.AddField_management("union", "FecalColiform", "DOUBLE")
            arcpy.AddField_management("union", "Zinc", "DOUBLE")    

            arcpy.SelectLayerByAttribute_management(union, "NEW_SELECTION", "Reclassify = 'Roadways'")
            arcpy.CalculateField_management(union, "TotalNitrogen", "12.2", "VB", "")
            arcpy.CalculateField_management(union, "TotalPhosphorus", "1.8", "VB", "")
            arcpy.CalculateField_management(union, "Sediment", "405", "VB", "")
            arcpy.CalculateField_management(union, "Copper", "0", "VB", "")
            arcpy.CalculateField_management(union, "Zinc", "0.1", "VB", "")
            arcpy.CalculateField_management(union, "FecalColiform", "2.8", "VB", "")


            arcpy.SelectLayerByAttribute_management(union, "NEW_SELECTION", "Reclassify in ( 'Commercial' )")
            arcpy.CalculateField_management(union, "TotalNitrogen", "14", "VB", "")
            arcpy.CalculateField_management(union, "TotalPhosphorus", "2.7", "VB", "")
            arcpy.CalculateField_management(union, "Sediment", "400", "VB", "")
            arcpy.CalculateField_management(union, "Copper", "0", "VB", "")
            arcpy.CalculateField_management(union, "Zinc", "0", "VB", "")
            arcpy.CalculateField_management(union, "FecalColiform", "8.4", "VB", "")


            arcpy.SelectLayerByAttribute_management(union, "NEW_SELECTION", "Reclassify IN ( 'Industrial' )")
            arcpy.CalculateField_management(union, "TotalNitrogen", "10.4", "VB", "")
            arcpy.CalculateField_management(union, "TotalPhosphorus", "1.9", "VB", "")
            arcpy.CalculateField_management(union, "Sediment", "372.5", "VB", "")
            arcpy.CalculateField_management(union, "Copper", "0.2", "VB", "")
            arcpy.CalculateField_management(union, "Zinc", "0.1", "VB", "")
            arcpy.CalculateField_management(union, "FecalColiform", "8.4", "VB", "")

            arcpy.SelectLayerByAttribute_management(union, "NEW_SELECTION", "Reclassify in ( 'Institutional' , 'Research Triangle Park' )")
            arcpy.CalculateField_management(union, "TotalNitrogen", "9.4", "VB", "")
            arcpy.CalculateField_management(union, "TotalPhosphorus", "0.7", "VB", "")
            arcpy.CalculateField_management(union, "Sediment", "50", "VB", "")
            arcpy.CalculateField_management(union, "Copper", "0", "VB", "")
            arcpy.CalculateField_management(union, "Zinc", "0", "VB", "")
            arcpy.CalculateField_management(union, "FecalColiform", "14.8", "VB", "")

            arcpy.SelectLayerByAttribute_management(union, "NEW_SELECTION", "Reclassify IN ( 'Parks and Open Space' , 'Agricultural' )")
            arcpy.CalculateField_management(union, "TotalNitrogen", "2.3", "VB", "")
            arcpy.CalculateField_management(union, "TotalPhosphorus", "0.1", "VB", "")
            arcpy.CalculateField_management(union, "Sediment", "10", "VB", "")
            arcpy.CalculateField_management(union, "Copper", "0", "VB", "")
            arcpy.CalculateField_management(union, "Zinc", "0", "VB", "")
            arcpy.CalculateField_management(union, "FecalColiform", "12", "VB", "")

            arcpy.SelectLayerByAttribute_management(union, "NEW_SELECTION", "Reclassify IN ( 'High Density Residential' , 'Medium Density Residential' )")
            arcpy.CalculateField_management(union, "TotalNitrogen", "11.2", "VB", "")
            arcpy.CalculateField_management(union, "TotalPhosphorus", "1.6", "VB", "")
            arcpy.CalculateField_management(union, "Sediment", "242.5", "VB", "")
            arcpy.CalculateField_management(union, "Copper", "0", "VB", "")
            arcpy.CalculateField_management(union, "Zinc", "0", "VB", "")
            arcpy.CalculateField_management(union, "FecalColiform", "30.2", "VB", "")

            arcpy.SelectLayerByAttribute_management(union, "NEW_SELECTION", "Reclassify IN( 'Very Low Density Residential' , 'Low Density Residential' )")
            arcpy.CalculateField_management(union, "TotalNitrogen", "6.4", "VB", "")
            arcpy.CalculateField_management(union, "TotalPhosphorus", "0.7", "VB", "")
            arcpy.CalculateField_management(union, "Sediment", "150", "VB", "")
            arcpy.CalculateField_management(union, "Copper", "0", "VB", "")
            arcpy.CalculateField_management(union, "Zinc", "0", "VB", "")
            arcpy.CalculateField_management(union, "FecalColiform", "16.2", "VB", "")

            arcpy.SelectLayerByAttribute_management(union, "CLEAR_SELECTION", "")

            ##Future landuse
            LanduseFuture = "LanduseFuture"

            inFeatures1 = [Lakes, LanduseFuture, Impervious]
            union_1 = "union_1"
            arcpy.Union_analysis (inFeatures1,union_1,"ALL", "", "GAPS")
            arcpy.AddField_management("union_1", "TotalNitrogen", "DOUBLE")
            arcpy.AddField_management("union_1", "TotalPhosphorus", "DOUBLE")
            arcpy.AddField_management("union_1", "Sediment", "DOUBLE")
            arcpy.AddField_management("union_1", "Copper", "DOUBLE")
            arcpy.AddField_management("union_1", "Zinc", "DOUBLE")
            arcpy.AddField_management("union_1", "FecalColiform", "DOUBLE")

            arcpy.SelectLayerByAttribute_management(union_1, "NEW_SELECTION", "Reclassify = 'Roadways'")
            arcpy.CalculateField_management(union_1, "TotalNitrogen", "12.2", "VB", "")
            arcpy.CalculateField_management(union_1, "TotalPhosphorus", "1.8", "VB", "")
            arcpy.CalculateField_management(union_1, "Sediment", "405", "VB", "")
            arcpy.CalculateField_management(union_1, "Copper", "0", "VB", "")
            arcpy.CalculateField_management(union_1, "Zinc", "0.1", "VB", "")
            arcpy.CalculateField_management(union_1, "FecalColiform", "2.8", "VB", "")


            arcpy.SelectLayerByAttribute_management(union_1, "NEW_SELECTION", "Reclassify in ( 'Commercial' )")
            arcpy.CalculateField_management(union_1, "TotalNitrogen", "14", "VB", "")
            arcpy.CalculateField_management(union_1, "TotalPhosphorus", "2.7", "VB", "")
            arcpy.CalculateField_management(union_1, "Sediment", "400", "VB", "")
            arcpy.CalculateField_management(union_1, "Copper", "0", "VB", "")
            arcpy.CalculateField_management(union_1, "Zinc", "0", "VB", "")
            arcpy.CalculateField_management(union_1, "FecalColiform", "8.4", "VB", "")


            arcpy.SelectLayerByAttribute_management(union_1, "NEW_SELECTION", "Reclassify IN ( 'Industrial' )")
            arcpy.CalculateField_management(union_1, "TotalNitrogen", "10.4", "VB", "")
            arcpy.CalculateField_management(union_1, "TotalPhosphorus", "1.9", "VB", "")
            arcpy.CalculateField_management(union_1, "Sediment", "372.5", "VB", "")
            arcpy.CalculateField_management(union_1, "Copper", "0.2", "VB", "")
            arcpy.CalculateField_management(union_1, "Zinc", "0.1", "VB", "")
            arcpy.CalculateField_management(union_1, "FecalColiform", "8.4", "VB", "")

            arcpy.SelectLayerByAttribute_management(union_1, "NEW_SELECTION", "Reclassify in ( 'Institutional' , 'Research Triangle Park' )")
            arcpy.CalculateField_management(union_1, "TotalNitrogen", "9.4", "VB", "")
            arcpy.CalculateField_management(union_1, "TotalPhosphorus", "0.7", "VB", "")
            arcpy.CalculateField_management(union_1, "Sediment", "50", "VB", "")
            arcpy.CalculateField_management(union_1, "Copper", "0", "VB", "")
            arcpy.CalculateField_management(union_1, "Zinc", "0", "VB", "")
            arcpy.CalculateField_management(union_1, "FecalColiform", "14.8", "VB", "")

            arcpy.SelectLayerByAttribute_management(union_1, "NEW_SELECTION", "Reclassify IN ( 'Parks and Open Space' , 'Agricultural' )")
            arcpy.CalculateField_management(union_1, "TotalNitrogen", "2.3", "VB", "")
            arcpy.CalculateField_management(union_1, "TotalPhosphorus", "0.1", "VB", "")
            arcpy.CalculateField_management(union_1, "Sediment", "10", "VB", "")
            arcpy.CalculateField_management(union_1, "Copper", "0", "VB", "")
            arcpy.CalculateField_management(union_1, "Zinc", "0", "VB", "")
            arcpy.CalculateField_management(union_1, "FecalColiform", "12", "VB", "")

            arcpy.SelectLayerByAttribute_management(union_1, "NEW_SELECTION", "Reclassify IN ( 'High Density Residential' , 'Medium Density Residential' )")
            arcpy.CalculateField_management(union_1, "TotalNitrogen", "11.2", "VB", "")
            arcpy.CalculateField_management(union_1, "TotalPhosphorus", "1.6", "VB", "")
            arcpy.CalculateField_management(union_1, "Sediment", "242.5", "VB", "")
            arcpy.CalculateField_management(union_1, "Copper", "0", "VB", "")
            arcpy.CalculateField_management(union_1, "Zinc", "0", "VB", "")
            arcpy.CalculateField_management(union_1, "FecalColiform", "30.2", "VB", "")

            arcpy.SelectLayerByAttribute_management(union_1, "NEW_SELECTION", "Reclassify IN( 'Very Low Density Residential' , 'Low Density Residential' )")
            arcpy.CalculateField_management(union_1, "TotalNitrogen", "6.4", "VB", "")
            arcpy.CalculateField_management(union_1, "TotalPhosphorus", "0.7", "VB", "")
            arcpy.CalculateField_management(union_1, "Sediment", "150", "VB", "")
            arcpy.CalculateField_management(union_1, "Copper", "0", "VB", "")
            arcpy.CalculateField_management(union_1, "Zinc", "0", "VB", "")
            arcpy.CalculateField_management(union_1, "FecalColiform", "16.2", "VB", "")

            arcpy.SelectLayerByAttribute_management(union_1, "CLEAR_SELECTION", "")
           
            Raster_Nitrogen = "Raster_Nitrogen"
            Raster_Phosphorus = "Raster_Phosphorus"
            Raster_Sediment = "Raster_Sediment"
            Raster_Copper = "Raster_Copper"
            Raster_Zinc = "Raster_Zinc"
            Raster_Fecal = "Raster_Fecal"
            arcpy.PolygonToRaster_conversion(union, "TotalNitrogen", Raster_Nitrogen, "CELL_CENTER", "NONE", "40")
            arcpy.PolygonToRaster_conversion(union, "TotalPhosphorus", Raster_Phosphorus, "CELL_CENTER", "NONE", "40")
            arcpy.PolygonToRaster_conversion(union, "Sediment", Raster_Sediment, "CELL_CENTER", "NONE", "40")
            arcpy.PolygonToRaster_conversion(union, "Copper", Raster_Copper, "CELL_CENTER", "NONE", "40")
            arcpy.PolygonToRaster_conversion(union, "Zinc", Raster_Zinc, "CELL_CENTER", "NONE", "40")
            arcpy.PolygonToRaster_conversion(union, "FecalColiform", Raster_Fecal, "CELL_CENTER", "NONE", "40")

            Raster_1_Nitrogen = "Raster_1_Nitrogen"
            Raster_1_Phosphorus = "Raster_1_Phosphorus"
            Raster_1_Sediment = "Raster_1_Sediment"
            Raster_1_Copper = "Raster_1_Copper"
            Raster_1_Zinc = "Raster_1_Zinc"
            Raster_1_Fecal = "Raster_1_Fecal"

            arcpy.PolygonToRaster_conversion(union_1, "TotalNitrogen", Raster_1_Nitrogen, "CELL_CENTER", "NONE", "40")
            arcpy.PolygonToRaster_conversion(union_1, "TotalPhosphorus", Raster_1_Phosphorus, "CELL_CENTER", "NONE", "40")
            arcpy.PolygonToRaster_conversion(union_1, "Sediment", Raster_1_Sediment, "CELL_CENTER", "NONE", "40")
            arcpy.PolygonToRaster_conversion(union_1, "Copper", Raster_1_Copper, "CELL_CENTER", "NONE", "40")
            arcpy.PolygonToRaster_conversion(union_1, "Zinc", Raster_1_Zinc, "CELL_CENTER", "NONE", "40")
            arcpy.PolygonToRaster_conversion(union_1, "FecalColiform", Raster_1_Fecal, "CELL_CENTER", "NONE", "40")

            demPath = "DEM"
            dem = Raster(demPath)
            fill = Fill(dem)
            flowDirection = FlowDirection(fill)
            flowAccN = FlowAccumulation(flowDirection,Raster_Nitrogen, "DOUBLE")
            flowAccP = FlowAccumulation(flowDirection,Raster_Phosphorus, "DOUBLE")
            flowAccN.save("C:/GIS/flowAccN.tif")
            flowAccP.save("C:/GIS/flowAccP.tif")
            flowAccSediment = FlowAccumulation(flowDirection,Raster_Sediment, "DOUBLE")
            flowAccCopper = FlowAccumulation(flowDirection,Raster_Copper, "DOUBLE")
            flowAccSediment.save("C:/GIS/flowAccSediment.tif")
            flowAccCopper.save("C:/GIS/flowAccCopper.tif")
            flowAccZn = FlowAccumulation(flowDirection,Raster_Zinc, "DOUBLE")
            flowAccFc = FlowAccumulation(flowDirection,Raster_Fecal, "DOUBLE")
            flowAccZn.save("C:/GIS/flowAccZn.tif")
            flowAccFc.save("C:/GIS/flowAccFc.tif")

            FlowAcc2_Nitrogen = FlowAccumulation(flowDirection,Raster_1_Nitrogen, "DOUBLE")
            FlowAcc2_Phosphorus = FlowAccumulation(flowDirection,Raster_1_Phosphorus, "DOUBLE")
            FlowAcc2_Sediment = FlowAccumulation(flowDirection,Raster_1_Sediment, "DOUBLE")
            FlowAcc2_Copper = FlowAccumulation(flowDirection,Raster_1_Copper, "DOUBLE")
            FlowAcc2_Zinc = FlowAccumulation(flowDirection,Raster_1_Zinc, "DOUBLE")
            FlowAcc2_Fecal = FlowAccumulation(flowDirection,Raster_1_Fecal, "DOUBLE")


            BMPN = "BMPN"
            BMPP = "BMPP"
            BMPFC = "BMPFC"
            BMPCU = "BMPCU"
            BMPZn = "BMPZn"
            BMPSediment = "BMPSediment"

            BMPpath = parameters[0].valueAsText
            BMPs = "BMPs"
            status = parameters[1].valueAsText
            arcpy.MakeFeatureLayer_management(BMPpath, BMPs)
            arcpy.SelectLayerByAttribute_management(BMPs, "NEW_SELECTION", " %s = 'TRUE'" %status)
            arcpy.PointToRaster_conversion(BMPs, "TN_Eff_Ex", BMPN, "MOST_FREQUENT", "NONE", "40")
            arcpy.PointToRaster_conversion(BMPs, "TP_Eff_Ex", BMPP, "MOST_FREQUENT", "NONE", "40")
            arcpy.PointToRaster_conversion(BMPs, "FC_Eff_Ex", BMPFc, "MOST_FREQUENT", "NONE", "40")
            arcpy.PointToRaster_conversion(BMPs, "CU_Eff_Ex", BMPCopper, "MOST_FREQUENT", "NONE", "40")
            arcpy.PointToRaster_conversion(BMPs, "Zn_Eff_Ex", BMPZn, "MOST_FREQUENT", "NONE", "40")
            arcpy.PointToRaster_conversion(BMPs, "Sed_Eff_Ex", BMPSediment, "MOST_FREQUENT", "NONE", "40")

            FlowAcc2_Nitrogen_BMP = FlowAccumulation(flowDirection, BMPN, "DOUBLE")
            FlowAcc2_Phosphorus_BMP = FlowAccumulation(flowDirection, BMPP, "DOUBLE")
            FlowAcc2_Sediment_BMP = FlowAccumulation(flowDirection, BMPSediment, "DOUBLE")
            FlowAcc2_Copper_BMP = FlowAccumulation(flowDirection, BMPCopper, "DOUBLE")
            FlowAcc2_Zn_BMP = FlowAccumulation(flowDirection, BMPZn, "DOUBLE")
            FlowAcc2_Fc_BMP = FlowAccumulation(flowDirection, BMPFC, "DOUBLE")



            maxN = Minus(692.2,FlowAcc2_Nitrogen_BMP)
            maxP = Minus(1082.5,FlowAcc2_Phosphorus_BMP)
            maxSediment = Minus(2205.8,FlowAcc2_Sediment_BMP)
            maxFc = Minus(1503,FlowAcc2_FC_BMP)
            maxCopper = Minus(1074,FlowAcc2_Copper_BMP)
            maxZn = Minus(1382,FlowAcc2_ZN_BMP)

            BMPdiv_N = Divide(maxN, 692.2)
            BMPdiv_P = Divide(maxP, 1082.5)
            BMPdiv_Sediment = Divide(maxSediment, 2205.8)
            BMPdiv_Copper = Divide(maxCopper, 1074)
            BMPdiv_Zn = Divide(maxZn,1382)
            BMPdiv_fc = Divide(maxFc, 1503)

            futureN = Times(FlowAcc2_Nitrogen,BMPdiv_N)
            futureP = Times(FlowAcc2_Phosphorus.BMPdiv_P)
            futureSediment = Times(FlowAcc2_Sediment,BMPdiv_Sediment)
            futureZn = Times(FlowAcc2_Zinc, BMPdiv_Zn)
            futureCopper = Times(FlowAcc2_Copper, BMPdiv_Copper)
            futureFc = Times(FlowAcc2_Fecal, BMPdiv_fc)
            
            futureN.save("C:/GIS/futureN1.tif")
            futureP.save("C:/GIS/futureP1.tif")
            futureSediment.save("C:/GIS/futureSediment1.tif")
            futureZn.save("C:/GIS/futureZn1.tif")
            futureCopper.save("C:/GIS/futureCopper.tif")
            futureFc.save("C:/GIS/futureFc.tif")

            log("final")
            N = Con(IsNull(flowAccN),0,Divide(futureN, flowAccN))
            P= Con(IsNull(flowAccP),0,Divide(futureP, flowAccP))
            Sediment = Con(IsNull(flowAccSediment),0,Divide(futureSediment, flowAccSediment))
            Zn = Con(IsNull(flowAccZn),0,Divide(futureZn, flowAccZn))
            Copper = Con(IsNull(flowAccCopper),0,Divide(futureCopper, flowAccCopper))
            Fc = Con(IsNull(flowAccFc),0,Divide(futureFc, flowAccFc))
            N.save("C:/GIS/N.tif")
            P.save("C:/GIS/P.tif")
            Sediment.save("C:/GIS/Sediment.tif")
            Zn.save("C:/GIS/Zn1.tif")
            Copper.save("C:/GIS/Copper1.tif")
            Fc.save("C:/GIS/Fc1.tif")

            log("reclassify")
            maxN = 1146.4
            maxP = 3889
            maxSediment = 8749
            maxFc = 299.3
            maxZn = 3685
            maxCopper = 494
            Reclass_N = Reclassify(N, "Value", "0 %f NODATA;%f %f 1;%f %f 2;%f %f 3;%f %f 4" %(0.05*maxN, 0.05*maxN, 0.1 * maxN, 0.1 * maxN, 0.25 * maxN, 0.25 * maxN, 0.5 * maxN, 0.5 * maxN, maxN), "DATA")
            Reclass_P = Reclassify(P, "Value", "0 %f NODATA;%f %f 1;%f %f 2;%f %f 3;%f %f 4" %(0.05*maxP, 0.05*maxP, 0.1 * maxP, 0.1 * maxP, 0.25 * maxP, 0.25 * maxP, 0.5 * maxP, 0.5 * maxP, maxP), "DATA")
            Reclass_Sediment = Reclassify(Sediment, "Value", "0 %f NODATA;%f %f 1;%f %f 2;%f %f 3;%f %f 4" %(0.05*maxSediment, 0.05*maxSediment, 0.1 * maxSediment, 0.1 * maxSediment, 0.25 * maxSediment, 0.25 * maxSediment, 0.5 * maxSediment, 0.5 * maxSediment, maxSediment), "DATA")
            Reclass_Fc = Reclassify(Fc, "Value", "0 %f NODATA;%f %f 1;%f %f 2;%f %f 3;%f %f 4" %(0.05*maxFc, 0.05*maxFc, 0.1 * maxFc, 0.1 * maxFc, 0.25 * maxFc, 0.25 * maxFc, 0.5 * maxFc, 0.5 * maxFc, maxFc), "DATA")
            Reclass_Zn = Reclassify(Zn, "Value", "0 %f NODATA;%f %f 1;%f %f 2;%f %f 3;%f %f 4" %(0.05*maxZn, 0.05*maxZn, 0.1 * maxZn, 0.1 * maxZn, 0.25 * maxZn, 0.25 * maxZn, 0.5 * maxZn, 0.5 * maxZn, maxZn), "DATA")
            Reclass_Copper = Reclassify(Copper, "Value", "0 %f NODATA;%f %f 1;%f %f 2;%f %f 3;%f %f 4" %(0.05*maxCopper, 0.05*maxCopper, 0.1 * maxCopper, 0.1 * maxCopper, 0.25 * maxCopper, 0.25 * maxCopper, 0.5 * maxCopper, 0.5 * maxCopper, maxCopper), "DATA")
            Stream_N = "Stream_N"
            Stream_P = "Stream_P"
            Stream_Sediment = "Stream_Sediment"
            Stream_Fc = "Stream_Fc"
            Stream_Zn = "Stream_Zn"
            Stream_Copper = "Stream_Copper"

            log("stream to feature")
            arcpy.gp.StreamToFeature_sa(Reclass_N, flowDirection, Stream_N, "SIMPLIFY")
            arcpy.gp.StreamToFeature_sa(Reclass_P, flowDirection, Stream_P, "SIMPLIFY")
            arcpy.gp.StreamToFeature_sa(Reclass_Sediment, flowDirection, Stream_Sediment, "SIMPLIFY")
            arcpy.gp.StreamToFeature_sa(Reclass_Fc, flowDirection, Stream_Fc, "SIMPLIFY")
            arcpy.gp.StreamToFeature_sa(Reclass_Zn, flowDirection, Stream_Zn, "SIMPLIFY")
            arcpy.gp.StreamToFeature_sa(Reclass_Copper, flowDirection, Stream_Copper, "SIMPLIFY")

		
        except Exception as err:
            log(traceback.format_exc())
            log(err)
            raise err
        return
        
