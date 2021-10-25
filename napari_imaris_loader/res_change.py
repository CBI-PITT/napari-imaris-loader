# -*- coding: utf-8 -*-
"""
Created on Sun Oct 24 16:49:37 2021

@author: alpha
"""

import napari, os
from magicgui import magic_factory
from napari_plugin_engine import napari_hook_implementation
# from .h5layer import layerH5
from .reader import ims_reader
import dask.array as da



@magic_factory(auto_call=False,call_button="update",
                resolution_level={'min': 0,'max': 9}
                )
def res_change(
    viewer: napari.Viewer,
    resolution_level: int
) -> 'napari.types.LayerDataTuple':
    
    for idx in viewer.layers:
        tupleOut = ims_reader(
            viewer.layers[str(idx)].metadata['fileName'],
            resLevel=resolution_level
            )
        break
    
    # tupleOut = tupleOut[0]
    # for dd in tupleOut[0]:
        
    
    return tupleOut[0]
    
    # for idx in viewer.layers:
    #     print(viewer.layers[str(idx)].metadata)
    #     print(viewer.layers[str(idx)].metadata['fileName'])
    #     print(viewer.layers[str(idx)].metadata['resolutionLevels'])
        
        # print(viewer.layers[str(idx)].data)
        # newData = viewer.layers[str(idx)].data
        # # newData = newData[:resolution_level]
        # newData = newData[0]
        # viewer.layers[str(idx)].data = newData



# @magic_factory(auto_call=False,call_button="update",
#                 resolution_level={'min': 0,'max': 9}
#                 )
# def res_change(
#     viewer: napari.Viewer,
#     resolution_level: int
# ):
    
#     for idx in viewer.layers:
#         print(viewer.layers[str(idx)].metadata)
#         print(viewer.layers[str(idx)].metadata['fileName'])
#         print(viewer.layers[str(idx)].metadata['resolutionLevels'])
        
#         # print(viewer.layers[str(idx)].data)
#         # newData = viewer.layers[str(idx)].data
#         # # newData = newData[:resolution_level]
#         # newData = newData[0]
#         # viewer.layers[str(idx)].data = newData




# @magic_factory(auto_call=False, threshold={'max': 65534})
# def threshold(
#         fileName: str,
#         data: 'napari.types.ImageData', 
#         threshold: int
# ) -> 'napari.types.LayerDataTuple':
    
#     filePrefix, fileExt = os.path.splitext(fileName)
#     newData = []
#     for idx,dd in enumerate(data):
#         newData.append(layerH5(filePrefix+str(idx)+fileExt,
#                                shape=data[idx].shape,
#                                dtype=data[idx].dtype,
#                                compress=True)
#                        )
#         # newData[idx] = da.from_array(newData[idx],chunks=[1]*(len(newData[idx].shape)-2) + [1024,1024])

#     return ([(x > threshold).astype(int) for x in data], {'name':fileName,
#                                              'multiscale':True}, 'labels')

@napari_hook_implementation
def napari_experimental_provide_dock_widget():
    return res_change

