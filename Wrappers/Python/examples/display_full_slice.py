#%%
from ccpi.viewer import viewer2D
from ccpi.viewer.utils.conversion import cilTIFFCroppedReader, cilNumpyCroppedReader, Converter
import os, glob
from PIL import Image
from PIL.TiffTags import TAGS
import matplotlib.pyplot as plt
import numpy as np


def get_fnames(dir, pattern='*.tiff'):
    '''Returns a list of filenames in dir matching pattern'''
    data_dir = os.path.abspath(r'E:/Data/Antikythera/X-RAY CT Fragment A/X-RAY CT A Scan 6/A Scan 6 Raw Data')
    print(data_dir)
    # fnames = glob.glob(os.path.join(data_dir, '*.tiff'))
    # print (fnames)
    import re
    fnames = []
    # Proj(\d+).tif
    ptn = re.compile(pattern)
    for i,el in enumerate(os.listdir(data_dir)):
        if ptn.match(el):
            # print(pattern.match(el).group(1) , el)
            fnames.append(os.path.join(data_dir, el))
    return fnames

# import pysnooper
# @pysnooper.snoop()
def create_sinogram(reader, vertical):
    fnames = reader.GetFileName()
    i=0
    reader.SetTargetZExtent((0, 0))
    reader.Update()
    proj = reader.GetOutput()
    dshape = Converter.vtk2numpy(proj).shape
    out = np.zeros((len(fnames), dshape[1]), dtype=np.float32)
    for i, el in enumerate(fnames):
        reader.SetTargetZExtent((i, i))
        reader.Update()
        proj = reader.GetOutput()
        pp = Converter.vtk2numpy(proj)
        out[i] = pp[:, vertical, :].squeeze()
    return out
#%%
data_dir = os.path.abspath('C:/Users/ofn77899/Data/dvc/')

ftype = 'tiff'

if ftype == 'npy':
    fname = os.path.abspath('C:/Users/ofn77899/Data/dvc/frame_000_f.npy')
    reader = cilNumpyCroppedReader()
    reader.SetFileName(fname)
elif ftype == 'tiff':
    reader = cilTIFFCroppedReader()
    # data_dir = os.path.abspath('C:/Users/ofn77899/Data/dvc/frame_000')
    data_dir = os.path.abspath(r'E:/Data/Antikythera/X-RAY CT Fragment A/X-RAY CT A Scan 6/A Scan 6 Raw Data')
    print(data_dir)
    # fnames = glob.glob(os.path.join(data_dir, '*.tiff'))
    # print (fnames)
    import re
    fnames = get_fnames(data_dir, r'Proj(\d+).tif')
#%%    
    dt = []
    start = True
    
    suspect = []
    for i,el in enumerate(fnames):
        with Image.open(el) as img:
            # print (img.tag[306])
            from datetime import datetime
            # print (img.tag[306][0])
            # tt = datetime.fromisoformat(img.tag[306][0])
            # print (tt)
            
            tt = datetime.strptime(img.tag[306][0], '%Y:%m:%d %H:%M:%S')
            # print (tt.toordinal())
            # print (tt, tt.timestamp())
            tt = tt.timestamp()
            if start:
                t0 = tt
                start = False
            dt.append((tt - t0))
            if tt-t0 > 1:
                suspect.append(el)
            
            t0 = tt
            
            if (i % 100 == 0):
                print (i/len(fnames))
                           
    reader.SetFileName(fnames)
    sino = create_sinogram(reader, vertical=1024)
    
    from cil.utilities.display import show2D
    show2D(sino, cmap='inferno')

#%%
    print (dt)

    # plt.scatter(dt, range(len(dt)))
    # plt.show()
    print (suspect)

    histo = plt.hist(dt, bins=6)

# v = viewer2D()
# v.setInputDataReader(reader)
# v.startRenderLoop()


# %%
