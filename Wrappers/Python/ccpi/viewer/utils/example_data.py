import os
import os.path
import vtk
import sys

# this is the default location after pip install
data_dir = os.path.abspath(os.path.join(sys.prefix, 'share', 'cil'))


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
    HEAD = 'head.mha'
    '''
    HEAD = 'head.mha'

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

        reader = vtk.vtkMetaImageReader()
        reader.SetFileName(data_file)
        reader.Update()
        return reader.GetOutput()
