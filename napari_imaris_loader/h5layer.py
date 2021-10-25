# -*- coding: utf-8 -*-
"""
Created on Sun Oct 24 21:54:33 2021

@author: alpha
"""

import h5py, os
import numpy as np

class layerH5:
    def __init__(self, fileName, shape, dtype=np.uint8, compress=True):
        self.fileName = fileName
        self.filePrefix, self.fileExt = os.path.splitext(self.fileName)
        self.shape = shape
        self.ndim = len(self.shape)
        self.dtype = dtype
        
        self.exists = os.path.exists(fileName)
        if self.exists == False:
            with h5py.File(fileName,'w') as hf:
                hf.create_dataset('layer1',
                                  shape=shape,
                                  dtype=np.uint8,
                                  # chunks=tuple([1]*(len(self.shape)-2) + [1024.1204]),
                                   chunks=True,
                                  compression='lzf' if compress==True else None
                                  )
            self.exists = True
        
    def __getitem__(self, key):
        with h5py.File(self.fileName,'a') as hf:
            return hf['layer1'][key]
    
    def __setitem__(self, key, newValue):
        with h5py.File(self.fileName,'a') as hf:
            hf['layer1'][key] = newValue
    