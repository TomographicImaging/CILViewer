import os
import os.path 
import vtk


data_dir = os.path.abspath(os.path.join(
        os.path.dirname(__file__),
        '../data/')
)

class DATA(object):
    @classmethod
    def dfile(cls):
        return None
    @classmethod
    def get(cls, **kwargs):
        ddir = kwargs.get('data_dir', data_dir)
        loader = TestData(data_dir=ddir)
        return loader.load(cls.dfile(), **kwargs)

class HEAD(DATA):
    @classmethod
    def dfile(cls):
        return TestData.HEAD


class TestData(object):
    '''Class to return test data
    
    provides 1 dataset:
    HEAD = 'headsq/quarter.nhdr'
    '''
    HEAD = 'headsq/quarter'
    
    def __init__(self, **kwargs):
        self.data_dir = kwargs.get('data_dir', data_dir)
        
    def load(self, which, **kwargs):
        '''
        Return a test data of the requested image

        Parameters
        ----------
        which: str
           Image selector: HEAD

        Returns
        -------
        vtkImageData
            The loaded dataset
        '''
        if which not in [TestData.HEAD]:
            raise ValueError('Unknown TestData {}.'.format(which))

        data_file = os.path.join(self.data_dir, which)

        reader = vtk.vtkImageReader2()
        reader.SetFilePrefix(data_file)
        reader.SetDataExtent(0, 63, 0, 63, 1, 93)
        reader.SetDataSpacing(3.2, 3.2, 1.5)
        reader.SetDataOrigin(0.0, 0.0, 0.0)
        reader.SetDataScalarTypeToUnsignedShort()
        reader.UpdateWholeExtent()
        reader.Update()
        return reader.GetOutput()
