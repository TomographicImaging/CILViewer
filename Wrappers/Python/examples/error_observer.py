
import vtk
from ccpi.viewer.iviewer import iviewer
from ccpi.viewer.utils.conversion import cilHDF5ResampleReader
from ccpi.viewer.utils.error_handling import EndObserver, ErrorObserver

'''
An example which shows attaching an error observer and end observer
to reading a HDF5 file
'''        


if __name__ == "__main__":
    hdf5_name = r'C:\Users\lhe97136\Work\Data\24737_fd_normalised.nxs'
    readerhdf5 = cilHDF5ResampleReader()
    error_obs = ErrorObserver()
    end_obs = EndObserver(error_observer=error_obs, callback_fn = lambda: iviewer(readerhdf5.GetOutputDataObject(0), readerhdf5.GetOutputDataObject(0)))
    readerhdf5.AddObserver(vtk.vtkCommand.ErrorEvent, error_obs)
    readerhdf5.AddObserver(vtk.vtkCommand.EndEvent, end_obs)
    readerhdf5.SetFileName(hdf5_name)
    # With this commented, we get an exception due to DatasetName not being set.
    # Uncommenting this runs the callback_fn in the EndEvent:
    # readerhdf5.SetDatasetName("entry1/tomo_entry/data/data")
    readerhdf5.Update()

