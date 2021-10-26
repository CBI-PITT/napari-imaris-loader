# -*- coding: utf-8 -*-
"""
Created on Tue Apr 27 20:40:39 2021

@author:AlanMWatson

Napari plugin for reading imaris files as a multiresolution series.
    
NOTE:  Currently "File/Preferences/Render Images Asynchronously" must be turned on for this plugin to work

*** Issues remain with indexing and the shape of returned arrays.  
 1) It is unclear if there is an issue with how I am implementing slicing in the ims module
 2) Different expections from napari on the state of the data that is returned between the Image and Chunk_loader methods in ims module

** It appears that napari is only requesting 2D (YX) chunks from the loader during 2D rendering 
which limits the utility of the async chunk_loader.  

*Future implemetation of caching in RAM and persistantly on disk is planned via ims module - currently disabled
RAM Cache may be redundant to napari cache unless we can implement 3D chunk caching
Disk cache may allow for loaded chunks to be stored to SSD for rapid future retrieval
with options to maintain this cache persistantly accross sessions.
"""

import os
from .ims import ims
import numpy as np
import dask.array as da
# from dask import delayed
# from dask.cache import Cache

from napari_plugin_engine import napari_hook_implementation



    
"""
Is this a bug in napari or specific to this reader?

path = "...\napari-env\Lib\site-packages\napari\layers\image\image.py"
Line 619-620
should read:
indices[d] = slice(
                    int(self.corner_pixels[0, d]),
                    int(self.corner_pixels[1, d] + 1),
                    1,
                    )

start/stop values of the slice must be coerced to int otherwise an error
is thrown when switching from 3D to 2D view

"""
    


def ims_reader(path,resLevel='max', colorsIndependant=False, preCache=False):
    
    # path = r"Z:\testData\bitplaneConverter.ims"  ## Dataset for testing
    #print('I AM IN THE READER')
    
    imsClass = ims(path)
   
    if imsClass.dtype==np.dtype('uint16'):
        contrastLimits = [0,65534]
    elif imsClass.dtype==np.dtype('uint8'):
        contrastLimits = [0,254]
    elif imsClass.dtype==np.dtype('float'):
        contrastLimits = [0,1]
    
    
    ## Enable async loading of tiles
    os.environ["NAPARI_ASYNC"] = "1"
    # os.environ['NAPARI_OCTREE'] = "1"
    
    
    
    # cache = Cache(10e9)  # Leverage two gigabytes of memory
    # cache.register()    # Turn cache on globally
    
    ## Extract Voxel Spacing
    scale = imsClass.resolution
    scale = [x/scale[-1] for x in scale]
    scale = [tuple(scale)]*imsClass.Channels
    print(scale)
    
    ## Display current Channel Names
    channelNames = []
    for cc in range(imsClass.Channels):
        channelNames.append('Channel {}'.format(cc))
        
    
    data = []
    for rr in range(imsClass.ResolutionLevels):
        print('Loading resolution level {}'.format(rr))
        data.append(ims(path,ResolutionLevelLock=rr,cache_location=imsClass.cache_location))
        
    
    chunks = True
    for idx,_ in enumerate(data):
        data[idx] = da.from_array(data[idx],
                                  chunks=data[idx].chunks if chunks == True else (1,1,data[idx].shape[-3],data[idx].shape[-2],data[idx].shape[-1]),
                                  fancy=False
                                  )
    
    
    # Base metadata that apply to all senarios
    meta = {
        "scale": scale,
        "contrast_limits": contrastLimits,
        "name": channelNames,
        "metadata": {'fileName':imsClass.filePathComplete,
                     'resolutionLevels':imsClass.ResolutionLevels
                     }
        }
    
    # Reslice to remove dangling single dimensions
    inwardSlice = 0
    for ii in range(len(imsClass.shape)):
        if imsClass.shape[ii] == 1:
            inwardSlice += 1
    
    if inwardSlice == 0:
        for idx,_ in enumerate(data):
            meta['channel_axis'] = 1
    elif inwardSlice == 1:
        for idx,_ in enumerate(data):
            data[idx] = data[idx][0]
            meta['channel_axis'] = 0
    elif inwardSlice == 2:
        for idx,_ in enumerate(data):
            data[idx] = data[idx][0,0]
    elif inwardSlice == 3:
        for idx,_ in enumerate(data):
            data[idx] = data[idx][0,0,0]
    elif inwardSlice == 4:
        for idx,_ in enumerate(data):
            data[idx] = data[idx][0,0,0,0]
    
    ## Possibility of implementing rapid caching of some data (lower resolution levels?) prior to visualization.
    ## done by calling a simple calculation over the whole dask array da.min()?
    # if preCache == True:
    #     for idx,dd in enumerate(reversed(data)):
    #         print('Caching resolution level {}'.format(len(data)-idx-1))
    #         for ii in range(imsClass.Channels):
    #             dd[0,ii].min().compute()
    #         if idx == 2:
    #             break

    # Option to cut off lower resolutions to improve 3D rendering
    # May provide a widgit that can impletment this after the dataset is loaded
    data = data if resLevel=='max' else data[:resLevel]
    
    # Set multiscale based on whether multiple resolutions are present
    meta["multiscale"] = True if len(data) > 1 else False

    if colorsIndependant and 'channel_axis' in meta:
        channelAxis = meta['channel_axis']
        
        channelData = []
        for cc in range(data[0].shape[channelAxis]):
            singleChannel = []
            for dd in data:
                if channelAxis == 0:
                    singleChannel.append(dd[cc])
                elif channelAxis == 1:
                    singleChannel.append(dd[:,cc])
            channelData.append(singleChannel)
                    
        del(meta['channel_axis'])
        
        metaData = []
        for cc in range(data[0].shape[channelAxis]):
            singleChannel = {
                'contrast_limits':meta['contrast_limits'],
                'multiscale':meta['multiscale'],
                'metadata':meta['metadata'],
                'scale':meta['scale'][cc],
                'name':meta['name'][cc]
                             }
            metaData.append(singleChannel)
        
        finalOutput = []
        for dd,mm in zip(channelData,metaData):
            finalOutput.append(
                (dd,mm)
                )
        return finalOutput
    
    
    else:
        return [(data,meta)]
        



@napari_hook_implementation
def napari_get_reader(path):
    if isinstance(path,str) and os.path.splitext(path)[1].lower() == '.ims':
        return ims_reader



                