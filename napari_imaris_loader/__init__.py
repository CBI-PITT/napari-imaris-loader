
try:
    from ._version import version as __version__
except ImportError:
    __version__ = "unknown"



#from ._reader import napari_get_reader
from .reader import napari_get_reader
#from .controls import napari_experimental_provide_dock_widget
from .resolution_change_widget import napari_experimental_provide_dock_widget



