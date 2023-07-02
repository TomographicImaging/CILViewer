from ccpi.viewer import viewer2D
from ccpi.viewer.utils.conversion import cilTIFFCroppedReader, cilNumpyCroppedReader
import os, glob


data_dir = os.path.abspath('C:/Users/ofn77899/Data/dvc/')

ftype = 'tiff'

if ftype == 'npy':
    fname = os.path.abspath('C:/Users/ofn77899/Data/dvc/frame_000_f.npy')
    reader = cilNumpyCroppedReader()
    reader.SetFileName(fname)
elif ftype == 'tiff':
    reader = cilTIFFCroppedReader()
    data_dir = os.path.abspath('C:/Users/ofn77899/Data/dvc/frame_000')
    fnames = glob.glob(os.path.join(data_dir, '*.tiff'))
    reader.SetFileName(fnames)


v = viewer2D()

v.setInputDataReader(reader)

v.startRenderLoop()

