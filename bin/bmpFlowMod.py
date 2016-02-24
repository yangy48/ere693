


# import library packages
import arcpy, os, sys, numpy

# get parameters (input and output datasets, filenames, etc)
# Flow_Direction = Raster(arcpy.getParameterAsText(0))
# BMP_Points     = Raster(arcpy.getParameterAsText(1))
# Output         = arcpy.getParameterAsText(2)
Flow_Direction = arcpy.Raster("C:/Users/csomerlot/Desktop/Lab05Data/Lab05Geodatabase.gdb/FlowDir_Fill1")
BMP_Points     = arcpy.Raster("C:/Users/csomerlot/Desktop/Lab05Data/Lab05Geodatabase.gdb/BMP_Points_PointToRaster")
Output         = "C:/Users/csomerlot/Desktop/Lab04Data/Lab04Data.gdb/output"

# set environment 

# create variables to hold input and output datasets
flowdirData = arcpy.RasterToNumPyArray(Flow_Direction)
lowerLeft = arcpy.Point(Flow_Direction.extent.XMin,Flow_Direction.extent.YMin)
cellSize  = Flow_Direction.meanCellWidth
height = len(flowdirData)
width = len(flowdirData[0])

bmppointData = arcpy.RasterToNumPyArray(BMP_Points)
if BMP_Points.extent.XMin != Flow_Direction.extent.XMin:
    print BMP_Points.extent.XMin, Flow_Direction.extent.XMin
    raise Exception("Xmin of extents not the same")
if BMP_Points.extent.YMin != Flow_Direction.extent.YMin: raise Exception("YMin of extents are not the same") 
if BMP_Points.meanCellWidth != Flow_Direction.meanCellWidth: raise Exception("Cell sizes are not the same")
if len(bmppointData) != height:
    print len(bmppointData[0]), height, width
    raise Exception("Heights are not the same")
if len(bmppointData[0]) != width: raise Exception("Widths are not the same")
   
outputData = numpy.empty([height, width], dtype=float)

# process (loop through) datasets

for R in range(1, height-1):
    for C in range(1, width-1):
        position = [R,C]
        while 0 < position[0] < height and 0 < position[1] < width:
            bmpval = bmppointData[position[0]][position[1]]
            if bmpval < 0: bmpval = 0
            outputData[position[0]][position[1]] += (1-bmpval)
            flowdirval = flowdirData[position[0]][position[1]]
            if flowdirval == 1:
                position[0] += 1
                position[1] += 0
            if flowdirval == 2:
                position[0] += 1
                position[1] += -1
            if flowdirval == 4:
                position[0] += 0
                position[1] += -1
            if flowdirval == 8:
                position[0] += -1
                position[1] += -1
            if flowdirval == 16:
                position[0] += -1
                position[1] += 0
            if flowdirval == 32:
                position[0] += -1
                position[1] += 1
            if flowdirval == 64:
                position[0] += 0
                position[1] += 1
            if flowdirval == 128:
                position[0] += 1
                position[1] += 1
        
# save outputs
outputRaster = arcpy.NumPyArrayToRaster(outputData,lowerLeft,cellSize)
outputRaster.save(Output)
