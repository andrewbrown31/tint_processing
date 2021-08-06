#!/usr/bin/env python
# coding: utf-8

# In[1]:


import numpy as np
from matplotlib import pyplot as plt
from matplotlib.animation import FuncAnimation
from IPython.display import HTML, Image, display
import tempfile
import os
import shutil
import glob
import tqdm
from scipy.ndimage import gaussian_filter

import pyart
from tint import Cell_tracks, animate
from tint.visualization import embed_mp4_as_gif


"""
Tracking Parameter Guide
------------------------

FIELD_THRESH : units of 'field' attribute
    The threshold used for object detection. Detected objects are connnected
    pixels above this threshold.
ISO_THRESH : units of 'field' attribute
    Used in isolated cell classification. Isolated cells must not be connected
    to any other cell by contiguous pixels above this threshold.
ISO_SMOOTH : pixels
    Gaussian smoothing parameter in peak detection preprocessing. See
    single_max in tint.objects.
MIN_SIZE : square kilometers
    The minimum size threshold in pixels for an object to be detected.
SEARCH_MARGIN : meters
    The radius of the search box around the predicted object center.
FLOW_MARGIN : meters
    The margin size around the object extent on which to perform phase
    correlation.
MAX_DISPARITY : float
    Maximum allowable disparity value. Larger disparity values are sent to
    LARGE_NUM.
MAX_FLOW_MAG : meters per second
    Maximum allowable global shift magnitude. See get_global_shift in
    tint.phase_correlation.
MAX_SHIFT_DISP : meters per second
    Maximum magnitude of difference in meters per second for two shifts to be
    considered in agreement. See correct_shift in tint.matching.
GS_ALT : meters
    Altitude in meters at which to perform phase correlation for global shift
    calculation. See correct_shift in tint.matching.
"""


# In[2]:

load_grid=True
smooth=True
if load_grid:
        #files = np.sort(glob.glob("/g/data/eg3/ab4502/radar/71_20151215_23*.pvol.h5"))
        #files=np.sort(glob.glob("/g/data/eg3/ab4502/radar/02_20031210_01*"))
        #files=np.sort(glob.glob("/g/data/eg3/ab4502/radar/02_20080516_19*"))
        files=np.sort(glob.glob("/g/data/eg3/ab4502/radar/02_20110204_07*"))
        #files=np.sort(glob.glob("/g/data/eg3/ab4502/radar/02_20150228_09*"))
        #files=np.sort(glob.glob("/g/data/eg3/ab4502/radar/02_20180617_01*"))

        get_ipython().system('rm /scratch/eg3/ab4502/tint/*.nc')
        cnt = 0
        for f in tqdm.tqdm(files):
            radar = pyart.aux_io.read_odim_h5(f)
            grid = pyart.map.grid_from_radars(radar,(41,121,121),((0,20e3),(-150e3,150e3),(-150e3,150e3)), weighting_function="Barnes2", min_radius=2500.)
            if smooth:
                    grid.fields["reflectivity"]["data"] = np.stack([gaussian_filter(grid.fields["reflectivity"]["data"][i], 2) for i in np.arange(41)])
            grid.time["data"] = float(grid.time["data"])
            pyart.io.write_grid("/scratch/eg3/ab4502/tint/"+str(cnt).zfill(3)+".nc", grid)
            cnt=cnt+1


# In[3]:


grid_files = np.sort(glob.glob("/scratch/eg3/ab4502/tint/*.nc"))
grids = (pyart.io.read_grid(fn) for fn in grid_files)


# In[4]:


tracks_obj = Cell_tracks()
tracks_obj.params["FIELD_THRESH"]=30
tracks_obj.params["MIN_SIZE"]=15
tracks_obj.params["SEARCH_MARGIN"]=10000
tracks_obj.params["SKIMAGE_PROPS"]=["eccentricity","major_axis_length","minor_axis_length"]
tracks_obj.params["FIELD_DEPTH"]=5
tracks_obj.params["LOCAL_MAX_DIST"]=4
tracks_obj.get_tracks(grids)


# In[8]:


get_ipython().system('rm /g/data/eg3/ab4502/tint_anim.mp4')
grid_files = np.sort(glob.glob("/scratch/eg3/ab4502/tint/*.nc"))
grids = (pyart.io.read_grid(fn) for fn in grid_files)
animate(tracks_obj, grids, "/g/data/eg3/ab4502/tint_anim", tracers=True)
tracks_obj.tracks.to_csv("/g/data/eg3/ab4502/tint_example.csv")
