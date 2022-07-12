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
    ''' Create the error observer and attach it to the hdf5 reader. If an error occurs,
     it will run the callback_fn, which is given the error message as an input.
     So in this case it will print the error message.'''
    error_obs = ErrorObserver(callback_fn=print)
    readerhdf5.AddObserver(vtk.vtkCommand.ErrorEvent, error_obs)
    ''' Create the end observer and attach it to the hdf5 reader.
    When the function it calls finishes, it checks the given error observer to see if an error occurred.
    If not, it then runs the callback_fn. In this case, it displays the hdf5 image in the iviewer.'''
    end_obs = EndObserver(
        error_observer=error_obs,
        callback_fn=lambda: iviewer(readerhdf5.GetOutputDataObject(0), readerhdf5.GetOutputDataObject(0)))
    readerhdf5.AddObserver(vtk.vtkCommand.EndEvent, end_obs)
    readerhdf5.SetFileName(hdf5_name)
    ''' With this commented, we get an exception due to DatasetName not being set.
    Uncommenting this runs the callback_fn in the EndEvent: '''
    #readerhdf5.SetDatasetName("entry1/tomo_entry/data/data")
    readerhdf5.Update()
