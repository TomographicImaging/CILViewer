# -*- coding: utf-8 -*-
"""
Created on Sat May 12 13:35:53 2018

@author: ofn77899
"""

import vtk
from vtk import vtkGraphLayoutView


def generate_data():
    g = vtk.vtkMutableDirectedGraph()

    # add vertices
    v = []
    for i in range(6):
        v.append(g.AddVertex())

    g.AddEdge(v[0], v[1])
    g.AddEdge(v[1], v[2])
    g.AddEdge(v[1], v[3])
    g.AddEdge(v[0], v[4])
    g.AddEdge(v[0], v[5])

    weights = vtk.vtkDoubleArray()
    weights.SetNumberOfComponents(1)
    weights.SetName("Weights")

    X = vtk.vtkDoubleArray()
    X.SetNumberOfComponents(1)
    X.SetName("X")

    Y = vtk.vtkDoubleArray()
    Y.SetNumberOfComponents(1)
    Y.SetName("Y")

    X.InsertNextValue(0)
    X.InsertNextValue(0)
    X.InsertNextValue(1)
    X.InsertNextValue(-1)
    X.InsertNextValue(0.5)
    X.InsertNextValue(-0.5)

    Y.InsertNextValue(0)
    Y.InsertNextValue(1)
    Y.InsertNextValue(1.5)
    Y.InsertNextValue(2)
    Y.InsertNextValue(-.5)
    Y.InsertNextValue(-.8)

    weights.InsertNextValue(1.)
    weights.InsertNextValue(2.)
    weights.InsertNextValue(3.)
    weights.InsertNextValue(4.)
    weights.InsertNextValue(5.)

    g.GetEdgeData().AddArray(weights)
    g.GetVertexData().AddArray(X)
    g.GetVertexData().AddArray(Y)

    return g


class UndirectedGraph(vtkGraphLayoutView):

    def __init__(self, renWin=None, iren=None):
        super().__init__()

        if renWin:
            self.SetRenderWindow(renWin)

        if iren:
            self.SetInteractor(iren)

        # Create layout strategy
        layoutStrategy = vtk.vtkAssignCoordinatesLayoutStrategy()
        layoutStrategy.SetYCoordArrayName('Y')
        layoutStrategy.SetXCoordArrayName('X')

        self.SetLayoutStrategy(layoutStrategy)
        self.SetVertexLabelVisibility(True)
        self.SetEdgeLabelVisibility(True)

    def update(self, input_data):
        self.AddRepresentationFromInput(input_data)
        self.SetEdgeLabelArrayName("Weights")
        self.ResetCamera()
        self.Render()

    def run(self, input_data):
        self.update(input_data)
        self.GetInteractor().Start()

if __name__ == "__main__":
    UndirectedGraph().run(generate_data())
