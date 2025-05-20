from eqt.ui import FormDialog, UISliderWidget
from PySide2 import QtCore, QtWidgets, QtGui

from ccpi.viewer.utils.settings_tooltips import TOOLTIPS_VOLUME_RENDER_SETTINGS
from ccpi.viewer.ui.helpers import color_scheme_list


class VolumeRenderSettingsDialog(FormDialog):
    """
    A FormDialog listing the viewer's volume render settings.
    """

    def __init__(self, parent=None, viewer=None, title=None):
        """
        Creates the FormDialog and sets up the form's widgets.
        The widgets are enabled if image data has been loaded in the viewer.
        Otherwise, the widgets are disabled. 

        viewer: The CILViewer instance that the dialog's settings will connect to.
        """
        FormDialog.__init__(self, parent, title=title)
        self.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, True)
        self.viewer = viewer

        self._setUpVolumeVisibility()
        self._setUpWindowingMin()
        self._setUpWindowingMax()
        self._setUpOpacityMapping()
        self._setUpColourScheme()
        self._setUpVolumeClipping()
        self._setUpColourRangeMin()
        self._setUpColourRangeMax()
        self._setUpMaxOpacity()

        self.toggleVolumeVisibility(is_init=True)

    def _setUpVolumeVisibility(self):
        """
        Configures the Volume Visibility QCheckBox, which both controls the visibility of the volume and
        enables/disables the dialog's settings widgets.
        
        If no image data has been loaded in the viewer, the QCheckBox will be unticked and disabled.
        """
        volume_visibility = QtWidgets.QCheckBox("Render 3D Volume", self.groupBox)

        self.addWidget(volume_visibility, "", "volume_visibility")
        self.formWidget.widgets["volume_visibility_field"].setToolTip(
            TOOLTIPS_VOLUME_RENDER_SETTINGS["volume_visibility"])
        
        if self.viewer.img3D is None:
            self.getWidget("volume_visibility").setChecked(False)
            self.getWidget("volume_visibility").setEnabled(False)
        else:
            self.getWidget("volume_visibility").setChecked(False)
        
        self.getWidget("volume_visibility").stateChanged.connect(self.toggleVolumeVisibility)

    def _setUpWindowingMin(self):
        windowing_slider_min = UISliderWidget.UISliderWidget(0.0, 100.0)

        self.addWidget(windowing_slider_min, "Windowing Minimum (%):", "windowing_slider_min")
        self.formWidget.widgets["windowing_slider_min_label"].setToolTip(
            TOOLTIPS_VOLUME_RENDER_SETTINGS["windowing_slider_min"])

        self.getWidget("windowing_slider_min").setValue(80)
        self.getWidget("windowing_slider_min").slider.valueChanged.connect(self.updateVolumeOpacityMin)
        self.getWidget("windowing_slider_min").line_edit.editingFinished.connect(self.updateVolumeOpacityMin)

    def _setUpWindowingMax(self):
        windowing_slider_max = UISliderWidget.UISliderWidget(0.0, 100.0)

        self.addWidget(windowing_slider_max, "Windowing Maximum (%):", "windowing_slider_max")
        self.formWidget.widgets["windowing_slider_max_label"].setToolTip(
            TOOLTIPS_VOLUME_RENDER_SETTINGS["windowing_slider_max"])

        self.getWidget("windowing_slider_max").setValue(99)
        self.getWidget("windowing_slider_max").slider.valueChanged.connect(self.updateVolumeOpacityMax)
        self.getWidget("windowing_slider_max").line_edit.editingFinished.connect(self.updateVolumeOpacityMax)

    def _setUpOpacityMapping(self):
        opacity_mapping = QtWidgets.QComboBox(self.groupBox)

        opacity_mapping.addItems(["Scalar", "Gradient"])
        self.addWidget(opacity_mapping, "Opacity Mapping:", "opacity_mapping")
        self.formWidget.widgets["opacity_mapping_label"].setToolTip(TOOLTIPS_VOLUME_RENDER_SETTINGS["opacity_mapping"])

        self.getWidget("opacity_mapping").currentIndexChanged.connect(self.setOpacityMapping)

    def _setUpColourScheme(self):
        colour_scheme = QtWidgets.QComboBox(self.groupBox)

        colour_scheme.addItems(color_scheme_list())
        self.addWidget(colour_scheme, "Colour Scheme:", "colour_scheme")
        self.formWidget.widgets["colour_scheme_label"].setToolTip(TOOLTIPS_VOLUME_RENDER_SETTINGS["colour_scheme"])

        self.getWidget("colour_scheme").currentIndexChanged.connect(self.setColourScheme)

    def _setUpVolumeClipping(self):
        volume_clipping = QtWidgets.QCheckBox("Volume Clipping", self.groupBox)
        volume_clipping_reset = QtWidgets.QPushButton("Reset Volume Clipping", self.groupBox)

        self.addWidget(volume_clipping, "", "volume_clipping")
        self.addWidget(volume_clipping_reset, "", "volume_clipping_reset")
        self.formWidget.widgets["volume_clipping_field"].setToolTip(TOOLTIPS_VOLUME_RENDER_SETTINGS["volume_clipping"])
        self.formWidget.widgets["volume_clipping_reset_field"].setToolTip(
            TOOLTIPS_VOLUME_RENDER_SETTINGS["volume_clipping_reset"])

        self.getWidget("volume_clipping").stateChanged.connect(self.viewer.style.ToggleVolumeClipping)
        self.getWidget("volume_clipping_reset").clicked.connect(self.resetVolumeClipping)

    def _setUpColourRangeMin(self):
        colour_range_slider_min = UISliderWidget.UISliderWidget(0.0, 100.0)

        self.addWidget(colour_range_slider_min, "Colour Range Minimum (%):", "colour_range_slider_min")
        self.formWidget.widgets["colour_range_slider_min_label"].setToolTip(
            TOOLTIPS_VOLUME_RENDER_SETTINGS["colour_range_slider_min"])

        self.getWidget("colour_range_slider_min").setValue(85)
        self.getWidget("colour_range_slider_min").slider.valueChanged.connect(self.updateColourRangeMin)
        self.getWidget("colour_range_slider_min").line_edit.editingFinished.connect(self.updateColourRangeMin)

    def _setUpColourRangeMax(self):
        colour_range_slider_max = UISliderWidget.UISliderWidget(0.0, 100.0)

        self.addWidget(colour_range_slider_max, "Colour Range Maximum (%):", "colour_range_slider_max")
        self.formWidget.widgets["colour_range_slider_max_label"].setToolTip(
            TOOLTIPS_VOLUME_RENDER_SETTINGS["colour_range_slider_max"])

        self.getWidget("colour_range_slider_max").setValue(95)
        self.getWidget("colour_range_slider_max").slider.valueChanged.connect(self.updateColourRangeMax)
        self.getWidget("colour_range_slider_max").line_edit.editingFinished.connect(self.updateColourRangeMax)

    def _setUpMaxOpacity(self):
        max_opacity_input = UISliderWidget.UISliderWidget(0.0, 100.0, decimals=3)

        self.addWidget(max_opacity_input, "Maximum Opacity (%):", "max_opacity_input")
        self.formWidget.widgets["max_opacity_input_label"].setToolTip(
            TOOLTIPS_VOLUME_RENDER_SETTINGS["max_opacity_input"])

        self.getWidget("max_opacity_input").setValue(self.viewer.style.GetVolumeRenderParameters()['max_opacity'] * 100)
        self.getWidget("max_opacity_input").slider.valueChanged.connect(self.setVolumeMaxOpacity)
        self.getWidget("max_opacity_input").line_edit.editingFinished.connect(self.setVolumeMaxOpacity)

    def updateColourRangeMin(self):
        """
        Updates the volume colour_range_slider_min value if it is greater 
        than or equal to the value of the colour_range_slider_max value.
        """
        if self.getWidget("colour_range_slider_min").value() >= self.getWidget("colour_range_slider_max").value():
            self.getWidget("colour_range_slider_min").setValue(self.getWidget("colour_range_slider_max").value() - 1)
        self.setColourRange()

    def updateColourRangeMax(self):
        """
        Updates the volume colour_range_slider_max value if it is less
        than or equal to the value of the colour_range_slider_min value.
        """
        if self.getWidget("colour_range_slider_max").value() <= self.getWidget("colour_range_slider_min").value():
            self.getWidget("colour_range_slider_max").setValue(self.getWidget("colour_range_slider_min").value() + 1)
        self.setColourRange()

    def setColourRange(self):
        """
        Sets the viewer's volume colour range using the values from
        the min/max colour range sliders.
        """
        self.viewer.setVolumeColorPercentiles(
            self.getWidget("colour_range_slider_min").value(),
            self.getWidget("colour_range_slider_max").value())

    def updateVolumeOpacityMin(self):
        """
        Updates the volume opacity (windowing) minimum slider value if it is greater 
        than or equal to the value of the volume opacity maximum slider.
        """
        if self.getWidget("windowing_slider_min").value() >= self.getWidget("windowing_slider_max").value():
            self.getWidget("windowing_slider_min").setValue(self.getWidget("windowing_slider_max").value() - 1)
        self.setVolumeOpacity()

    def updateVolumeOpacityMax(self):
        """
        Updates the volume opacity (windowing) maximum slider value if it is less 
        than or equal to the value of the volume opacity minimum slider.
        """
        if self.getWidget("windowing_slider_max").value() <= self.getWidget("windowing_slider_min").value():
            self.getWidget("windowing_slider_max").setValue(self.getWidget("windowing_slider_min").value() + 1)
        self.setVolumeOpacity()

    def setVolumeOpacity(self):
        """
        Sets the viewer's volume opacity mapping using the values from
        the min/max volume opacity (windowing) sliders.
        """
        opacity = self.getWidget("opacity_mapping").currentText()
        opacity_min, opacity_max = (self.getWidget("windowing_slider_min").value(),
                                    self.getWidget("windowing_slider_max").value())
        if opacity == "Gradient":
            self.viewer.setGradientOpacityPercentiles(opacity_min, opacity_max)
        elif opacity == "Scalar":
            self.viewer.setScalarOpacityPercentiles(opacity_min, opacity_max)

    def setVolumeMaxOpacity(self):
        """
        Sets the viewer's volume opacity mapping maximum value.
        """
        mo = self.getWidget("max_opacity_input").value() / 100
        self.viewer.setMaximumOpacity(mo)

    def resetVolumeClipping(self):
        """
        Resets the viewer's volume clipping to the default state.
        """
        self.getWidget("volume_clipping").setChecked(False)
        if self.viewer.volume_render_initialised:
            if self.viewer.volume.GetMapper().GetClippingPlanes() is not None:
                self.viewer.volume.GetMapper().RemoveAllClippingPlanes()
        if self.viewer.clipping_plane_initialised:
            self.viewer.style.SetVolumeClipping(False)
            self.removeClippingPlane()

    def removeClippingPlane(self):
        """
        Removes the clipping plane from the viewer.
        """
        if hasattr(self.viewer, "planew"):
            self.viewer.removeClippingPlane()
            self.viewer.getRenderer().Render()
            self.viewer.updatePipeline()

    def toggleVolumeVisibility(self, is_init=False):
        """
        Toggles the volume visibility in the viewer. The volume visibility QCheckBox
        determines whether the dialog's widgets are enabled/disabled.

        is_init: Boolean value that limits the method's behaviour when the dialog is created.
        """
        volume_visibility_checked = self.getWidget("volume_visibility").isChecked()

        self.getWidget("windowing_slider_min").setEnabled(volume_visibility_checked)
        self.getWidget("windowing_slider_max").setEnabled(volume_visibility_checked)
        self.getWidget("opacity_mapping").setEnabled(volume_visibility_checked)
        self.getWidget("colour_scheme").setEnabled(volume_visibility_checked)
        self.getWidget("volume_clipping").setEnabled(volume_visibility_checked)
        self.getWidget("volume_clipping_reset").setEnabled(volume_visibility_checked)
        self.getWidget("colour_range_slider_min").setEnabled(volume_visibility_checked)
        self.getWidget("colour_range_slider_max").setEnabled(volume_visibility_checked)
        self.getWidget("max_opacity_input").setEnabled(volume_visibility_checked)

        if is_init is True:
            return
        else:
            self.viewer.style.ToggleVolumeVisibility()

            if volume_visibility_checked:
                self.setOpacityMapping()
                if self.getWidget("volume_clipping").isChecked() and hasattr(self.viewer, "planew"):
                    self.viewer.planew.On()
                    self.viewer.updatePipeline()
            elif hasattr(self.viewer, "planew"):
                self.viewer.planew.Off()
                self.viewer.updatePipeline()
                print("Volume visibility off")

            self.viewer.updateVolumePipeline()

    def setOpacityMapping(self):
        """
        Sets the viewer's opacity mapping method.
        """
        method = self.getWidget("opacity_mapping").currentText().lower()
        self.viewer.setVolumeRenderOpacityMethod(method)
        self.viewer.updateVolumePipeline()

    def setColourScheme(self):
        """
        Sets the viewer's volume colour scheme.
        """
        colour_scheme = self.getWidget("colour_scheme").currentText()
        self.viewer.setVolumeColorMapName(colour_scheme)
        self.viewer.updateVolumePipeline()

    def getSettings(self):
        """
        Returns a dictionary of widget settings from the dialog.
        """
        settings = {}
        for key, value in self.formWidget.widgets.items():
            if isinstance(value, QtWidgets.QLabel):
                settings[key] = value.text()
            elif isinstance(value, QtWidgets.QCheckBox):
                settings[key] = value.isChecked()
            elif isinstance(value, QtWidgets.QComboBox):
                settings[key] = value.currentIndex()
            elif isinstance(value, UISliderWidget.UISliderWidget):
                settings[key] = value.value()
        return settings

    def applySettings(self, settings):
        """
        Applies the widget settings to the dialog.

        settings: A dictionary of widget names and their associated state/value.
        """
        for key, value in settings.items():
            widg = self.formWidget.widgets[key]
            if isinstance(widg, QtWidgets.QLabel):
                widg.setText(value)
            elif isinstance(widg, QtWidgets.QCheckBox):
                widg.setChecked(value)
            elif isinstance(widg, QtWidgets.QComboBox):
                widg.setCurrentIndex(value)
            elif isinstance(widg, UISliderWidget.UISliderWidget):
                widg.setValue(value)