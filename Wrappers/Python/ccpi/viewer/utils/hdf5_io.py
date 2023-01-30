import vtk
from vtk.util.vtkAlgorithm import VTKPythonAlgorithmBase
import h5py
import numpy as np
from vtk.numpy_interface import dataset_adapter as dsa
from vtk.util import numpy_support

# Methods for reading and writing HDF5 files:


def write_image_data_to_hdf5(filename, data, dataset_name, attributes={}):
    '''
    Writes vtkImageData to a dataset in a HDF5 file

    Args:
        filename: string - name of HDF5 file to write to.
        data: vtkImageData - image data to write.
        DatasetName: string - DatasetName for HDF5 dataset.
        attributes: dict - attributes to assign to HDF5 dataset.
    '''

    with h5py.File(filename, "a") as f:
        # The function imgdata.GetPointData().GetScalars() returns a pointer to a
        # vtk<TYPE>Array where the data is stored as X-Y-Z.
        array = numpy_support.vtk_to_numpy(data.GetPointData().GetScalars())

        # Note that we flip the dimensions here because
        # VTK's order is Fortran whereas h5py writes in
        # C order. We don't want to do deep copies so we write
        # with dimensions flipped and pretend the array is
        # C order.
        array = array.reshape(data.GetDimensions()[::-1])
        try:
            dset = f.create_dataset(dataset_name, data=array)
        except RuntimeError:
            print("Unable to save image data to {0}."
                  "Dataset with name {1} already exists in this file.".format(filename, dataset_name))
            return
        for key, value in attributes.items():
            dset.attrs[key] = value


class HDF5Reader(VTKPythonAlgorithmBase):
    '''
    vtkAlgorithm for reading vtkImageData from a HDF5 file
    Adapted from:
    https://blog.kitware.com/developing-hdf5-readers-using-vtkpythonalgorithm/
    To use this, you must set a FileName (the file you are reading), and also a
    DatasetName (the name of where in the hdf5 file the data will be saved)
    '''

    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self, nInputPorts=0, nOutputPorts=1, outputType='vtkImageData')

        self._FileName = None
        self._DatasetName = None
        self._4DSliceIndex = 0
        self._4DIndex = 0

    def RequestData(self, request, inInfo, outInfo):
        self._update_output_data(outInfo)
        return 1

    def _update_output_data(self, outInfo):
        if self._DatasetName is None:
            raise Exception("DataSetName must be set.")
        if self._FileName is None:
            raise Exception("FileName must be set.")
        with h5py.File(self._FileName, 'r') as f:
            info = outInfo.GetInformationObject(0)
            shape = np.shape(f[self._DatasetName])
            # print("keys:", list(f.keys()))
            # print(shape)
            ue = info.Get(vtk.vtkStreamingDemandDrivenPipeline.UPDATE_EXTENT())
            # Note that we flip the update extents because VTK is Fortran order
            # whereas h5py reads in C order. When writing we pretend that the
            # data was C order so we have to flip the extents/dimensions.
            if len(shape) == 3:
                data = f[self._DatasetName][ue[4]:ue[5] + 1, ue[2]:ue[3] + 1, ue[0]:ue[1] + 1]
            elif len(shape) == 4:
                if self._4DIndex == 0:
                    data = f[self._DatasetName][self._4DSliceIndex, ue[4]:ue[5] + 1, ue[2]:ue[3] + 1, ue[0]:ue[1] + 1]
                elif self._4DIndex == 1:
                    data = f[self._DatasetName][ue[4]:ue[5] + 1, self._4DSliceIndex, ue[2]:ue[3] + 1, ue[0]:ue[1] + 1]
                elif self._4DIndex == 2:
                    data = f[self._DatasetName][ue[4]:ue[5] + 1, ue[2]:ue[3] + 1, self._4DSliceIndex, ue[0]:ue[1] + 1]
                elif self._4DIndex == 3:
                    data = f[self._DatasetName][ue[4]:ue[5] + 1, ue[2]:ue[3] + 1, ue[0]:ue[1] + 1, self._4DSliceIndex]
            else:
                raise Exception("Currently only 3D and 4D datasets are supported.")
            # print("attributes: ", f.attrs.items())
            output = dsa.WrapDataObject(vtk.vtkImageData.GetData(outInfo))
            output.SetExtent(ue)
            output.PointData.append(data.ravel(), self._DatasetName)
            output.PointData.SetActiveScalars(self._DatasetName)
            return output

    def SetFileName(self, fname):
        if fname != self._FileName:
            self.Modified()
            if self._DatasetName is not None:
                with h5py.File(fname, 'r') as f:
                    if not (self._DatasetName in f):
                        raise Exception("No dataset named {} exists in {}.".format(self._DatasetName, fname))
            self._FileName = fname

    def GetFileName(self):
        return self._FileName

    def SetDatasetName(self, lname):
        if lname != self._DatasetName:
            self.Modified()
            if self._FileName is not None:
                with h5py.File(self._FileName, 'r') as f:
                    if not (lname in f):
                        raise Exception("No dataset named {} exists in {}.".format(lname, self._FileName))
            self._DatasetName = lname

    def GetDatasetName(self):
        return self._DatasetName

    def Set4DIndex(self, index):
        '''Sets which index is the 4th dimension that we will only read 1 slice of.'''
        if index not in range(0, 4):
            raise Exception("4D Index must be between 0 and 3.")
        if index != self._4DIndex:
            self.Modified()
            self._4DIndex = index

    def Set4DSliceIndex(self, index):
        '''Sets which index to read along the 4th dimension.'''
        if index != self._4DSliceIndex:
            self.Modified()
            self._4DSliceIndex = index

    def GetDimensions(self):
        if self._FileName is None:
            raise Exception("FileName must be set.")
        with h5py.File(self._FileName, 'r') as f:
            # Note that we flip the shape because VTK is Fortran order
            # whereas h5py reads in C order. When writing we pretend that the
            # data was C order so we have to flip the extents/dimensions.
            if self._DatasetName is None:
                raise Exception("DataSetName must be set.")
            return f[self._DatasetName].shape[::-1]

    def GetDataSetAttributes(self):
        if self._FileName is None:
            raise Exception("FileName must be set.")
        with h5py.File(self._FileName, 'r') as f:
            if self._DatasetName is None:
                raise Exception("DataSetName must be set.")
            return dict(f[self._DatasetName].attrs)

    def GetOrigin(self):
        # There is not a standard way to set the origin in a HDF5
        # file so we do not have a way to read it. Therefore we
        # assume it is at 0,0,0
        return (0, 0, 0)

    def GetDataType(self):
        if self._FileName is None:
            raise Exception("FileName must be set.")
        with h5py.File(self._FileName, 'r') as f:
            data_type = type(f[self._DatasetName][0][0][0])
            if isinstance(data_type, np.ndarray):
                data_type = type(f[self._DatasetName][0][0][0])
            return data_type

    def RequestInformation(self, request, inInfo, outInfo):
        dims = self.GetDimensions()
        info = outInfo.GetInformationObject(0)
        info.Set(vtk.vtkStreamingDemandDrivenPipeline.WHOLE_EXTENT(), (0, dims[0] - 1, 0, dims[1] - 1, 0, dims[2] - 1),
                 6)
        return 1


class HDF5SubsetReader(VTKPythonAlgorithmBase):
    '''Modifies a HDF5Reader to return a different extent from an HDF5 file
    
    
    Examples:
    ---------
    
    reader = HDF5Reader() 
    reader.SetFileName('file.h5') 
    reader.SetDatasetName("ImageData") 
    
    cropped_reader = HDF5SubsetReader() 
    cropped_reader.SetInputConnection(reader.GetOutputPort()) 
    cropped_reader.SetUpdateExtent((0, 2, 3, 5, 1, 2)) 
    cropped_reader.Update() 
    '''

    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self,
                                        nInputPorts=1,
                                        inputType='vtkImageData',
                                        nOutputPorts=1,
                                        outputType='vtkImageData')
        self.__UpdateExtent = None

    def RequestInformation(self, request, inInfo, outInfo):
        info = outInfo.GetInformationObject(0)
        info.Set(vtk.vtkStreamingDemandDrivenPipeline.WHOLE_EXTENT(), self.__UpdateExtent, 6)
        return 1

    def RequestUpdateExtent(self, request, inInfo, outInfo):
        if self.__UpdateExtent is not None:
            info = inInfo[0].GetInformationObject(0)

            whole_extent = info.Get(vtk.vtkStreamingDemandDrivenPipeline.WHOLE_EXTENT())
            set_extent = list(info.Get(vtk.vtkStreamingDemandDrivenPipeline.UPDATE_EXTENT()))

            for i, value in enumerate(set_extent):
                if value == -1:
                    set_extent[i] = whole_extent[i]
                else:
                    if i % 2 == 0:
                        if value < whole_extent[i]:
                            raise ValueError("Requested extent {}\
                                is outside of original image extent {} as {}<{}".format(
                                set_extent, whole_extent, value, whole_extent[i]))
                    else:
                        if value > whole_extent[i]:
                            raise ValueError("Requested extent {}\
                                is outside of original image extent {} as {}>{}".format(
                                set_extent, whole_extent, value, whole_extent[i]))

            self.SetUpdateExtent(set_extent)

            info.Set(vtk.vtkStreamingDemandDrivenPipeline.UPDATE_EXTENT(), self.__UpdateExtent, 6)
        return 1

    def RequestData(self, request, inInfo, outInfo):
        inp = vtk.vtkImageData.GetData(inInfo[0])
        opt = vtk.vtkImageData.GetData(outInfo)
        opt.ShallowCopy(inp)
        return 1

    def SetUpdateExtent(self, ue):
        if ue != self.__UpdateExtent:
            self.Modified()
            self.__UpdateExtent = ue

    def GetUpdateExtent(self):
        return self.__UpdateExtent

    def GetOutput(self):
        return self.GetOutputDataObject(0)
