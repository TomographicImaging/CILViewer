from ccpi.viewer.CILViewer import CILViewer as viewer3D
import glob
import vtk
import numpy as np
from ccpi.viewer.utils.io import ImageReader, \
                                cilTIFFResampleReader
from ccpi.viewer.utils.conversion import cilNumpyResampleReader, \
                                         cilHDF5ResampleReader,\
                                         cilRawResampleReader

import os, sys
import argparse


def createAnimation(viewer, FrameCount=20, 
                    InitialCameraPosition=None, FocalPoint=None, 
                    ClippingRange=None, AngleRange = 360, ViewUp = None, clip_plane=False, 
                    fname_offset=0, fname_prefix='test', output_dir='.'):
    
    viewer

    if InitialCameraPosition is None:
        InitialCameraPosition = viewer.getCamera().GetPosition()
    if FocalPoint is None:
        FocalPoint = viewer.getCamera().GetFocalPoint()
    if ClippingRange is None:
        ClippingRange = (0,2000)
    if ViewUp is None:
        ViewUp = (0,0,1)
    if FrameCount is None:
        FrameCount = 100
    #Setting locked values for camera position
    locX = InitialCameraPosition[0]
    locY = InitialCameraPosition[1]
    locZ = InitialCameraPosition[2]

    print('Initial Camera Position: {}'.format(InitialCameraPosition))
    #Setting camera position
    viewer.getCamera().SetPosition(InitialCameraPosition)
    viewer.getCamera().SetFocalPoint(FocalPoint)

    #Setting camera viewup 
    viewer.getCamera().SetViewUp(ViewUp)

    #Set camera clipping range
    viewer.getCamera().SetClippingRange(ClippingRange)

    #Defining distance from camera to focal point
    r = np.sqrt(((InitialCameraPosition[0]-FocalPoint[0])**2)
    +(InitialCameraPosition[1]-FocalPoint[1])**2)
    print('Radius (distance from camera to focal point): {}'.format(r))

    if not clip_plane:
        viewer.style.ToggleSliceVisibility()
        
    #Animating the camera
    for x in range(FrameCount):
        if clip_plane:
            # move the slice during rotation
            new_slice = round(x/FrameCount * viewer.img3D.GetDimensions()[2])
            print('displaying slice {}'.format(new_slice))
            viewer.style.SetActiveSlice(new_slice)
            viewer.updatePipeline(False)
            # plane on the slice plane
            plane = vtk.vtkPlane()
            plane.SetOrigin(0,0,new_slice * viewer.img3D.GetSpacing()[2])
            plane.SetNormal(0,0,-1)

            viewer.volume.GetMapper().RemoveAllClippingPlanes()
            viewer.volume.GetMapper().AddClippingPlane(plane)
            viewer.volume.Modified()
            viewer.getRenderer().Render()
            

        
        angle = (2 * np.pi ) * (x/FrameCount)
        NewLocationX = r * np.sin(angle) + FocalPoint[0]
        NewLocationY = r * np.cos(angle) + FocalPoint[1]
        NewLocation = (NewLocationX, NewLocationY, locZ)
        camera = vtk.vtkCamera()
        camera.SetFocalPoint(FocalPoint)
        camera.SetViewUp(ViewUp)
        camera.SetPosition(*NewLocation)
        viewer.ren.SetActiveCamera(camera)
        viewer.adjustCamera()
        
        import time
        time.sleep(0.1)
        print("render frame {} angle {}".format(x, angle))
        print('Camera Position: {}'.format(NewLocation))
        rp = np.sqrt(((NewLocation[0]-FocalPoint[0])**2)
            +(NewLocation[1]-FocalPoint[1])**2)
        print ('Camera trajectory radius {}'.format(rp))
        #Rendering and saving the render
        viewer.getRenderer().Render()
        viewer.renWin.Render()
        saveRender(viewer, x + fname_offset, fname_prefix, directory=output_dir)

def saveRender(viewer, number, file_prefix, directory='.'):
    w2if = vtk.vtkWindowToImageFilter()
    w2if.SetInput(viewer.renWin)
    w2if.Update()

    
    saveFilename = '{}_{:04d}.png'.format(os.path.join(directory, file_prefix), number)

    writer = vtk.vtkPNGWriter()
    writer.SetFileName(saveFilename)
    writer.SetInputConnection(w2if.GetOutputPort())
    writer.Write()

class Readers():
    @staticmethod
    def get_reader(filename, dimensions=None, data_path=None):
        if os.path.isdir(filename):
            # should return and TIFF reader
            return Readers._return_tiff_reader(filename)
        else:
            if data_path is not None:
                
                # HDF5 file
                import h5py
                with h5py.File(filename, 'r') as f:
                    f.items()
                reader = cilHDF5ResampleReader()
                reader.SetFileName(filename)
                reader.SetDatasetName(data_path)
                return reader
            
            elif dimensions is not None:
                reader = cilRawResampleReader()
                reader.SetFileName(filename)
                reader.SetStoredArrayShape(dimensions)
                return reader
            else:
                # Figure out what file we have
                # 2) npy
                from ccpi.viewer.utils.conversion import parseNpyHeader
                try:
                    header = parseNpyHeader(filename)
                    if header['type'] == 'NUMPY':
                        ret = cilNumpyResampleReader()
                        ret.SetFileName(filename)
                        return ret
                except Exception as err:
                    pass
                
                # 3) mha/mhd
                try:
                    from ccpi.viewer.utils.conversion import cilMetaImageResampleReader
                    reader = cilMetaImageResampleReader()
                    reader.SetFileName(filename)
                    
                    reader.ReadMetaImageHeader()
                    return reader
                except Exception as err:
                        pass
                
            
            # 1) raw file
            
    @staticmethod
    def _return_tiff_reader(dirname):            
        fnames = [el for el in glob.glob(os.path.join(dirname, "*.tiff"))]
    
        print ("#########################") 
        print (dirname, fnames)

        if len(fnames) == 0:
            # try again with .tif extension
            fnames = [el for el in glob.glob(os.path.join(dirname, "*.tiff"))]
            raise ValueError(f"Directory {dirname} does not contain tiff files with extension tiff or tif")
        reader = cilTIFFResampleReader()
        reader.SetFileName(fnames)
        return reader
    

if __name__ == '__main__':    
    parser = argparse.ArgumentParser(description='Create awesome volume render')

    parser.add_argument('--verbose', type=int, default=0)
    parser.add_argument('--volume', type=str, default='scalar')
    parser.add_argument('--max_opacity', type=float, default=0.1)
    parser.add_argument('--spacing', type=float, nargs=3, default=None)
    parser.add_argument('--spacing_multiplier', type=float, nargs=3, default=None)
    parser.add_argument('--max_size', type=int, nargs=3, default=[1024,1024,1024])
    parser.add_argument('--resample_z', type=bool, default=True)
    parser.add_argument('--colormap', type=str, default='viridis')
    parser.add_argument('--num_frames', type=int, default=10)
    parser.add_argument('--output_dir', type=str, default='.')
    parser.add_argument('--output_prefix', type=str, default='awesome')
    parser.add_argument('--dimensions', type=int, nargs=3, default=None)
    parser.add_argument('--data_path', type=str, default=None)
    parser.add_argument('--camera_position', type=float)
    
    parser.add_argument('input', help='File or directory')
    args = parser.parse_args()

    print (args)

    # print ("################### ", len(sys.argv))
    # exit(0)

    from ccpi.viewer.CILViewer import CILViewer as viewer3D
    from ccpi.viewer.utils.io import ImageReader, cilHDF5ResampleReader, cilTIFFResampleReader
    import vtk

    v = viewer3D(debug=True if args.verbose >0 else False)



    # detect the file format and return the appropriate reader


    # reader = ImageReader(r"C:\Users\ofn77899\Data\dvc/frame_000_f.npy", resample=False)
    # reader = ImageReader(r"{}/head_uncompressed.mha".format(os.path.dirname(__file__)), resample=False)
    # data = reader.Read()



    pokemon = args.output_prefix
    
    # subdir = 'Not_Angled'

    reader = Readers.get_reader(args.input, dimensions=args.dimensions, 
                                data_path=args.data_path)
    
    # dirname = os.path.abspath("C:/Users/ofn77899/Data\HOW/{}/{}/".format(pokemon, subdir))
    
    # fnames = [el for el in glob.glob(os.path.join(dirname, "*.tiff"))]
    
    # print ("#########################") 
    # print (dirname, fnames)

    # if len(fnames) == 0:
    #     exit(1)

    # reader = cilTIFFResampleReader()
    # reader.SetFileName(fnames)
    reader.SetTargetSize(1024*1024*1024)
    reader.Update()
    data = reader.GetOutput()

    print (data.GetSpacing())
        
    if args.spacing is not None:
        data.SetSpacing(*args.spacing)
    elif args.spacing_multiplier is not None:
        dims = data.GetDimensions()
        spac = list(data.GetSpacing())
        # spac[2] = dims[0]/dims[2]
        # spac[2] *= 0.75
        for i in range(3):
            spac[i] *= args.spacing_multiplier[i] 
        data.SetSpacing(*spac)
    print (data.GetSpacing())

    v.setInputData(reader.GetOutput())

    v.style.ToggleVolumeVisibility()
    

    v.setVolumeColorMapName('viridis')

    # define colors and opacity with default values
    colors, opacity = v.getColorOpacityForVolumeRender()

    v.volume_property.SetColor(colors)

    method = 'scalar'
    if method == 'gradient':
        color_percentiles = (65., 98.)
        gradient_opacity_percentiles = (75., 99.9)
        max_opacity = 0.1
        v.setVolumeRenderOpacityMethod('gradient')
        v.setGradientOpacityPercentiles(*gradient_opacity_percentiles, update_pipeline=False)
        v.volume_property.SetGradientOpacity(opacity)
    else:
        color_percentiles = (75., 99.)
        scalar_opacity_percentiles = (94., 99.5)
        max_opacity = 0.1
        v.setVolumeRenderOpacityMethod('scalar')
        v.setScalarOpacityPercentiles(*scalar_opacity_percentiles, update_pipeline=False)
        v.volume_property.SetScalarOpacity(opacity)
    
    v.setVolumeColorPercentiles(*color_percentiles, update_pipeline=False)
    v.setMaximumOpacity(max_opacity)

    # default background
    # self.ren.SetBackground(.1, .2, .4)
    # v.ren.SetBackground(0, 0, 0)
    v.ren.SetBackground(1,1,1)
    
    
    createAnimation(v, FrameCount=args.num_frames, 
                    InitialCameraPosition=(
                        (483.8653687626969, -2173.282759469902, 1052.4208133258792)
                        ), 
                    AngleRange=360, 
                    clip_plane=True, 
                    fname_offset=0,
                    fname_prefix=pokemon,
                    output_dir="C:/Users/ofn77899/Data/HOW/Picachu/renders")
    
    createAnimation(v, FrameCount=args.num_frames, 
                    InitialCameraPosition=(
                        (483.8653687626969, -2173.282759469902, 1052.4208133258792)
                        ), 
                    AngleRange=360, 
                    clip_plane=False, 
                    fname_offset=100,
                    fname_prefix=pokemon,
                    output_dir=r'C:\Users\ofn77899\Data\HOW\Picachu\renders')

    