from eqt.ui import FormDialog, UISliderWidget
from PySide2 import QtCore, QtWidgets, QtGui

from ccpi.viewer.ui.helpers import color_scheme_list


class VolumeRenderSettingsDialog(FormDialog):
    """Volume render settings dialogue."""

    def __init__(self, parent=None, title=None, scale_factor=1):
        FormDialog.__init__(self, parent, title=title)
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, True)

        # 3D Volume visibility
        volume_visibility = QtWidgets.QCheckBox("3D Volume Visibility", self.groupBox)
        self.addWidget(volume_visibility, "", "volume_visibility")

        self.scale_factor = scale_factor
        # Windowing min
        windowing_slider_min = UISliderWidget.UISliderWidget(0.0, 100.0)
        self.addWidget(windowing_slider_min, "Windowing min", "windowing_slider_min")

        # Windowing max
        windowing_slider_max = UISliderWidget.UISliderWidget(0.0, 100.0)
        self.addWidget(windowing_slider_max, "Windowing max", "windowing_slider_max")

        # Opacity mapping
        opacity_mapping = QtWidgets.QComboBox(self.groupBox)
        opacity_mapping.addItems(["Scalar", "Gradient"])
        self.addWidget(opacity_mapping, "Opacity mapping", "opacity_mapping")

        # Color scheme
        color_scheme = QtWidgets.QComboBox(self.groupBox)
        color_scheme.addItems(color_scheme_list())
        self.addWidget(color_scheme, "Color scheme", "color_scheme")

        # Volume clipping
        volume_clipping = QtWidgets.QCheckBox("Volume clipping", self.groupBox)
        self.addWidget(volume_clipping, "", "volume_clipping")
        volume_clipping_reset = QtWidgets.QPushButton("Reset volume clipping", self.groupBox)
        self.addWidget(volume_clipping_reset, "", "volume_clipping_reset")

        # Color range min
        color_range_slider_min = UISliderWidget.UISliderWidget(0.0, 100.0)
        self.addWidget(color_range_slider_min, "Color range min", "color_range_slider_min")

        # Color range max
        color_range_slider_max = UISliderWidget.UISliderWidget(0.0, 100.0)
        self.addWidget(color_range_slider_max, "Color range max", "color_range_slider_max")

        # Max opacity
        max_opacity_label = QtWidgets.QLabel("Max opacity")
        max_opacity_input = QtWidgets.QDoubleSpinBox(self.groupBox)
        self.addWidget(max_opacity_input, max_opacity_label, "max_opacity_input")

        # Disable 3D related widgets if volume visibility is not checked
        volume_visibility_checked = self.getWidget("volume_visibility").isChecked()
        self.getWidget("opacity_mapping").setEnabled(volume_visibility_checked)
        self.getWidget("color_scheme").setEnabled(volume_visibility_checked)
        self.getWidget("volume_clipping").setEnabled(volume_visibility_checked)
        self.getWidget("volume_clipping_reset").setEnabled(volume_visibility_checked)
        self.getWidget("color_range_slider_min").setEnabled(volume_visibility_checked)
        self.getWidget("color_range_slider_max").setEnabled(volume_visibility_checked)
        self.getWidget("windowing_slider_min").setEnabled(volume_visibility_checked)
        self.getWidget("windowing_slider_max").setEnabled(volume_visibility_checked)

    def set_viewer(self, viewer):
        """Attach the events to the viewer."""
        self.viewer = viewer

        # Volume visibility
        self.getWidget("volume_visibility").stateChanged.connect(self.toggle_volume_visibility)

        # Opacity mapping
        self.getWidget("opacity_mapping").currentIndexChanged.connect(self.change_opacity_mapping)

        # Color scheme
        self.getWidget("color_scheme").currentIndexChanged.connect(self.change_color_scheme)

        # Volume clipping
        self.getWidget("volume_clipping").stateChanged.connect(self.viewer.style.ToggleVolumeClipping)

        # Reset volume clipping
        self.getWidget("volume_clipping_reset").clicked.connect(self.reset_volume_clipping)

        # Color range slider min
        self.getWidget("color_range_slider_min").setValue(85)
        self.getWidget("color_range_slider_min").slider.sliderReleased.connect(self.change_color_range_min)

        # Color range slider max
        self.getWidget("color_range_slider_max").setValue(95)
        self.getWidget("color_range_slider_max").slider.sliderReleased.connect(self.change_color_range_max)

        # Windowing slider min
        self.getWidget("windowing_slider_min").setValue(80)
        self.getWidget("windowing_slider_min").slider.sliderReleased.connect(self.change_volume_opacity_min)

        # Windowing slider max
        self.getWidget("windowing_slider_max").setValue(99)
        self.getWidget("windowing_slider_max").slider.sliderReleased.connect(self.change_volume_opacity_max)

        # MaxOpacity spinbox max
        self.getWidget("max_opacity_input").setRange(0, 1)
        self.getWidget("max_opacity_input").setDecimals(3)
        self.getWidget("max_opacity_input").setValue(viewer.style.GetVolumeRenderParameters()['max_opacity'])
        self.getWidget("max_opacity_input").valueChanged.connect(self.change_volume_max_opacity)

    def change_color_range_min(self):
        """Change the volume color range min value."""
        if self.getWidget("color_range_slider_min").value() >= self.getWidget("color_range_slider_max").value():
            self.getWidget("color_range_slider_min").setValue(self.getWidget("color_range_slider_max").value() - 1)

        self.change_color_range()

    def change_color_range_max(self):
        """Change the volume color range max value."""
        if self.getWidget("color_range_slider_max").value() <= self.getWidget("color_range_slider_min").value():
            self.getWidget("color_range_slider_max").setValue(self.getWidget("color_range_slider_min").value() + 1)
        self.change_color_range()

    def change_color_range(self):
        """Change the volume color range."""
        self.viewer.setVolumeColorPercentiles(
            self.getWidget("color_range_slider_min").value() / self.scale_factor,
            self.getWidget("color_range_slider_max").value() / self.scale_factor)

    def change_volume_opacity_min(self):
        """Change the volume opacity mapping min value."""
        if self.getWidget("windowing_slider_min").value() >= self.getWidget("windowing_slider_max").value():
            self.getWidget("windowing_slider_min").setValue(self.getWidget("windowing_slider_max").value() - 1)

        self.change_volume_opacity()

    def change_volume_opacity_max(self):
        """Change the volume opacity mapping."""
        if self.getWidget("windowing_slider_max").value() <= self.getWidget("windowing_slider_min").value():
            self.getWidget("windowing_slider_max").setValue(self.getWidget("windowing_slider_min").value() + 1)

        self.change_volume_opacity()

    def change_volume_opacity(self):
        """Change the volume opacity mapping"""
        opacity = self.getWidget("opacity_mapping").currentText()
        opacity_min, opacity_max = (
            self.getWidget("windowing_slider_min").value() / self.scale_factor,
            self.getWidget("windowing_slider_max").value() / self.scale_factor,
        )
        if opacity == "Gradient":
            self.viewer.setGradientOpacityPercentiles(opacity_min, opacity_max)
        elif opacity == "Scalar":
            self.viewer.setScalarOpacityPercentiles(opacity_min, opacity_max)

    def change_volume_max_opacity(self):
        """Change the volume opacity mapping max value."""
        mo = self.getWidget("max_opacity_input").value()
        self.viewer.setMaximumOpacity(mo)

    def reset_volume_clipping(self):
        """Reset the volume clipping to the default state."""
        self.getWidget("volume_clipping").setChecked(False)
        if self.viewer.volume_render_initialised:
            if self.viewer.volume.GetMapper().GetClippingPlanes() is not None:
                self.viewer.volume.GetMapper().RemoveAllClippingPlanes()
        if self.viewer.clipping_plane_initialised:
            self.viewer.style.SetVolumeClipping(False)
            self.remove_clipping_plane()

    def remove_clipping_plane(self):
        """Remove the clipping plane from the viewer."""
        if hasattr(self.viewer, "planew"):
            self.viewer.remove_clipping_plane()
            self.viewer.getRenderer().Render()
            self.viewer.updatePipeline()

    def get_settings(self):
        """Return a dictionary of settings from the dialog."""
        settings = {}
        for key, value in self.formWidget.widgets.items():
            if isinstance(value, QtWidgets.QLabel):
                settings[key] = value.text()
            elif isinstance(value, QtWidgets.QCheckBox):
                settings[key] = value.isChecked()
            elif isinstance(value, QtWidgets.QComboBox):
                settings[key] = value.currentIndex()

        return settings

    def apply_settings(self, settings):
        """Apply the settings to the dialog."""
        for key, value in settings.items():
            widg = self.formWidget.widgets[key]
            if isinstance(widg, QtWidgets.QLabel):
                widg.setText(value)
            elif isinstance(widg, QtWidgets.QCheckBox):
                widg.setChecked(value)
            elif isinstance(widg, QtWidgets.QComboBox):
                widg.setCurrentIndex(value)

    def toggle_volume_visibility(self):
        """Toggle volume visibility."""
        # Set 3D widgets enabled/disabled depending on volume visibility checkbox
        volume_visibility_checked = self.getWidget("volume_visibility").isChecked()
        self.getWidget("windowing_slider_min").setEnabled(volume_visibility_checked)
        self.getWidget("windowing_slider_max").setEnabled(volume_visibility_checked)
        self.getWidget("opacity_mapping").setEnabled(volume_visibility_checked)
        self.getWidget("color_scheme").setEnabled(volume_visibility_checked)
        self.getWidget("volume_clipping").setEnabled(volume_visibility_checked)
        self.getWidget("volume_clipping_reset").setEnabled(volume_visibility_checked)
        self.getWidget("color_range_slider_min").setEnabled(volume_visibility_checked)
        self.getWidget("color_range_slider_max").setEnabled(volume_visibility_checked)

        self.viewer.style.ToggleVolumeVisibility()

        if volume_visibility_checked:
            self.change_opacity_mapping()
            if self.getWidget("volume_clipping").isChecked() and hasattr(self.viewer, "planew"):
                print("Volume visibility on")
                self.viewer.planew.On()
                self.viewer.updatePipeline()
        elif hasattr(self.viewer, "planew"):
            self.viewer.planew.Off()
            self.viewer.updatePipeline()
            print("Volume visibility off")

        self.viewer.updateVolumePipeline()

    def change_opacity_mapping(self):
        """Change opacity mapping method."""
        method = self.getWidget("opacity_mapping").currentText().lower()
        self.viewer.setVolumeRenderOpacityMethod(method)
        self.viewer.updateVolumePipeline()

    def change_color_scheme(self):
        """Change color scheme."""
        color_scheme = self.getWidget("color_scheme").currentText()
        self.viewer.setVolumeColorMapName(color_scheme)
        self.viewer.updateVolumePipeline()
