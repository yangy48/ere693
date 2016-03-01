


# import library packages
import arcpy, os, sys, numpy

# get parameters (input and output datasets, filenames, etc)
# Flow_Direction = Raster(arcpy.getParameterAsText(0))
# BMP_Points     = Raster(arcpy.getParameterAsText(1))
# Output         = arcpy.getParameterAsText(2)
Flow_Direction = arcpy.Raster("C:/Users/csomerlot/Desktop/Lab05Data/Lab05Geodatabase.gdb/FlowDir_Fill1")
BMP_Points     = arcpy.Raster("C:/Users/csomerlot/Desktop/Lab05Data/Lab05Geodatabase.gdb/BMP_Points_PointToRaster")
Output         = "C:/Users/csomerlot/Desktop/Lab05Data/Lab05Geodatabase.gdb/output"

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
start = time.time()
print "Starting at %s" % (time.asctime())
count = 0
for R in range(1, height-1):
    if count in [1, 2, 5, 10, 15, 25, 50, 100, 200, 500, 1000, 1500, 2000]:
        print "Processing %i rows took %i seconds" % (count, (time.time()-start))
    count += 1
    for C in range(1, width-1):
        c = C
        r = R
        while 0 < r < height and 0 < c < width:
            bmpval = bmppointData[r][c]
            if bmpval < 0: bmpval = 0
            outputData[r][c] += (1-bmpval)
            flowdirval = flowdirData[r][c]
            if flowdirval == 1:
                c += 1
                r += 0
            if flowdirval == 2:
                c += 1
                r += 1
            if flowdirval == 4:
                c += 0
                r += 1
            if flowdirval == 8:
                c += -1
                r += 1
            if flowdirval == 16:
                c += -1
                r += 0
            if flowdirval == 32:
                c += -1
                r += -1
            if flowdirval == 64:
                c += 0
                r += -1
            if flowdirval == 128:
                c += 1
                r += -1
        
# save outputs
outputRaster = arcpy.NumPyArrayToRaster(outputData,lowerLeft,cellSize)
outputRaster.save(Output)
