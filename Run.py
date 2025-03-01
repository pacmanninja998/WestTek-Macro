import sys
import os
import json
import time
import psutil
import threading
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QPushButton, QLabel, QListWidget, 
                           QTabWidget, QFormLayout, QLineEdit, QMessageBox,
                           QToolTip, QGroupBox, QScrollArea, QFrame, QSplitter,
                           QDialog)
from PyQt5.QtCore import Qt, QSize, pyqtSlot
from PyQt5.QtGui import QFont, QIcon, QKeyEvent, QMouseEvent

# Import the script classes
from PrimaryAltWestTek import PrimaryWestTek
from TimedRunWestTek import TimedRunWestTek
from AltWestTek import Alt

# Custom LineEdit for capturing key/mouse presses
class KeyCaptureLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.capturing = False
        self.setReadOnly(True)
        self.setText("Click to set...")
        self.setCursor(Qt.PointingHandCursor)
    
    def mousePressEvent(self, event):
        if not self.capturing:
            self.startCapture()
        else:
            # Handle mouse press as input
            button_map = {
                Qt.LeftButton: "left mouse",
                Qt.RightButton: "right mouse",
                Qt.MiddleButton: "middle mouse"
            }
            if event.button() in button_map:
                self.setText(button_map[event.button()])
                self.stopCapture()
        
        # Call the parent's implementation
        super().mousePressEvent(event)
    
    def keyPressEvent(self, event):
        if self.capturing:
            key_text = event.text()
            key_code = event.key()
            
            # Map special keys
            special_keys = {
                Qt.Key_F1: "f1",
                Qt.Key_F2: "f2",
                Qt.Key_F3: "f3",
                Qt.Key_F4: "f4",
                Qt.Key_F5: "f5",
                Qt.Key_F6: "f6",
                Qt.Key_F7: "f7",
                Qt.Key_F8: "f8",
                Qt.Key_F9: "f9",
                Qt.Key_F10: "f10",
                Qt.Key_F11: "f11",
                Qt.Key_F12: "f12",
                Qt.Key_Escape: "esc",
                Qt.Key_Tab: "tab",
                Qt.Key_CapsLock: "caps lock",
                Qt.Key_Shift: "shift",
                Qt.Key_Control: "ctrl",
                Qt.Key_Alt: "alt",
                Qt.Key_Space: "space",
                Qt.Key_Return: "enter",
                Qt.Key_Backspace: "backspace",
                Qt.Key_Delete: "delete",
                Qt.Key_Insert: "insert",
                Qt.Key_Home: "home",
                Qt.Key_End: "end",
                Qt.Key_PageUp: "page up",
                Qt.Key_PageDown: "page down",
                Qt.Key_Up: "up",
                Qt.Key_Down: "down",
                Qt.Key_Left: "left",
                Qt.Key_Right: "right",
                Qt.Key_NumLock: "num lock",
                Qt.Key_Asterisk: "numpad*",
                Qt.Key_Plus: "numpad+",
                Qt.Key_Minus: "numpad-",
                Qt.Key_Slash: "numpad/",
                Qt.Key_Period: ".",
                Qt.Key_0: "0",
                Qt.Key_1: "1",
                Qt.Key_2: "2",
                Qt.Key_3: "3",
                Qt.Key_4: "4",
                Qt.Key_5: "5",
                Qt.Key_6: "6",
                Qt.Key_7: "7",
                Qt.Key_8: "8",
                Qt.Key_9: "9"
            }
            
            # Check for numpad keys
            if key_code in range(Qt.Key_0, Qt.Key_9 + 1) and (event.modifiers() & Qt.KeypadModifier):
                self.setText(f"numpad{key_text}")
            elif key_code in special_keys:
                self.setText(special_keys[key_code])
            elif key_text:
                self.setText(key_text.lower())
            
            self.stopCapture()
        else:
            super().keyPressEvent(event)
    
    def startCapture(self):
        self.capturing = True
        self.setText("Press any key or click mouse...")
        self.setStyleSheet("background-color: #ffeeee;")
    
    def stopCapture(self):
        self.capturing = False
        self.setStyleSheet("")
        self.setCursor(Qt.PointingHandCursor)


class MasterControllerGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize configuration storage
        self.config_folder = os.path.join(os.path.expanduser("~"), "Documents", "WestTekAuto")
        self.primary_config_file = os.path.join(self.config_folder, "primary_config.json")
        self.timed_run_config_file = os.path.join(self.config_folder, "timed_run_config.json")
        self.alt_config_file = os.path.join(self.config_folder, "alt_config.json")
        
        # Create default configurations
        self.primary_config = self.get_default_primary_config()
        self.timed_run_config = self.get_default_timed_run_config()
        self.alt_config = self.get_default_alt_config()
        
        # Ensure config folder exists and load configs
        self.ensure_config_folder()
        self.load_configs()
        
        # Initialize script instances (will be created when needed)
        self.primary_westek = None
        self.timed_run_westek = None
        self.alt_westek = None
        
        # Keep track of running script
        self.current_script = None
        self.script_thread = None
        
        # Setup UI
        self.init_ui()
        
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("WestTek Automation Controller")
        self.setMinimumSize(800, 600)
        
        self.setWindowIcon(QIcon('icon.ico'))
        
        # Create main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Title
        title_label = QLabel("WestTek Automation Controller")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel("Select a script to run:")
        desc_label.setFont(QFont("Arial", 10))
        main_layout.addWidget(desc_label)
        
        # Script list
        self.script_list = QListWidget()
        self.script_list.addItem("PrimaryAltWestTek (For Main Character with AFK Player)")
        self.script_list.addItem("AltWestTek (For AFK Players)")        
        self.script_list.addItem("TimedRun (For Single Player)")
        self.script_list.setFont(QFont("Arial", 12))
        main_layout.addWidget(self.script_list)
        
        # Script description
        self.script_desc = QLabel("")
        self.script_desc.setWordWrap(True)
        self.script_desc.setFont(QFont("Arial", 10))
        self.script_desc.setMinimumHeight(80)
        main_layout.addWidget(self.script_desc)
        
        # Connect script list selection to update description
        self.script_list.currentRowChanged.connect(self.update_script_description)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Start button
        self.start_button = QPushButton("Start Selected Script")
        self.start_button.setFont(QFont("Arial", 12, QFont.Bold))
        self.start_button.clicked.connect(self.start_selected_script)
        button_layout.addWidget(self.start_button)
        
        # Stop button
        self.stop_button = QPushButton("Stop Running Script")
        self.stop_button.setFont(QFont("Arial", 12))
        self.stop_button.clicked.connect(self.stop_running_script)
        self.stop_button.setEnabled(False)
        button_layout.addWidget(self.stop_button)
        
        # Settings button
        self.settings_button = QPushButton("Settings")
        self.settings_button.setFont(QFont("Arial", 12))
        self.settings_button.clicked.connect(self.open_settings)
        button_layout.addWidget(self.settings_button)
        
        main_layout.addLayout(button_layout)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setFont(QFont("Arial", 10, QFont.Bold))
        main_layout.addWidget(self.status_label)
        
        # Select the first script by default
        self.script_list.setCurrentRow(0)
        self.update_script_description(0)
        
        # Show the window
        self.show()
    
    def update_script_description(self, index):
        """Update the script description based on selection"""
        descriptions = [
            "PrimaryAltWestTek is for your main character with AFK players. It handles shooting, OPK toggling, and elevator usage.",
            "AltWestTek is designed for AFK players. It performs automated movement patterns and key presses to keep your character active.",
            "TimedRun is optimized for single player mode. It focuses on efficient shooting and movement without waiting for other players."
        ]
        
        if 0 <= index < len(descriptions):
            self.script_desc.setText(descriptions[index])
    
    def ensure_config_folder(self):
        """Create config folder if it doesn't exist"""
        if not os.path.exists(self.config_folder):
            os.makedirs(self.config_folder)
            self.save_configs()  # Save default configs
    
    def load_configs(self):
        """Load configurations from files"""
        try:
            if os.path.exists(self.primary_config_file):
                with open(self.primary_config_file, 'r') as f:
                    loaded_config = json.load(f)
                    # Update only existing keys to handle new config options in future versions
                    for key in loaded_config:
                        if key in self.primary_config:
                            self.primary_config[key] = loaded_config[key]
            
            if os.path.exists(self.timed_run_config_file):
                with open(self.timed_run_config_file, 'r') as f:
                    loaded_config = json.load(f)
                    for key in loaded_config:
                        if key in self.timed_run_config:
                            self.timed_run_config[key] = loaded_config[key]
            
            if os.path.exists(self.alt_config_file):
                with open(self.alt_config_file, 'r') as f:
                    loaded_config = json.load(f)
                    for key in loaded_config:
                        if key in self.alt_config:
                            self.alt_config[key] = loaded_config[key]
        except Exception as e:
            QMessageBox.warning(self, "Configuration Error", 
                              f"Error loading configurations: {str(e)}\nDefault configurations will be used.")
            # Reset to defaults if there's an error
            self.primary_config = self.get_default_primary_config()
            self.timed_run_config = self.get_default_timed_run_config()
            self.alt_config = self.get_default_alt_config()
            self.save_configs()
    
    def save_configs(self):
        """Save configurations to files"""
        try:
            with open(self.primary_config_file, 'w') as f:
                json.dump(self.primary_config, f, indent=2)
            
            with open(self.timed_run_config_file, 'w') as f:
                json.dump(self.timed_run_config, f, indent=2)
            
            with open(self.alt_config_file, 'w') as f:
                json.dump(self.alt_config, f, indent=2)
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Could not save configurations: {str(e)}")
    
    def get_default_primary_config(self):
        """Get default configuration for PrimaryAltWestTek"""
        return {
            # Random timing values
            "shot_min_time": 63,
            "shot_max_time": 88,
            "quick_min_time": 50,
            "quick_max_time": 150,
            "shot_wait_min": 100,
            "shot_wait_max": 105,
            "slow_min_time": 1000,
            "slow_max_time": 1500,
            "load_screen_min": 10000,
            "load_screen_max": 12000,
            "elevator_reset_min": 8000,
            "elevator_reset_max": 12000,
            
            # Shooting config
            "shots": 60,
            "wait_time": 60000,  # 60 seconds in milliseconds
            
            # Keys
            "shoot_key": "left mouse",
            "right_key": "d",
            "sprint_key": "left shift",
            "crouch_key": "left ctrl",
            "use_key": "e",
            "opk_enable1": "numpad1",
            "opk_enable2": "numpad2",
            
            # Hotkeys
            "pause_hotkey": "f1",
            "exit_hotkey": "f2",
            "start_hotkey": "f3",
            "reload_hotkey": "f4",
            
            # Process
            "game_process": "Fallout76.exe"
        }
    
    def get_default_timed_run_config(self):
        """Get default configuration for TimedRunWestekAFKSingleShotStealth"""
        return {
            # Random timing values
            "shot_min_time": 63,
            "shot_max_time": 88,
            "quick_min_time": 50,
            "quick_max_time": 150,
            "shot_wait_min": 100,
            "shot_wait_max": 105,
            "slow_min_time": 1000,
            "slow_max_time": 1500,
            "load_screen_min": 10000,
            "load_screen_max": 12000,
            "elevator_reset_min": 8000,
            "elevator_reset_max": 12000,
            
            # Shooting config
            "shots": 60,
            "wait_time": 60000,  # 60 seconds in milliseconds
            
            # Keys
            "shoot_key": "left mouse",
            "right_key": "d",
            "sprint_key": "left shift",
            "crouch_key": "left ctrl",
            "use_key": "e",
            "opk_enable1": "numpad1",
            "opk_enable2": "numpad2",
            
            # Hotkeys
            "pause_hotkey": "f1",
            "exit_hotkey": "f2",
            "start_hotkey": "f3",
            "reload_hotkey": "f4",
            
            # Process
            "game_process": "Fallout76.exe"
        }
    
    def get_default_alt_config(self):
        """Get default configuration for AltWestTek"""
        return {
            "walk_min_time": 63,
            "walk_max_time": 88,
            "sleep_min_time": 80,
            "sleep_max_time": 100,
            "walk_cycles": 8,
            "wait_time": 60000,  # 60 seconds in milliseconds
            "action_key": "e",
            "action_press_time": 60,  # in milliseconds
            "action_cycles": 15,
            "backward_key": "s",
            "right_key": "d",
            "start_hotkey": "f3",
            "stop_hotkey": "f2",
            "game_process": "Fallout76.exe"
        }
    
    def start_selected_script(self):
        """Start the selected script"""
        # Don't allow starting if a script is already running
        if self.current_script is not None:
            QMessageBox.warning(self, "Script Running", "A script is already running. Stop it first.")
            return
        
        selected_row = self.script_list.currentRow()
        
        if selected_row == 0:  # PrimaryAltWestTek
            self.primary_westek = PrimaryWestTek(self.primary_config)
            self.current_script = "primary"
            self.status_label.setText("Running: PrimaryAltWestTek")
            
            # Start in a separate thread
            self.script_thread = threading.Thread(target=self.primary_westek.run)
            self.script_thread.daemon = True
            self.script_thread.start()
        
        elif selected_row == 1:  # AltWestTek
            self.alt_westek = Alt(self.alt_config)
            self.current_script = "alt"
            self.status_label.setText("Running: AltWestTek")
            
            # Start in a separate thread
            self.script_thread = threading.Thread(target=self.alt_westek.run)
            self.script_thread.daemon = True
            self.script_thread.start()
                
        elif selected_row == 2:  # TimedRun
            self.timed_run_westek = TimedRunWestTek(self.timed_run_config)
            self.current_script = "timed_run"
            self.status_label.setText("Running: TimedRun")
            
            # Start in a separate thread
            self.script_thread = threading.Thread(target=self.timed_run_westek.run)
            self.script_thread.daemon = True
            self.script_thread.start()
        
        # Update button states
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.settings_button.setEnabled(False)
        self.script_list.setEnabled(False)
        
        # Start monitoring thread
        self.monitor_thread = threading.Thread(target=self.monitor_script)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def stop_running_script(self):
        """Stop the currently running script"""
        if self.current_script == "alt" and self.alt_westek:
            self.alt_westek.running = False
            self.alt_westek.unregister_hotkeys()
        elif self.current_script == "primary" and self.primary_westek:
            self.primary_westek.running = False
            self.primary_westek.unregister_hotkeys()
        elif self.current_script == "timed_run" and self.timed_run_westek:
            self.timed_run_westek.running = False
            self.timed_run_westek.unregister_hotkeys()
        
        self.status_label.setText("Stopped")
        self.current_script = None
        
        # Update button states
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.settings_button.setEnabled(True)
        self.script_list.setEnabled(True)
    
    def monitor_script(self):
        """Monitor the running script thread"""
        while self.current_script is not None:
            if not self.script_thread.is_alive():
                # Script has stopped
                self.current_script = None
                # Update UI from the main thread
                QApplication.instance().processEvents()
                self.status_label.setText("Script finished")
                self.start_button.setEnabled(True)
                self.stop_button.setEnabled(False)
                self.settings_button.setEnabled(True)
                self.script_list.setEnabled(True)
                break
            time.sleep(1)
    
    def open_settings(self):
        """Open the settings dialog"""
        self.settings_dialog = SettingsDialog(self, self.primary_config, self.timed_run_config, self.alt_config)
        result = self.settings_dialog.exec_()
        
        if result:
            # Save updated configurations
            self.primary_config = self.settings_dialog.primary_config
            self.timed_run_config = self.settings_dialog.timed_run_config
            self.alt_config = self.settings_dialog.alt_config
            self.save_configs()
    
    def closeEvent(self, event):
        """Handle the window close event"""
        # Stop any running script
        if self.current_script is not None:
            self.stop_running_script()
        
        # Accept the close event
        event.accept()


class SettingsDialog(QDialog):
    def __init__(self, parent, primary_config, timed_run_config, alt_config):
        super().__init__(parent)
        
        # Store configurations
        self.primary_config = primary_config.copy()
        self.timed_run_config = timed_run_config.copy()
        self.alt_config = alt_config.copy()
        
        # Default configurations for resetting
        self.default_primary_config = parent.get_default_primary_config()
        self.default_timed_run_config = parent.get_default_timed_run_config()
        self.default_alt_config = parent.get_default_alt_config()
        
        # Initialize UI
        self.init_ui()
    
    def init_ui(self):
        """Initialize the settings dialog UI"""
        self.setWindowTitle("WestTek Automation Settings")
        self.setMinimumSize(800, 600)
        
        # Create central widget and layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Create tabs for each script
        self.create_primary_tab()
        self.create_timed_run_tab()
        self.create_alt_tab()
        
        main_layout.addWidget(self.tab_widget)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Save button
        save_button = QPushButton("Save")
        save_button.setFont(QFont("Arial", 12, QFont.Bold))
        save_button.clicked.connect(self.accept)
        button_layout.addWidget(save_button)
        
        # Cancel button
        cancel_button = QPushButton("Cancel")
        cancel_button.setFont(QFont("Arial", 12))
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        main_layout.addLayout(button_layout)
    
    def create_primary_tab(self):
        """Create the PrimaryAltWestTek settings tab"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        
        # Dictionary of field descriptions (tooltips)
        tooltips = {
            "shot_min_time": "Minimum time to hold down the shoot button (in milliseconds)",
            "shot_max_time": "Maximum time to hold down the shoot button (in milliseconds)",
            "quick_min_time": "Minimum time for quick actions (in milliseconds)",
            "quick_max_time": "Maximum time for quick actions (in milliseconds)",
            "shot_wait_min": "Minimum wait time between shots (in milliseconds)",
            "shot_wait_max": "Maximum wait time between shots (in milliseconds)",
            "slow_min_time": "Minimum time for slow actions (in milliseconds)",
            "slow_max_time": "Maximum time for slow actions (in milliseconds)",
            "load_screen_min": "Minimum wait time for load screens (in milliseconds)",
            "load_screen_max": "Maximum wait time for load screens (in milliseconds)",
            "elevator_reset_min": "Not used (in milliseconds)",
            "elevator_reset_max": "Not used (in milliseconds)",
            "shots": "Number of shots to fire in sequence",
            "wait_time": "Has to be above 1 minute for respawn to happen  (in milliseconds)",
            "shoot_key": "Key to use for shooting",
            "right_key": "Key to use for right movement",
            "sprint_key": "Key to use for sprinting",
            "crouch_key": "Key to use for crouching",
            "use_key": "Key to use for interactions",
            "opk_enable1": "First key for OPK sequence",
            "opk_enable2": "Second key for OPK sequence",
            "pause_hotkey": "Hotkey to pause the script",
            "exit_hotkey": "Hotkey to exit the script",
            "start_hotkey": "Hotkey to start the script",
            "reload_hotkey": "Hotkey to reload the script",
            "game_process": "Process name to monitor for the game"
        }
        
        # Create fields for settings
        self.primary_fields = {}
        
        # Helper method to create field with reset button
        def create_field_with_reset(key, label_text, is_key_field=False):
            field_layout = QHBoxLayout()
            
            # Create line edit or key capture edit based on the field type
            if is_key_field:
                line_edit = KeyCaptureLineEdit()
                line_edit.setText(str(self.primary_config[key]))
            else:
                line_edit = QLineEdit(str(self.primary_config[key]))
                
            line_edit.setToolTip(tooltips.get(key, ""))
            field_layout.addWidget(line_edit)
            
            # Create reset button
            reset_button = QPushButton("↺")
            reset_button.setToolTip(f"Set {key} to default")
            reset_button.setMaximumWidth(30)
            reset_button.clicked.connect(lambda: self.reset_field(line_edit, key, "primary"))
            field_layout.addWidget(reset_button)
            
            # Store field reference
            self.primary_fields[key] = line_edit
            
            return label_text, field_layout
        
        # Timing settings
        timing_group = QGroupBox("Timing Settings")
        timing_layout = QFormLayout()
        
        # Create timing fields
        label, layout_widget = create_field_with_reset("shot_min_time", "Shot Min Time:")
        timing_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("shot_max_time", "Shot Max Time:")
        timing_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("quick_min_time", "Quick Min Time:")
        timing_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("quick_max_time", "Quick Max Time:")
        timing_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("shot_wait_min", "Shot Wait Min:")
        timing_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("shot_wait_max", "Shot Wait Max:")
        timing_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("slow_min_time", "Slow Min Time:")
        timing_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("slow_max_time", "Slow Max Time:")
        timing_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("load_screen_min", "Load Screen Min:")
        timing_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("load_screen_max", "Load Screen Max:")
        timing_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("elevator_reset_min", "Elevator Reset Min:")
        timing_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("elevator_reset_max", "Elevator Reset Max:")
        timing_layout.addRow(label, layout_widget)
        
        timing_group.setLayout(timing_layout)
        layout.addWidget(timing_group)
        
        # Config settings
        config_group = QGroupBox("Config Settings")
        config_layout = QFormLayout()
        
        # Create config fields
        label, layout_widget = create_field_with_reset("shots", "Number of Shots:")
        config_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("wait_time", "Wait Time (ms):")
        config_layout.addRow(label, layout_widget)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Key settings
        key_group = QGroupBox("Key Settings")
        key_layout = QFormLayout()
        
        # Create key fields with key capture
        label, layout_widget = create_field_with_reset("shoot_key", "Shoot Key:", True)
        key_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("right_key", "Right Movement Key:", True)
        key_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("sprint_key", "Sprint Key:", True)
        key_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("crouch_key", "Crouch Key:", True)
        key_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("use_key", "Use/Interact Key:", True)
        key_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("opk_enable1", "OPK Enable Key 1:", True)
        key_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("opk_enable2", "OPK Enable Key 2:", True)
        key_layout.addRow(label, layout_widget)
        
        key_group.setLayout(key_layout)
        layout.addWidget(key_group)
        
        # Hotkey settings
        hotkey_group = QGroupBox("Hotkey Settings")
        hotkey_layout = QFormLayout()
        
        # Create hotkey fields with key capture
        label, layout_widget = create_field_with_reset("pause_hotkey", "Pause Hotkey:", True)
        hotkey_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("exit_hotkey", "Exit Hotkey:", True)
        hotkey_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("start_hotkey", "Start Hotkey:", True)
        hotkey_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("reload_hotkey", "Reload Hotkey:", True)
        hotkey_layout.addRow(label, layout_widget)
        
        hotkey_group.setLayout(hotkey_layout)
        layout.addWidget(hotkey_group)
        
        # Process settings
        process_group = QGroupBox("Process Settings")
        process_layout = QFormLayout()
        
        # Create process fields
        label, layout_widget = create_field_with_reset("game_process", "Game Process Name:")
        process_layout.addRow(label, layout_widget)
        
        process_group.setLayout(process_layout)
        layout.addWidget(process_group)
        
        scroll_area.setWidget(container)
        self.tab_widget.addTab(scroll_area, "PrimaryAltWestTek")
    
    def create_timed_run_tab(self):
        """Create the TimedRunWestekAFKSingleShotStealth settings tab"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        
        # Dictionary of field descriptions (tooltips)
        tooltips = {
            "shot_min_time": "Minimum time to hold down the shoot button (in milliseconds)",
            "shot_max_time": "Maximum time to hold down the shoot button (in milliseconds)",
            "quick_min_time": "Minimum time for quick actions (in milliseconds)",
            "quick_max_time": "Maximum time for quick actions (in milliseconds)",
            "shot_wait_min": "Minimum wait time between shots (in milliseconds)",
            "shot_wait_max": "Maximum wait time between shots (in milliseconds)",
            "slow_min_time": "Minimum time for slow actions (in milliseconds)",
            "slow_max_time": "Maximum time for slow actions (in milliseconds)",
            "load_screen_min": "Minimum wait time for load screens (in milliseconds)",
            "load_screen_max": "Maximum wait time for load screens (in milliseconds)",
            "elevator_reset_min": "Not used (in milliseconds)",
            "elevator_reset_max": "Not used (in milliseconds)",
            "shots": "Number of shots to fire in sequence",
            "wait_time": "Has to be above 1 minute for respawn to happen (in milliseconds)",
            "shoot_key": "Key to use for shooting",
            "right_key": "Key to use for right movement",
            "sprint_key": "Key to use for sprinting",
            "crouch_key": "Key to use for crouching",
            "use_key": "Key to use for interactions",
            "opk_enable1": "First key for OPK sequence",
            "opk_enable2": "Second key for OPK sequence",
            "pause_hotkey": "Hotkey to pause the script",
            "exit_hotkey": "Hotkey to exit the script",
            "start_hotkey": "Hotkey to start the script",
            "reload_hotkey": "Hotkey to reload the script",
            "game_process": "Process name to monitor for the game"
        }
        
        # Create fields for settings
        self.timed_run_fields = {}
        
        # Helper method to create field with reset button
        def create_field_with_reset(key, label_text, is_key_field=False):
            field_layout = QHBoxLayout()
            
            # Create line edit or key capture edit based on the field type
            if is_key_field:
                line_edit = KeyCaptureLineEdit()
                line_edit.setText(str(self.timed_run_config[key]))
            else:
                line_edit = QLineEdit(str(self.timed_run_config[key]))
                
            line_edit.setToolTip(tooltips.get(key, ""))
            field_layout.addWidget(line_edit)
            
            # Create reset button
            reset_button = QPushButton("↺")
            reset_button.setToolTip(f"Set {key} to default")
            reset_button.setMaximumWidth(30)
            reset_button.clicked.connect(lambda: self.reset_field(line_edit, key, "timed_run"))
            field_layout.addWidget(reset_button)
            
            # Store field reference
            self.timed_run_fields[key] = line_edit
            
            return label_text, field_layout
        
        # Timing settings
        timing_group = QGroupBox("Timing Settings")
        timing_layout = QFormLayout()
        
        # Create timing fields
        label, layout_widget = create_field_with_reset("shot_min_time", "Shot Min Time:")
        timing_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("shot_max_time", "Shot Max Time:")
        timing_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("quick_min_time", "Quick Min Time:")
        timing_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("quick_max_time", "Quick Max Time:")
        timing_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("shot_wait_min", "Shot Wait Min:")
        timing_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("shot_wait_max", "Shot Wait Max:")
        timing_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("slow_min_time", "Slow Min Time:")
        timing_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("slow_max_time", "Slow Max Time:")
        timing_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("load_screen_min", "Load Screen Min:")
        timing_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("load_screen_max", "Load Screen Max:")
        timing_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("elevator_reset_min", "Elevator Reset Min:")
        timing_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("elevator_reset_max", "Elevator Reset Max:")
        timing_layout.addRow(label, layout_widget)
        
        timing_group.setLayout(timing_layout)
        layout.addWidget(timing_group)
        
        # Config settings
        config_group = QGroupBox("Config Settings")
        config_layout = QFormLayout()
        
        # Create config fields
        label, layout_widget = create_field_with_reset("shots", "Number of Shots:")
        config_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("wait_time", "Wait Time (ms):")
        config_layout.addRow(label, layout_widget)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Key settings
        key_group = QGroupBox("Key Settings")
        key_layout = QFormLayout()
        
        # Create key fields with key capture
        label, layout_widget = create_field_with_reset("shoot_key", "Shoot Key:", True)
        key_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("right_key", "Right Movement Key:", True)
        key_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("sprint_key", "Sprint Key:", True)
        key_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("crouch_key", "Crouch Key:", True)
        key_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("use_key", "Use/Interact Key:", True)
        key_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("opk_enable1", "OPK Enable Key 1:", True)
        key_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("opk_enable2", "OPK Enable Key 2:", True)
        key_layout.addRow(label, layout_widget)
        
        key_group.setLayout(key_layout)
        layout.addWidget(key_group)
        
        # Hotkey settings
        hotkey_group = QGroupBox("Hotkey Settings")
        hotkey_layout = QFormLayout()
        
        # Create hotkey fields with key capture
        label, layout_widget = create_field_with_reset("pause_hotkey", "Pause Hotkey:", True)
        hotkey_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("exit_hotkey", "Exit Hotkey:", True)
        hotkey_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("start_hotkey", "Start Hotkey:", True)
        hotkey_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("reload_hotkey", "Reload Hotkey:", True)
        hotkey_layout.addRow(label, layout_widget)
        
        hotkey_group.setLayout(hotkey_layout)
        layout.addWidget(hotkey_group)
        
        # Process settings
        process_group = QGroupBox("Process Settings")
        process_layout = QFormLayout()
        
        # Create process fields
        label, layout_widget = create_field_with_reset("game_process", "Game Process Name:")
        process_layout.addRow(label, layout_widget)
        
        process_group.setLayout(process_layout)
        layout.addWidget(process_group)
        
        scroll_area.setWidget(container)
        self.tab_widget.addTab(scroll_area, "TimedRun")
    
    def create_alt_tab(self):
        """Create the AltWestTek settings tab"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        
        container = QWidget()
        layout = QVBoxLayout(container)
        
        # Dictionary of field descriptions (tooltips)
        tooltips = {
            "walk_min_time": "Minimum walking time in milliseconds",
            "walk_max_time": "Maximum walking time in milliseconds",
            "sleep_min_time": "Minimum sleep time in milliseconds",
            "sleep_max_time": "Maximum sleep time in milliseconds",
            "walk_cycles": "Number of walking cycles to perform",
            "wait_time": "Has to be above 1 minute for respawn to happen (in milliseconds)",
            "action_key": "Key to press for interactions",
            "action_press_time": "Time to hold the action key (in milliseconds)",
            "action_cycles": "Number of times to press the action key",
            "backward_key": "Key to use for backward movement",
            "right_key": "Key to use for right movement",
            "start_hotkey": "Hotkey to start the script",
            "stop_hotkey": "Hotkey to stop the script",
            "game_process": "Process name to monitor for the game"
        }
        
        # Create fields for settings
        self.alt_fields = {}
        
        # Helper method to create field with reset button
        def create_field_with_reset(key, label_text, is_key_field=False):
            field_layout = QHBoxLayout()
            
            # Create line edit or key capture edit based on the field type
            if is_key_field:
                line_edit = KeyCaptureLineEdit()
                line_edit.setText(str(self.alt_config[key]))
            else:
                line_edit = QLineEdit(str(self.alt_config[key]))
                
            line_edit.setToolTip(tooltips.get(key, ""))
            field_layout.addWidget(line_edit)
            
            # Create reset button
            reset_button = QPushButton("↺")
            reset_button.setToolTip(f"Set {key} to default")
            reset_button.setMaximumWidth(30)
            reset_button.clicked.connect(lambda: self.reset_field(line_edit, key, "alt"))
            field_layout.addWidget(reset_button)
            
            # Store field reference
            self.alt_fields[key] = line_edit
            
            return label_text, field_layout
        
        # Movement settings
        movement_group = QGroupBox("Movement Settings")
        movement_layout = QFormLayout()
        
        # Create movement fields
        label, layout_widget = create_field_with_reset("walk_min_time", "Walk Min Time:")
        movement_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("walk_max_time", "Walk Max Time:")
        movement_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("sleep_min_time", "Sleep Min Time:")
        movement_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("sleep_max_time", "Sleep Max Time:")
        movement_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("walk_cycles", "Walk Cycles:")
        movement_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("wait_time", "Wait Time (ms):")
        movement_layout.addRow(label, layout_widget)
        
        movement_group.setLayout(movement_layout)
        layout.addWidget(movement_group)
        
        # Action settings
        action_group = QGroupBox("Action Settings")
        action_layout = QFormLayout()
        
        # Create action fields
        label, layout_widget = create_field_with_reset("action_key", "Action Key:", True)
        action_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("action_press_time", "Action Press Time (ms):")
        action_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("action_cycles", "Action Cycles:")
        action_layout.addRow(label, layout_widget)
        
        action_group.setLayout(action_layout)
        layout.addWidget(action_group)
        
        # Key settings
        key_group = QGroupBox("Key Settings")
        key_layout = QFormLayout()
        
        # Create key fields
        label, layout_widget = create_field_with_reset("backward_key", "Backward Movement Key:", True)
        key_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("right_key", "Right Movement Key:", True)
        key_layout.addRow(label, layout_widget)
        
        key_group.setLayout(key_layout)
        layout.addWidget(key_group)
        
        # Hotkey settings
        hotkey_group = QGroupBox("Hotkey Settings")
        hotkey_layout = QFormLayout()
        
        # Create hotkey fields
        label, layout_widget = create_field_with_reset("start_hotkey", "Start Hotkey:", True)
        hotkey_layout.addRow(label, layout_widget)
        
        label, layout_widget = create_field_with_reset("stop_hotkey", "Stop Hotkey:", True)
        hotkey_layout.addRow(label, layout_widget)
        
        hotkey_group.setLayout(hotkey_layout)
        layout.addWidget(hotkey_group)
        
        # Process settings
        process_group = QGroupBox("Process Settings")
        process_layout = QFormLayout()
        
        # Create process fields
        label, layout_widget = create_field_with_reset("game_process", "Game Process Name:")
        process_layout.addRow(label, layout_widget)
        
        process_group.setLayout(process_layout)
        layout.addWidget(process_group)
        
        scroll_area.setWidget(container)
        self.tab_widget.addTab(scroll_area, "AltWestTek")
    
    def reset_field(self, field, key, config_type):
        """Reset a field to its default value"""
        if config_type == "primary":
            default_value = self.default_primary_config[key]
        elif config_type == "timed_run":
            default_value = self.default_timed_run_config[key]
        elif config_type == "alt":
            default_value = self.default_alt_config[key]
        else:
            return
        
        # Set the field value
        field.setText(str(default_value))
    
    def accept(self):
        """Save settings and close dialog"""
        # Update primary config from fields
        for key, field in self.primary_fields.items():
            value = field.text()
            # Convert numeric values to appropriate types
            if key in ["shot_min_time", "shot_max_time", "quick_min_time", "quick_max_time", 
                     "shot_wait_min", "shot_wait_max", "slow_min_time", "slow_max_time",
                     "load_screen_min", "load_screen_max", "elevator_reset_min", "elevator_reset_max",
                     "shots", "wait_time"]:
                try:
                    self.primary_config[key] = int(value)
                except ValueError:
                    QMessageBox.warning(self, "Invalid Value", 
                                     f"Invalid numeric value for {key}. Using default: {self.primary_config[key]}")
            else:
                self.primary_config[key] = value
        
        # Update timed run config from fields
        for key, field in self.timed_run_fields.items():
            value = field.text()
            # Convert numeric values to appropriate types
            if key in ["shot_min_time", "shot_max_time", "quick_min_time", "quick_max_time", 
                     "shot_wait_min", "shot_wait_max", "slow_min_time", "slow_max_time",
                     "load_screen_min", "load_screen_max", "elevator_reset_min", "elevator_reset_max",
                     "shots", "wait_time"]:
                try:
                    self.timed_run_config[key] = int(value)
                except ValueError:
                    QMessageBox.warning(self, "Invalid Value", 
                                     f"Invalid numeric value for {key}. Using default: {self.timed_run_config[key]}")
            else:
                self.timed_run_config[key] = value
        
        # Update alt config from fields
        for key, field in self.alt_fields.items():
            value = field.text()
            # Convert numeric values to appropriate types
            if key in ["walk_min_time", "walk_max_time", "sleep_min_time", "sleep_max_time",
                     "walk_cycles", "wait_time", "action_press_time", "action_cycles"]:
                try:
                    self.alt_config[key] = int(value)
                except ValueError:
                    QMessageBox.warning(self, "Invalid Value", 
                                     f"Invalid numeric value for {key}. Using default: {self.alt_config[key]}")
            else:
                self.alt_config[key] = value
        
        # Accept the dialog
        super().accept()


# Run the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("WestTek Automation")
    app.setWindowIcon(QIcon('icon.ico'))
    gui = MasterControllerGUI()
    sys.exit(app.exec_())