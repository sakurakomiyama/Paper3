import pandas as pd
import matplotlib.dates as mdates
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.interpolate import UnivariateSpline
from scipy.ndimage import gaussian_filter1d
from scipy import stats
from scipy.stats import gaussian_kde
from datetime import datetime # for "to_csv_wdatetime" function
import os
# specially for map
from mpl_toolkits.basemap import Basemap
from matplotlib_scalebar.scalebar import ScaleBar
import matplotlib.image as mpimg
from matplotlib.patches import Rectangle, ConnectionPatch
from matplotlib.patches import Polygon
import matplotlib.gridspec as gridspec
#from scipy.spatial import ConvexHull
from matplotlib.lines import Line2D

exec(open("Functions.py").read())
#%matplotlib qt 


