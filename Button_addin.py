import arcpy
import pythonaddins
import os.path

class TopoHydro(object):
    """Implementation for Button_addin.button (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        try:
    # name of toolbox without tbx extension
            toolboxName = "Toolbox"

    # name of tool to be executed
            toolName = "TopoHydro"

    # create string with path to toolbox
            toolboxPath = os.path.join(os.path.dirname(__file__), toolboxName + ".pyt")

    # call geoprocessing tool
            pythonaddins.GPToolDialog(toolboxPath, toolName)
            #toolboxPath = os.path.join(os.path.dirname(_file_),"ToolboxCopy.pyt")
            #pythonaddins.GPToolDialog(toolboxPath,"TopoHydro")
        except TypeError:
            pass


class ImpCov(object):
    """Implementation for Button_addin.button_1 (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        try:
    # name of toolbox without tbx extension
            toolboxName = "Toolbox"

    # name of tool to be executed
            toolName = "ImpCov"

    # create string with path to toolbox
            toolboxPath = os.path.join(os.path.dirname(__file__), toolboxName + ".pyt")

    # call geoprocessing tool
            pythonaddins.GPToolDialog(toolboxPath, toolName)
        except TypeError:
            pass


class Runoff(object):
    """Implementation for Button_addin.button_2 (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        try:
    # name of toolbox without tbx extension
            toolboxName = "Toolbox"

    # name of tool to be executed
            toolName = "Runoff"

    # create string with path to toolbox
            toolboxPath = os.path.join(os.path.dirname(__file__), toolboxName + ".pyt")

    # call geoprocessing tool
            pythonaddins.GPToolDialog(toolboxPath, toolName)
 
        except TypeError:
            pass

class GetNEXRAD(object):
    """Implementation for Button_addin.button_3 (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        try:
    # name of toolbox without tbx extension
            toolboxName = "Toolbox"

    # name of tool to be executed
            toolName = "GetNEXRAD"

    # create string with path to toolbox
            toolboxPath = os.path.join(os.path.dirname(__file__), toolboxName + ".pyt")

    # call geoprocessing tool
            pythonaddins.GPToolDialog(toolboxPath, toolName)
            
        except TypeError:
            pass

        
class ScenarioAnalysis(object):
    """Implementation for Button_addin.button_4 (Button)"""
    def __init__(self):
        self.enabled = True
        self.checked = False
    def onClick(self):
        try:
    # name of toolbox without tbx extension
            toolboxName = "Toolbox"

    # name of tool to be executed
            toolName = "ScenarioAnalysis"

    # create string with path to toolbox
            toolboxPath = os.path.join(os.path.dirname(__file__), toolboxName + ".pyt")

    # call geoprocessing tool
            pythonaddins.GPToolDialog(toolboxPath, toolName)

        except TypeError:
            pass


