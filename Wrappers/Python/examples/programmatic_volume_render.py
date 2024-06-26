from ccpi.viewer.CILViewer2D import CILViewer2D as viewer2D
from ccpi.viewer.CILViewer import CILViewer as viewer3D
import glob
import vtk

if __name__ == '__main__':
    v = viewer3D(debug=False)
    from ccpi.viewer.utils.io import ImageReader, cilHDF5ResampleReader, cilTIFFResampleReader
    from ccpi.viewer.utils.conversion import cilTIFFImageReaderInterface
    import os
    # reader = ImageReader(r"C:\Users\ofn77899\Data\dvc/frame_000_f.npy", resample=False)
    # reader = ImageReader(r"{}/head_uncompressed.mha".format(os.path.dirname(__file__)), resample=False)
    # data = reader.Read()
    
    dirname = r"C:\Users\ofn77899\Data\HOW\Not_Angled"
    fnames = [el for el in glob.glob(os.path.join(dirname, "*.tiff"))]
    
    reader = cilTIFFResampleReader()
    reader.SetFileName(fnames)
    reader.SetTargetSize(1024*1024*1024)
    reader.Update()
    data = reader.GetOutput()

    dims = data.GetDimensions()
    spac = list(data.GetSpacing())
    spac[2] = dims[0]/dims[2]
    print (data.GetSpacing())
    data.SetSpacing(*spac)
    print (data.GetSpacing())

    v.setInputData(reader.GetOutput())

    v.style._volume_render_pars =  {
            'color_percentiles' : (75., 99.),
            'scalar_opacity_percentiles' : (80., 99.),
            'gradient_opacity_percentiles' : (95., 99.9),
            'max_opacity' : 0.05
        }


    v.setVolumeColorMapName('bone')
    v.setVolumeRenderOpacityMethod('gradient')

    v.style.ToggleVolumeVisibility()
    v.style.ToggleSliceVisibility()

    # default background
    # self.ren.SetBackground(.1, .2, .4)
    v.ren.SetBackground(0, 0, 0)
    
    v.startRenderLoop()

    v.createAnimation(FrameCount=10, InitialCameraPosition=((483.8653687626969, -2173.282759469902, 1052.4208133258792)), AngleRange=360)

    