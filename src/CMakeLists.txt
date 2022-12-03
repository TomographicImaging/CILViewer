
# Prevent a "command line is too long" failure in Windows.
set(CMAKE_NINJA_FORCE_RESPONSE_FILE "ON" CACHE BOOL "Force Ninja to use response files.")

message(STATUS "FOUND VTK LIBRARIES" ${VTK_LIBRARIES})
add_executable(Viewer3D MACOSX_BUNDLE Viewer3D.cxx )
  target_link_libraries(Viewer3D PRIVATE ${VTK_LIBRARIES}
)

target_include_directories(Viewer3D PRIVATE ${CMAKE_CURRENT_SOURCE_DIR}/include)

# vtk_module_autoinit is needed
vtk_module_autoinit(
  TARGETS Viewer3D
  MODULES ${VTK_LIBRARIES}
)

add_subdirectory(Wrapping)