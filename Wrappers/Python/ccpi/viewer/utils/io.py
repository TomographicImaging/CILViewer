
import glob
import os
import re

import vtk


def SaveRenderToPNG(render_window, filename):
    ''' Saves contents of a vtk render window
    to a PNG file.

    Parameters
    ----------
    render_window: vtkRenderWindow
        render window to save contents of.
    filename: str
        name of file to write PNG to.
    '''
    w2if = vtk.vtkWindowToImageFilter()
    w2if.SetInput(render_window)
    w2if.Update()

    basename = os.path.splitext(os.path.basename(filename))[0]
    # Note regex matching is different to glob matching:
    regex = '{}_([0-9]*)\.png'.format(basename)
    fname_string = '{}_{}.png'.format(basename, '[0-9]*')
    directory = os.path.dirname(filename)
    slist = []

    for el in glob.glob(os.path.join(directory, fname_string)):
        el = os.path.basename(el)
        slist.append(int(re.search(regex, el).group(1)))

    if len(slist) == 0:
        number = 0
    else:
        number = max(slist)+1

    saveFilename = '{}_{:04d}.png'.format(os.path.join(directory, basename), number)

    writer = vtk.vtkPNGWriter()
    writer.SetFileName(saveFilename)
    writer.SetInputConnection(w2if.GetOutputPort())
    writer.Write()
