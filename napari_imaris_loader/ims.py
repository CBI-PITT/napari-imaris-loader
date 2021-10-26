# -*- coding: utf-8 -*-
"""
Created on Sun Oct 24 10:49:36 2021

@author: alpha
"""

import os, sys, glob, itertools, functools, pickle, shutil, random #, hashlib
import numpy as np
# from functools import lru_cache
from psutil import virtual_memory
import h5py

class ims:
    def __init__(self, file, ResolutionLevelLock=None, cache_location=None, mem_size=20, disk_size=2000):
        
        ##  mem_size = in gigabytes that remain FREE as cache fills
        ##  disk_size = in gigabytes that remain FREE as cache fills
        self.filePathComplete = file
        self.filePathBase = os.path.split(file)[0]
        self.fileName = os.path.split(file)[1]
        self.fileExtension = os.path.splitext(self.fileName)[1]
        if cache_location == None and mem_size == None:
            self.cache = None
        else:
            self.cache = True
        self.cache_location = cache_location
        self.disk_size = disk_size * 1e9
        self.mem_size = mem_size * 1e9
        self.memCache = {}
        self.cacheFiles = []
        self.metaData = {}
        self.ResolutionLevelLock = ResolutionLevelLock
        
        with h5py.File(file, 'r') as hf:
            # hf = h5py.File(file, 'r')
            dataSet = hf['DataSet']
            R0 = dataSet['ResolutionLevel 0']
            T0 = R0['TimePoint 0']
            C0 = T0['Channel 0']
            data = C0['Data']
            
            self.ResolutionLevels = len(dataSet)
            self.TimePoints = len(R0)
            self.Channels = len(T0)
            
            self.resolution = (round(float(readAttribute(self, 'DataSetInfo/Image', 'ExtMax2')) / float(readAttribute(self, 'DataSetInfo/Image', 'Z')),3),\
                                   round(float(readAttribute(self, 'DataSetInfo/Image', 'ExtMax1')) / float(readAttribute(self, 'DataSetInfo/Image', 'Y')),3),\
                                       round(float(readAttribute(self, 'DataSetInfo/Image', 'ExtMax0')) / float(readAttribute(self, 'DataSetInfo/Image', 'X')),3))
            
            
            # print(self.resolution)
            self.shape = (self.TimePoints,
                          self.Channels,
                          int(readAttribute(self, 'DataSetInfo/Image', 'Z')),\
                                       int(readAttribute(self, 'DataSetInfo/Image', 'Y')),\
                                        int(readAttribute(self, 'DataSetInfo/Image', 'X')))
            
            self.chunks = (1,1,data.chunks[0],data.chunks[1],data.chunks[2])
            self.ndim = len(self.shape)
            self.dtype = data.dtype
            self.shapeH5Array = data.shape
                
            for r,t,c in itertools.product(range(self.ResolutionLevels), range(self.TimePoints), range(self.Channels)):
                
                locationAttrib = locationGenerator(r,t,c,data='attrib')
                locationData = locationGenerator(r,t,c,data='data')
                
                # print(locationAttrib)
                # print(locationData)
                
                # Collect attribute info
                self.metaData[r,t,c,'shape'] = (t+1,
                                                c+1,
                                                int(readAttribute(self, locationAttrib, 'ImageSizeZ')),\
                                       int(readAttribute(self, locationAttrib, 'ImageSizeY')),\
                                        int(readAttribute(self, locationAttrib, 'ImageSizeX'))
                                           )
                self.metaData[r,t,c,'resolution'] = tuple([round(float((origShape/newShape)*origRes),3) for origRes, origShape, newShape in zip(self.resolution,self.shape[-3:],self.metaData[r,t,c,'shape'][-3:])])
                self.metaData[r,t,c,'HistogramMax'] = int(float(readAttribute(self, locationAttrib, 'HistogramMax')))
                self.metaData[r,t,c,'HistogramMin'] = int(float(readAttribute(self, locationAttrib, 'HistogramMin')))
                
                # Collect dataset info
                self.metaData[r,t,c,'chunks'] = (1,1,hf[locationData].chunks[0],hf[locationData].chunks[1],hf[locationData].chunks[2])
                self.metaData[r,t,c,'shapeH5Array'] = hf[locationData].shape
                self.metaData[r,t,c,'dtype'] = hf[locationData].dtype
                
                
        if isinstance(self.ResolutionLevelLock, int):
            self.shape = self.metaData[self.ResolutionLevelLock,t,c,'shape']
            self.ndim = len(self.shape)
            self.chunks = self.metaData[self.ResolutionLevelLock,t,c,'chunks']
            self.shapeH5Array = self.metaData[self.ResolutionLevelLock,t,c,'shapeH5Array']
            self.resolution = self.metaData[self.ResolutionLevelLock,t,c,'resolution']
            self.dtype = self.metaData[self.ResolutionLevelLock,t,c,'dtype']
            
            ##  Should define a method to change the ResolutionLevelLock after class in initialized
                    
        # print(self.metaData)
                
    def __getitem__(self, key):
        # print(key)
        
        '''
        All ims class objects are represented as shape (TCZYX)
        An integer only slice will return the entire timepoint (T) data as a numpy array
        
        Any other variation on slice will be coerced to 5 dimensions and 
        extract that array
        
        If a 6th dimentions is present in the slice, dim[0] is assumed to be the resolutionLevel
        this will be used when choosing which array to extract.  Otherwise ResolutionLevelLock
        will be obeyed.  If ResolutionLevelLock is == None - default resolution is 0 (full-res)
        and a slice of 5 or less dimentions will extract information from resolutionLevel 0.
        
        ResolutionLevelLock is used when building a multiresolution series to load into napari
        This option enables a 5D slice to lock on to a specified resolution level.
        '''
        
        origionalKey = key
        res = self.ResolutionLevelLock
        
        if isinstance(key,slice) == False and isinstance(key,int) == False and len(key) == 6:
            res = key[0]
            if res >= self.ResolutionLevels:
                raise ValueError('Layer is larger than the number of ResolutionLevels')
            key = tuple([x for x in key[1::]])
        
        ## All slices will be converted to 5 dims and placed into a tuple
        if isinstance(key,slice):
            key = [key]
        
        if isinstance(key, int):
            key = [slice(key)]
        
        ## Convert int/slice mix to a tuple of slices
        elif isinstance(key,tuple):
            key = tuple([slice(x) if isinstance(x,int) else x for x in key])
            
        key = list(key)
        while len(key) < 5:
            key.append(slice(None))
        key = tuple(key)
        

                
        # if self.cache == None:
        #     return getSlice(
        #         self, 
        #         r = res if res is not None else 0,
        #         t = sliceFixer(self,key[0],'t',res=res),
        #         c = sliceFixer(self,key[1],'c',res=res),
        #         z = sliceFixer(self,key[2],'z',res=res),
        #         y = sliceFixer(self,key[3],'y',res=res), 
        #         x = sliceFixer(self,key[4],'x',res=res)
        #         )
        # else:
        #     return cache(location=self.cache_location,mem_size=self.mem_size,disk_size=self.disk_size)(getSlice)(
        #         self, 
        #         r = res if res is not None else 0,
        #         t = sliceFixer(self,key[0],'t',res=res),
        #         c = sliceFixer(self,key[1],'c',res=res),
        #         z = sliceFixer(self,key[2],'z',res=res),
        #         y = sliceFixer(self,key[3],'y',res=res), 
        #         x = sliceFixer(self,key[4],'x',res=res)
        #         )
        
        sliceReturned = getSlice(
                self, 
                r = res if res is not None else 0, #Force ResolutionLock of None to be 0 when slicing
                t = sliceFixer(self,key[0],'t',res=res),
                c = sliceFixer(self,key[1],'c',res=res),
                z = sliceFixer(self,key[2],'z',res=res),
                y = sliceFixer(self,key[3],'y',res=res), 
                x = sliceFixer(self,key[4],'x',res=res)
                )
        print('Image Slices Requested: {} / Item shape returned: {} \n'.format(origionalKey,sliceReturned.shape))
        return sliceReturned
    
    

def sliceFixer(self,sliceObj,dim,res):
    '''
    Converts slice.stop == None to the origional image dims
    dim = dimension.  should be str: r,t,c,z,y,x
    
    Always returns a fully filled slice object (ie NO None)
    
    Negative slice values are not implemented yet self[:-5]
    
    Slicing with lists (fancy) is not implemented yet self[[1,2,3]]
    '''
    

    if res == None:
        res = 0
    
    dims = {'r':self.ResolutionLevels,
            't':self.TimePoints,
            'c':self.Channels,
            'z':self.metaData[(res,0,0,'shape')][-3],
            'y':self.metaData[(res,0,0,'shape')][-2],
            'x':self.metaData[(res,0,0,'shape')][-1]
            }
    
    if (sliceObj.stop is not None) and (sliceObj.stop > dims[dim]):
        raise ValueError('The specified stop dimension "{}" in larger than the dimensions of the \
                         origional image'.format(dim))
    if (sliceObj.start is not None) and (sliceObj.start > dims[dim]):
        raise ValueError('The specified start dimension "{}" in larger than the dimensions of the \
                         origional image'.format(dim))
    
    if isinstance(sliceObj.stop,int) and sliceObj.start == None and sliceObj.step == None:
        return slice(
            sliceObj.stop,
            sliceObj.stop+1,
            1 if sliceObj.step is None else sliceObj.step
            )
    
    if sliceObj == slice(None):
        return slice(0,dims[dim],1)
    
    if sliceObj.step == None:
        sliceObj = slice(sliceObj.start,sliceObj.stop,1)
    
    if sliceObj.stop == None:
        sliceObj = slice(
            sliceObj.start,
            dims[dim],
            sliceObj.step
            )
    
    ##  Need to reevaluate if this last statement is still required
    if isinstance(sliceObj.stop,int) and sliceObj.start == None:
        sliceObj = slice(
            max(0,sliceObj.stop-1),
            sliceObj.stop,
            sliceObj.step
            )
    
    # print(sliceObj)
    return sliceObj


##########################################################################################

def locationGenerator(r,t,c,data='data'):
    """
    Given R, T, C, this funtion will generate a path to data in an imaris file
    default data == 'data' the path will reference with array of data
    if data == 'attrib' the bath will reference the channel location where attributes are stored
    """
    
    location = 'DataSet/ResolutionLevel {}/TimePoint {}/Channel {}'.format(r,t,c)
    if data == 'data':
        location = location + '/Data'
    return location
        
def readAttribute(imsClass, location, attrib):
    ''' Location should be specified as a path:  for example
    'DataSet/ResolutionLevel 0/TimePoint 0/Channel 1'
    
    attrib is a string that defines the attribute to extract: for example
    'ImageSizeX'
    '''
    with h5py.File(imsClass.filePathComplete, 'r') as hf:
            return str(hf[location].attrs[attrib], encoding='ascii')



def getCacheSize(cacheLocation):
    '''
    This can be very slow for a cache with LARGE numbers of files.
    '''
    return sum(([os.path.getsize(d) for d in glob.glob(os.path.join(cacheLocation,'*','*','*'))]))

def getCacheFiles(cacheLocation):
    '''
    This can be very slow for a cache with LARGE numbers of files.
    '''
    return glob.glob(os.path.join(cacheLocation,'*','*','*'))

def getRandomCacheFile(cacheLocation):
    '''
    This will choose a random file in the disk cache
    '''
    level1 = glob.glob(os.path.join(cacheLocation,'*'))
    level2 = glob.glob(os.path.join(random.choice(level1),'*'))
    level3 = glob.glob(os.path.join(random.choice(level2),'*'))
    return random.choice(level3)
    

def diskCacheFreeSpace(location):
    total, used, free = shutil.disk_usage(location)
    return free

def memCacheFreeSpace():
    z = virtual_memory()
    return z.available

def cacheFileNameGen(location, fhash):
    return os.path.join(location,fhash[0:2],fhash[2:4],fhash)
    
def saveCacheFile(fname,toPickle):
    with open(fname,'wb') as f:
        # print('Saving to cache')
        pickle.dump(toPickle,f)

def cache(location=None,mem_size=1e9,disk_size=1e9):


    def actual_decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            
            fname = '{}|{}|{}|{}'.format(func.__name__,
                                      ','.join(args[0].filePathComplete),
                                      ','.join(map(str,args[1::])), #args[2::] because 0 is filepath and 1 is a h5py object that will chance with each round
                                      ','.join(map(lambda it: '{}:{}'.format(it[0],it[1]),kwargs.items()))
                                      )
                
            fhash = str(hashlib.md5(fname.encode()).hexdigest())  ## Just a bit faster than murmur
            
            data = args[0].memCache.get(fhash)
            if data is not None: return data
            
            if location is not None:
                # if os.path.exists(location) == False:
                #     print('Making Cache Dirs')
                #     os.makedirs(location)
                
                fname = cacheFileNameGen(location, fhash)
                filePresent = os.path.exists(fname)
                # print(fname)
                # print(filePresent)
                # print(fname)
                if filePresent:
                    try:
                        with open(fname,'rb') as f:
                            # print('Loading from DISK cache')
                            data = pickle.load(f)
                    except Exception:
                        data = func(*args,**kwargs)
                        print('error')
                else:
                    data = func(*args,**kwargs)
            else:
                data = func(*args,**kwargs)
                
            newDataSize = sys.getsizeof(data)
            
            ## Trim MEM cache
            while memCacheFreeSpace() <= mem_size - newDataSize:
                for key in args[0].memCache:
                    # with open(os.path.join(location,key),'wb') as f:
                    #     # print('Saving to cache')
                    #     pickle.dump(args[0].memCache[key],f)
                    del args[0].memCache[key]
                    break
            
            ## Trim disk cache
            if location is not None:
                if filePresent == False:
                    if diskCacheFreeSpace(location) <= disk_size:
                        # if args[0].cacheFiles == []:
                        #     print('Reading Cache Files')
                        #     args[0].cacheFiles = getCacheFiles(location)
                        #     random.shuffle(args[0].cacheFiles)
                        # while getCacheSize(location) >= disk_size and len(files) > 0:
                        #     fileToRemove = files.pop(0)
                        #     print('Removing: {}'.format(fileToRemove))
                        #     os.remove(fileToRemove)
                        
                        ##  As long as free space is too low, pick a random cache file and delete it
                        while diskCacheFreeSpace(location) <= disk_size:
                            fileToRemove = getRandomCacheFile(location)
                            print('Trimming Cache File: {}'.format(fileToRemove))
                            os.remove(fileToRemove)
            
            if location is not None:
                if filePresent == False:
                    os.makedirs(os.path.split(fname)[0],exist_ok = True)
                    saveCacheFile(fname,data)
            
            # Insert new data into memCache dictionary
            args[0].memCache[fhash] = data
            return data
            
            # return output
        return wrapper
    return actual_decorator



def getSlice(imsClass,r,t,c,z,y,x):
    
    '''
    IMS stores 3D datasets ONLY with Resolution, Time, and Color as 'directory'
    structure witing HDF5.  Thus, data access can only happen accross dims XYZ
    for a specific RTC.  
    '''
    
    # incomingSlices = (r,t,c,z,y,x)
    tSize = list(range(imsClass.TimePoints)[t])
    cSize = list(range(imsClass.Channels)[c])
    zSize = len(range(imsClass.metaData[(r,0,0,'shape')][-3])[z])
    ySize = len(range(imsClass.metaData[(r,0,0,'shape')][-2])[y])
    xSize = len(range(imsClass.metaData[(r,0,0,'shape')][-1])[x])
    
    outputArray = np.zeros((len(tSize),len(cSize),zSize,ySize,xSize))
    # chunkRequested = outputArray.shape
    
    with h5py.File(imsClass.filePathComplete, 'r') as hf:
        for idxt, t in enumerate(tSize):
            for idxc, c in enumerate(cSize):
                # print(t)
                # print(c)
                dSetString = locationGenerator(r,t,c,data='data')
                outputArray[idxt,idxc,:,:,:] = hf[dSetString][z,y,x]
    
    
    ''' Some issues here with the output of these arrays.  Napari sometimes expects
    3-dim arrays and sometimes 5-dim arrays which originates from the dask array input representing
    tczyx dimentions of the imaris file.  When os.environ["NAPARI_ASYNC"] = "1", squeezing
    the array to 3 dimentions works.  When ASYNC is off squeese does not work.
    Napari thows an error because it did not get a 3-dim array.
    
    Am I implementing slicing wrong?  or does napari have some inconsistancy with the 
    dimentions of the arrays that it expects with different loading mechanisms if the 
    arrays have unused single dimentions.
    
    Currently "NAPARI_ASYNC" = '1' is set to one in the image loader
    Currently File/Preferences/Render Images Asynchronously must be turned on for this plugin to work
    '''
    try:
        # if os.environ["NAPARI_ASYNC"] == '1':
        #     while outputArray.shape[0] == 1 and len(outputArray.shape) > 1:
        #         outputArray = outputArray[0,:]
        #     # sliceOutput = outputArray.shape
        #     # print('Incoming Slices: {} / Slice Requested: {} / Slice Output {}'.format(incomingSlices,chunkRequested,sliceOutput))
        #     return outputArray
        
        ## Above code only eliminates low single length dims
        ## Squeeze will eliminate ALL single length dims
        if os.environ["NAPARI_ASYNC"] == '1':
            return np.squeeze(outputArray)
    except KeyError:
        pass
    
    # sliceOutput = outputArray.shape
    # print('Incoming Slices: {} / Slice Requested: {} / Slice Output {}'.format(incomingSlices,chunkRequested,sliceOutput))
    return outputArray
