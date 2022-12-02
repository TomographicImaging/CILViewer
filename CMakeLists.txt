cmake_minimum_required(VERSION 3.12 FATAL_ERROR)

project(CylinderExample)

find_package(VTK COMPONENTS 
  CommonColor
  CommonCore
  FiltersSources
  InteractionStyle
  RenderingContextOpenGL2
  RenderingCore
  RenderingFreeType
  RenderingGL2PSOpenGL2
  RenderingOpenGL2
)

if (NOT VTK_FOUND)
  message(FATAL_ERROR "CylinderExample: Unable to find the VTK build folder.")
endif()

add_subdirectory(src)
