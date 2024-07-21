import maya.cmds as cmds
import maya.OpenMayaUI as omui
from PySide2 import QtCore, QtWidgets
from PySide2.QtGui import QColor, QPalette
from shiboken2 import wrapInstance
import os
import subprocess
import platform

def get_maya_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)

def derive_output_path(scene_path):
    base_name = os.path.basename(scene_path)
    dir_name = os.path.dirname(scene_path).replace("\\", "/")
    
    # Move up to the "shots" directory and replace "tasks/anim" with "outputs/anim"
    parts = dir_name.split("/")
    if "tasks" in parts:
        tasks_index = parts.index("tasks")
        parts = parts[:tasks_index] + ["outputs", "anim"] + parts[tasks_index+2:]

    task_folder = "/".join(parts)
    task_folder = os.path.join(task_folder, base_name.split('.')[0])
    task_folder = os.path.normpath(task_folder).replace("\\", "/")
    output_file = os.path.join(task_folder, base_name.split('.')[0] + ".abc")
    output_file = os.path.normpath(output_file).replace("\\", "/")
    
    return output_file

class AlembicExporter(QtWidgets.QDialog):
    def __init__(self, parent=get_maya_window()):
        super(AlembicExporter, self).__init__(parent)
        
        self.setWindowTitle("Alembic Exporter")
        self.setMinimumWidth(300)
        
        self.create_widgets()
        self.create_layout()
        self.create_connections()
        
        self.populate_geo_objects()
    
    def create_widgets(self):
        self.geo_list_widget = QtWidgets.QListWidget()
        self.playblast_checkbox = QtWidgets.QCheckBox("Generate Playblast (feature not yet implemented)")
        self.playblast_checkbox.setChecked(False)
        self.playblast_checkbox.setEnabled(False)  # Disable the checkbox
        self.pre_roll_spinner = QtWidgets.QSpinBox()
        self.pre_roll_spinner.setRange(0, 1000)
        self.pre_roll_spinner.setValue(50)
        self.post_roll_spinner = QtWidgets.QSpinBox()
        self.post_roll_spinner.setRange(0, 1000)
        self.post_roll_spinner.setValue(50)
        self.submit_button = QtWidgets.QPushButton("Submit")
        
        # Set the submit button color to light blue
        self.submit_button.setStyleSheet("QPushButton { background-color: #4285F4; color: white; }")
    
    def create_layout(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.geo_list_widget)
        layout.addWidget(self.playblast_checkbox)
        
        spinner_layout = QtWidgets.QHBoxLayout()
        spinner_layout.addWidget(QtWidgets.QLabel("Pre Roll Frames:"))
        spinner_layout.addWidget(self.pre_roll_spinner)
        spinner_layout.addWidget(QtWidgets.QLabel("Post Roll Frames:"))
        spinner_layout.addWidget(self.post_roll_spinner)
        
        layout.addLayout(spinner_layout)
        
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.submit_button)
        
        layout.addLayout(button_layout)
    
    def create_connections(self):
        self.submit_button.clicked.connect(self.on_submit)
    
    def populate_geo_objects(self):
        geo_objects = [obj for obj in cmds.ls(long=True) if obj.endswith('_GEO')]
        for obj in geo_objects:
            display_name = obj.split(":")[-1]  # Strip the namespace for display
            item = QtWidgets.QListWidgetItem(display_name)
            item.setCheckState(QtCore.Qt.Checked)
            item.setData(QtCore.Qt.UserRole, obj)  # Store the full object name with namespace
            self.geo_list_widget.addItem(item)
    
    def on_submit(self):
        selected_geo_objects = [self.geo_list_widget.item(i).data(QtCore.Qt.UserRole) for i in range(self.geo_list_widget.count()) if self.geo_list_widget.item(i).checkState() == QtCore.Qt.Checked]
        
        if not selected_geo_objects:
            QtWidgets.QMessageBox.warning(self, "No Objects Selected", "Please select at least one GEO object.")
            return
        
        # Check if in a valid task file
        if not self.is_valid_task_file():
            QtWidgets.QMessageBox.critical(self, "Invalid Task File", "The current scene file is not a valid task file.")
            return
        
        scene_path = cmds.file(query=True, sceneName=True)
        output_path = derive_output_path(scene_path)
        
        if os.path.exists(output_path):
            result = QtWidgets.QMessageBox.question(self, "File Exists", "The output file already exists. Do you want to override it?", QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            if result == QtWidgets.QMessageBox.No:
                return
        
        # Create the output directory if it doesn't exist
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Run the export process
        self.export_alembic(selected_geo_objects, output_path)
        
        if self.playblast_checkbox.isChecked():
            self.generate_playblast(output_dir)
        
        QtWidgets.QMessageBox.information(self, "Success", "Alembic export completed successfully.")
        
        # Open the output folder
        self.open_output_folder(output_dir)
    
    def is_valid_task_file(self):
        scene_path = cmds.file(query=True, sceneName=True)
        dir_name = os.path.dirname(scene_path).replace("\\", "/")
        parts = dir_name.split("/")
        
        # Check if the path contains exactly one period
        if scene_path.count(".") != 1:
            print(f"Debug: Scene path has {scene_path.count('.')} periods, expected 1")
            return False
        
        # Check if the directory two levels up is "tasks"
        if len(parts) < 3 or parts[-2] != "tasks":
            print(f"Debug: Directory two levels up is {parts[-2] if len(parts) >= 2 else 'not available'}, expected 'tasks'")
            return False
        
        # Check if the immediate directory contains "anim"
        if "anim" not in parts[-1]:
            print(f"Debug: 'anim' not found in parts[-1], it is {parts[-1]}")
            return False
        
        return True
    
    def export_alembic(self, geo_objects, output_path):
        start_frame = cmds.playbackOptions(query=True, minTime=True)
        end_frame = cmds.playbackOptions(query=True, maxTime=True)
        
        pre_roll = self.pre_roll_spinner.value()
        post_roll = self.post_roll_spinner.value()
        
        # Adjust the timeline to accommodate pre and post roll frames
        original_start_frame = start_frame
        original_end_frame = end_frame
        new_start_frame = start_frame - pre_roll
        new_end_frame = end_frame + post_roll
        
        cmds.playbackOptions(minTime=new_start_frame, maxTime=new_end_frame)
        
        cmds.select(geo_objects, replace=True)
        cmds.bakeResults(simulation=True, t=(new_start_frame, new_end_frame), sampleBy=1, oversamplingRate=1, disableImplicitControl=True,
                         preserveOutsideKeys=True, sparseAnimCurveBake=False, removeBakedAttributeFromLayer=False,
                         bakeOnOverrideLayer=False, minimizeRotation=True, controlPoints=False, shape=True)
        
        abc_export_command = '-frameRange {0} {1} -uvWrite -worldSpace -writeVisibility -dataFormat ogawa'.format(
            new_start_frame, new_end_frame)
        
        for obj in geo_objects:
            abc_export_command += ' -root ' + obj
        
        # Add quotes around the output path to handle spaces
        abc_export_command += ' -file "{}"'.format(output_path)
        cmds.AbcExport(j=abc_export_command)
        
        # Restore the original timeline
        cmds.playbackOptions(minTime=original_start_frame, maxTime=original_end_frame)
    
    def generate_playblast(self, output_dir):
        # Placeholder for playblast generation logic
        pass

    def open_output_folder(self, path):
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

if __name__ == "__main__":
    try:
        exporter_ui.close() # pylint: disable=E0601
        exporter_ui.deleteLater()
    except:
        pass
    
    exporter_ui = AlembicExporter()
    exporter_ui.show()
