# -*- coding: utf-8 -*-
"""
Created on Sun Oct 24 16:49:37 2021

@author: alpha
"""

import napari, os
from magicgui import magic_factory
from napari_plugin_engine import napari_hook_implementation
from .h5layer import layerH5
import dask.array as da


# @magic_factory(auto_call=False,call_button="update",
#                contrast_lower={'min': 0,'max': 65534},
#                contrast_upper={'min': 0,'max': 65534}
#                )
# def threshold(
#     viewer: napari.Viewer,
#     contrast_lower: int,
#     contrast_upper: int
# ):
    
#     print(vars(viewer.layers['Channel 1']))
#     for idx in viewer.layers:
#         viewer.layers[str(idx)].contrast_limits = [contrast_lower,contrast_upper]

@magic_factory(auto_call=False, threshold={'max': 65534})
def threshold(
        fileName: str,
        data: 'napari.types.ImageData', 
        threshold: int
) -> 'napari.types.LayerDataTuple':
    
    filePrefix, fileExt = os.path.splitext(fileName)
    newData = []
    for idx,dd in enumerate(data):
        newData.append(layerH5(filePrefix+str(idx)+fileExt,
                               shape=data[idx].shape,
                               dtype=data[idx].dtype,
                               compress=True)
                       )
        # newData[idx] = da.from_array(newData[idx],chunks=[1]*(len(newData[idx].shape)-2) + [1024,1024])

    return ([(x > threshold).astype(int) for x in data], {'name':fileName,
                                             'multiscale':True}, 'labels')

@napari_hook_implementation
def napari_experimental_provide_dock_widget():
    return threshold

