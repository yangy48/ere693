import arcpy
import pythonaddins

class createfishnet(object):
    """Implementation for New folder_addin.fishnettool (Tool)"""
    def __init__(self):
    self.enabled = True
    self.cursor = 3
    self.shape = 'Rectangle'
    
def onRectangle(self, rectangle_geometry):
    """Occurs when the rectangle is drawn and the mouse button is released.
    The rectangle is a extent object."""

    extent = rectangle_geometry
    # Create a fishnet with 10 rows and 10 columns.
    if arcpy.Exists(r'in_memory\fishnet'):
        arcpy.Delete_management(r'in_memory\fishnet')
    fishnet = arcpy.CreateFishnet_management(r'in_memory\fishnet',
                            '%f %f' %(extent.XMin, extent.YMin),
                            '%f %f' %(extent.XMin, extent.YMax),
                            0, 0, 10, 10,
                            '%f %f' %(extent.XMax, extent.YMax),'NO_LABELS',
                            '%f %f %f %f' %(extent.XMin, extent.YMin, extent.XMax, extent.YMax), 'POLYGON')
    arcpy.RefreshActiveView()
    return fishnet

class createfishnet2(object):
    """Implementation for New folder_addin.fishnettool2 (Tool)"""
    def __init__(self):
    self.enabled = True
    self.cursor = 3
    self.shape = 'Rectangle'
    
def onRectangle(self, rectangle_geometry):
    """Occurs when the rectangle is drawn and the mouse button is released.
    The rectangle is a extent object."""

    extent = rectangle_geometry
    # Create a fishnet with 20 rows and 20 columns.
    if arcpy.Exists(r'in_memory\fishnet'):
        arcpy.Delete_management(r'in_memory\fishnet')
    fishnet = arcpy.CreateFishnet_management(r'in_memory\fishnet',
                            '%f %f' %(extent.XMin, extent.YMin),
                            '%f %f' %(extent.XMin, extent.YMax),
                            0, 0, 20, 20,
                            '%f %f' %(extent.XMax, extent.YMax),'NO_LABELS',
                            '%f %f %f %f' %(extent.XMin, extent.YMin, extent.XMax, extent.YMax), 'POLYGON')
    arcpy.RefreshActiveView()
    return fishnet
