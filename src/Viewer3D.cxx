#include "Viewer3D.h"




int main(int, char*[])
{
  vtkNew<vtkNamedColors> colors;

  // Set the background color.
  std::array<unsigned char, 4> bkg{{26, 51, 102, 255}};
  // colors->SetColor("BkgColor", bkg.data());

  // This creates a polygonal cylinder model with eight circumferential facets
  // (i.e, in practice an octagonal prism).
  vtkNew<vtkCylinderSource> cylinder;
  cylinder->SetResolution(8);

  // The mapper is responsible for pushing the geometry into the graphics
  // library. It may also do color mapping, if scalars or other attributes are
  // defined.
  vtkNew<vtkPolyDataMapper> cylinderMapper;
  cylinderMapper->SetInputConnection(cylinder->GetOutputPort());

  // The actor is a grouping mechanism: besides the geometry (mapper), it
  // also has a property, transformation matrix, and/or texture map.
  // Here we set its color and rotate it around the X and Y axes.
  vtkNew<vtkActor> cylinderActor;
  cylinderActor->SetMapper(cylinderMapper);
  cylinderActor->GetProperty()->SetColor(0.8, 0.1, 0.1);
  cylinderActor->RotateX(30.0);
  cylinderActor->RotateY(-45.0);

  // The renderer generates the image
  // which is then displayed on the render window.
  // It can be thought of as a scene to which the actor is added
  vtkNew<vtkRenderer> renderer;
  renderer->AddActor(cylinderActor);
  renderer->SetBackground(0.1,0.2,0.4);
  // Zoom in a little by accessing the camera and invoking its "Zoom" method.
  renderer->ResetCamera();
  renderer->GetActiveCamera()->Zoom(1.5);

  // The render window is the actual GUI window
  // that appears on the computer screen
  vtkNew<vtkRenderWindow> renderWindow;
  renderWindow->SetSize(300, 300);
  renderWindow->AddRenderer(renderer);
  renderWindow->SetWindowName("Cylinder");

  // The render window interactor captures mouse events
  // and will perform appropriate camera or actor manipulation
  // depending on the nature of the events.
  vtkNew<vtkRenderWindowInteractor> renderWindowInteractor;
  renderWindowInteractor->SetRenderWindow(renderWindow);

  // applies the interactor style trackball camera
  vtkNew<vtkInteractorStyleTrackballCamera> style;
  renderWindowInteractor->SetInteractorStyle(style);

  // This starts the event loop and as a side effect causes an initial render.
  renderWindow->Render();

  renderWindowInteractor->Start();

  return EXIT_SUCCESS;
}
