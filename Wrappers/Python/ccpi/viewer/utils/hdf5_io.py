import vtk
from vtk.util.vtkAlgorithm import VTKPythonAlgorithmBase
import h5py
import numpy as np
from vtk.numpy_interface import dataset_adapter as dsa

# Methods for reading and writing HDF5 files:


def write_image_data_to_hdf5(filename, data, dataset_name, attributes={},
                             array_name='vtkarray'):
    '''
    Writes vtkImageData to a dataset in a HDF5 file

    Args:
        filename: string - name of HDF5 file to write to.
        data: vtkImageData - image data to write.
        DatasetName: string - DatasetName for HDF5 dataset.
        attributes: dict - attributes to assign to HDF5 dataset.
        array_name: string - name of array to read points from the vtkImageData
    '''

    with h5py.File(filename, "a") as f:
        wdata = dsa.WrapDataObject(data)
        array = wdata.PointData[array_name]
        # Note that we flip the dimensions here because
        # VTK's order is Fortran whereas h5py writes in
        # C order. We don't want to do deep copies so we write
        # with dimensions flipped and pretend the array is
        # C order.
        array = array.reshape(wdata.GetDimensions()[::-1])
        try:
            dset = f.create_dataset(dataset_name, data=array)
        except RuntimeError:
            print("Unable to save image data to {0}."
                  "Dataset with name {1} already exists in this file.".format(
                      filename, dataset_name))
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
        VTKPythonAlgorithmBase.__init__(self,
                                        nInputPorts=0,
                                        nOutputPorts=1,
                                        outputType='vtkImageData')

        self.__FileName = ""
        self.__DatasetName = None
        self.__4DIndex = 0

    def RequestData(self, request, inInfo, outInfo):
        if self.__DatasetName is None:
            raise Exception("DataSetName must be set.")
        with h5py.File(self.__FileName, 'r') as f:
            info = outInfo.GetInformationObject(0)
            shape = np.shape(f[self.__DatasetName])
            # print("keys:", list(f.keys()))
            # print(shape)
            ue = info.Get(vtk.vtkStreamingDemandDrivenPipeline.UPDATE_EXTENT())
            # Note that we flip the update extents because VTK is Fortran order
            # whereas h5py reads in C order. When writing we pretend that the
            # data was C order so we have to flip the extents/dimensions.
            if len(shape) == 3:
                data = f[self.__DatasetName][ue[4]:ue[5]+1, ue[2]:ue[3]+1, ue[0]:ue[1]+1]
            elif len(shape) == 4:
                data = f[self.__DatasetName][self.__4DIndex][
                    ue[4]:ue[5] + 1, ue[2]:ue[3]+1, ue[0]:ue[1]+1]
            # print("attributes: ", f.attrs.items())
            output = dsa.WrapDataObject(vtk.vtkImageData.GetData(outInfo))
            output.SetExtent(ue)
            output.PointData.append(data.ravel(), self.__DatasetName)
            output.PointData.SetActiveScalars(self.__DatasetName)
            return 1

    def SetFileName(self, fname):
        if fname != self.__FileName:
            self.Modified()
            self.__FileName = fname

    def GetFileName(self):
        return self.__FileName

    def SetDatasetName(self, lname):
        if lname != self.__DatasetName:
            self.Modified()
            self.__DatasetName = lname

    def GetDatasetName(self):
        return self.__DatasetName

    def Set4DIndex(self, index):
        '''Sets which index to read, in the case of a 4D dataset'''
        if index != self.__4DIndex:
            self.Modified()
            self.__4DIndex = index

    def GetDimensions(self):
        with h5py.File(self.__FileName, 'r') as f:
            # Note that we flip the shape because VTK is Fortran order
            # whereas h5py reads in C order. When writing we pretend that the
            # data was C order so we have to flip the extents/dimensions.
            if self.__DatasetName is None:
                raise Exception("DataSetName must be set.")
            return f[self.__DatasetName].shape[::-1]

    def GetOrigin(self):
        # There is not a standard way to set the origin in a HDF5
        # file so we do not have a way to read it. Therefore we 
        # assume it is at 0,0,0
        return (0, 0, 0)

    def GetDataType(self):
        with h5py.File(self.__FileName, 'r') as f:
            data_type = type(f[self.__DatasetName][0][0][0])
            if isinstance(data_type, np.ndarray):
                data_type = type(f[self.__DatasetName][0][0][0])
            return data_type

    def RequestInformation(self, request, inInfo, outInfo):
        dims = self.GetDimensions()
        info = outInfo.GetInformationObject(0)
        info.Set(vtk.vtkStreamingDemandDrivenPipeline.WHOLE_EXTENT(),
                 (0, dims[0]-1, 0, dims[1]-1, 0, dims[2]-1), 6)
        return 1


class HDF5SubsetReader(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self,
                                        nInputPorts=1,
                                        inputType='vtkImageData',
                                        nOutputPorts=1,
                                        outputType='vtkImageData')
        self.__UpdateExtent = None

    def RequestInformation(self, request, inInfo, outInfo):
        info = outInfo.GetInformationObject(0)
        info.Set(vtk.vtkStreamingDemandDrivenPipeline.WHOLE_EXTENT(),
                 self.__UpdateExtent, 6)
        return 1

    def RequestUpdateExtent(self, request, inInfo, outInfo):
        if self.__UpdateExtent is not None:
            info = inInfo[0].GetInformationObject(0)

            whole_extent = info.Get(
                vtk.vtkStreamingDemandDrivenPipeline.WHOLE_EXTENT())
            set_extent = list(info.Get(
                vtk.vtkStreamingDemandDrivenPipeline.UPDATE_EXTENT()))
            for i, value in enumerate(set_extent):
                if value == -1:
                    set_extent[i] = whole_extent[i]
                else:
                    if i % 2 == 0:
                        if value < whole_extent[i]:
                            raise ValueError("Requested extent {}\
                                is outside of original image extent {}".format(
                                set_extent, whole_extent))
                    else:
                        if value > whole_extent[i]:
                            raise ValueError("Requested extent {}\
                                is outside of original image extent {}".format(
                                set_extent, whole_extent))
            
            self.SetUpdateExtent(set_extent)

            info.Set(vtk.vtkStreamingDemandDrivenPipeline.UPDATE_EXTENT(),
                     self.__UpdateExtent, 6)
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
