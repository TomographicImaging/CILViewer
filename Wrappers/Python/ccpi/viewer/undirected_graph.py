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


class GraphInteractorStyle(vtk.vtkInteractorStyleRubberBand2D):

    def __init__(self, callback):
        vtk.vtkInteractorStyleRubberBand2D.__init__(self)
        self._viewer = callback

        self.AddObserver("MouseMoveEvent", self.OnMouseMoveEvent, 1.0)

    def GetEventPosition(self):
        return self.GetInteractor().GetEventPosition()

    def GetRenderer(self):
        return self._viewer.GetRenderer()

    def Render(self):
        self._viewer.Render()

    def display2world(self, viewerposition):
        vc = vtk.vtkCoordinate()
        vc.SetCoordinateSystemToViewport()
        vc.SetValue(viewerposition + (0.0, ))

        return vc.GetComputedWorldValue(self.GetRenderer())

    def OnMouseMoveEvent(self, interactor, event):
        position = interactor.GetInteractor().GetEventPosition()
        world_position = self.display2world(position)
        level = world_position[1] * 100

        # Don't display values outside the graph scope
        if level < 0:
            level = 0
        if level > 100:
            level = 100

        # Create the label
        point_label = "Level: {:.1f} %".format(level)

        # Set the label and push change
        self.updateCornerAnnotation('pointAnnotation', point_label)
        self.Render()


class UndirectedGraph(vtkGraphLayoutView):

    annotations = {"featureAnnotation": 0, "pointAnnotation": 2}

    def __init__(self, renWin=None, iren=None):
        super().__init__()

        if renWin:
            self.renWin = renWin
        else:
            self.renWin = vtk.vtkRenderWindow()
        if iren:
            self.iren = iren
        else:
            self.iren = vtk.vtkRenderWindowInteractor()

        self.SetRenderWindow(self.renWin)
        self.SetInteractor(self.iren)

        # Add observer to display level.
        self.iren.AddObserver("MouseMoveEvent", self.OnMouseMoveEvent, 1.)

        # Create corner annotations
        self.featureAnnotation = self.createCornerAnnotation()
        self.pointAnnotation = self.createCornerAnnotation()

    def update(self, input_data):

        # Create layout strategy
        layoutStrategy = vtk.vtkAssignCoordinatesLayoutStrategy()
        layoutStrategy.SetYCoordArrayName('Y')
        layoutStrategy.SetXCoordArrayName('X')

        self.AddRepresentationFromInput(input_data)
        self.SetVertexLabelArrayName("VertexID")
        self.SetVertexLabelVisibility(True)

        self.SetLayoutStrategy(layoutStrategy)

        annotation_link = vtk.vtkAnnotationLink()
        annotation_link.AddObserver("AnnotationChangedEvent", self.select_callback)
        self.GetRepresentation(0).SetAnnotationLink(annotation_link)
        self.GetRepresentation(0).SetScalingArrayName('VertexID')
        self.GetRepresentation(0).ScalingOn()

        self.ResetCamera()
        self.Render()

    def createCornerAnnotation(self):
        cornerAnnotation = vtk.vtkCornerAnnotation()
        cornerAnnotation.SetMaximumFontSize(12)
        cornerAnnotation.PickableOff()
        cornerAnnotation.VisibilityOff()
        cornerAnnotation.GetTextProperty().ShadowOn()
        self.GetRenderer().AddActor(cornerAnnotation)

        return cornerAnnotation

    def updateCornerAnnotation(self, target_annotation, label):

        annotation = getattr(self, target_annotation)

        # Make sure the annotation is visible
        if not annotation.GetVisibility():
            annotation.VisibilityOn()

        # Get the correct corner
        corner_index = self.annotations[target_annotation]
        annotation.SetText(corner_index, label)

    def run(self, input_data):
        self.update(input_data)
        self.GetInteractor().Start()

    ######### INTERACTOR CALBACKS #########
    def select_callback(self, interactor, event):
        sel = interactor.GetCurrentSelection()

        for nn in range(sel.GetNumberOfNodes()):
            sel_ids = sel.GetNode(nn).GetSelectionList()
            if sel_ids.GetNumberOfTuples() > 0:
                for ii in range(sel_ids.GetNumberOfTuples()):
                    print(int(sel_ids.GetTuple1(ii)))

    def display2world(self, viewerposition):
        vc = vtk.vtkCoordinate()
        vc.SetCoordinateSystemToViewport()
        vc.SetValue(viewerposition + (0.0, ))

        return vc.GetComputedWorldValue(self.GetRenderer())

    def OnMouseMoveEvent(self, interactor, event):

        # Allow default behaviour
        interactor.GetInteractorStyle().OnMouseMove()

        position = interactor.GetEventPosition()
        world_position = self.display2world(position)
        level = world_position[1] * 100

        # Don't display values outside the graph scope
        if level < 0:
            level = 0
        if level > 100:
            level = 100

        # Create the label
        point_label = "Level: {:.1f} %".format(level)

        # Set the label and push change
        self.updateCornerAnnotation('pointAnnotation', point_label)
        self.Render()


if __name__ == "__main__":
    UndirectedGraph().run(generate_data())
