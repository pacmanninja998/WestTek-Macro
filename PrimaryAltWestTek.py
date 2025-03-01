import time
import random
import keyboard
import datetime
import sys
import subprocess
import psutil

class PrimaryWestTek:
    def __init__(self, config=None):
        # Default configuration
        self.default_config = {
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
        
        # Use provided config or default
        self.config = config if config else self.default_config
        self.running = False
        self.paused = False
        self.hotkeys_registered = False
    
    def display_tooltip(self, message=None):
        """Display a message (equivalent to ToolTip in AHK)"""
        if message:
            print(f"\rCountdown: {message}", end="")
        else:
            print("\r" + " " * 20 + "\r", end="")  # Clear the line
    
    def process_exists(self, process_name):
        """Check if a process exists by name"""
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == process_name:
                return True
        return False
    
    def pause_toggle(self):
        """Toggle pause state"""
        self.paused = not self.paused
        if self.paused:
            print("Script paused. Press F1 to resume.")
        else:
            print("Script resumed.")
    
    def exit_script(self):
        """Exit the script"""
        print("Exiting script...")
        self.running = False
        self.unregister_hotkeys()
        sys.exit()
    
    def reload_script(self):
        """Reload the script"""
        print("Reloading script...")
        self.unregister_hotkeys()
        # In Python, we'd typically restart the process
        # This is a simplified version
        python = sys.executable
        os.execl(python, python, *sys.argv)
    
    def start_automation(self):
        """Function for the main automation workflow"""
        self.running = True
        
        # First loop - countdown until seconds = 01
        while self.running and not self.paused:
            # Get current time seconds
            current_seconds = datetime.datetime.now().strftime("%S")
            
            if int(current_seconds) > 1:
                countdown = 60 - int(current_seconds)
            else:
                countdown = 1
                
            self.display_tooltip(countdown)
            
            if current_seconds == "01":
                self.display_tooltip()  # Clear tooltip
                break
            
            time.sleep(0.1)  # Small delay to prevent high CPU usage
        
        # Main automation loop
        while self.running and not self.paused:
            # Check if game is running
            if not self.process_exists(self.config["game_process"]):
                print(f"{self.config['game_process']} not running. Exiting script...")
                self.exit_script()
                return
            
            # Get start time for timing
            start_time = time.time()
            
            # Shooting loop
            for _ in range(self.config["shots"]):
                shot_time = random.randint(self.config["shot_min_time"], self.config["shot_max_time"]) / 1000
                wait_time = random.randint(self.config["shot_wait_min"], self.config["shot_wait_max"]) / 1000
                
                keyboard.press(self.config["shoot_key"])
                time.sleep(shot_time)
                keyboard.release(self.config["shoot_key"])
                time.sleep(wait_time)
            
            # Deactivate OPK
            keyboard.press(self.config["opk_enable1"])
            time.sleep(0.03)
            keyboard.release(self.config["opk_enable1"])
            time.sleep(1)
            keyboard.press(self.config["opk_enable2"])
            time.sleep(0.03)
            keyboard.release(self.config["opk_enable2"])
            time.sleep(1)
            
            # Run to the right, get in standing position
            for _ in range(4):
                keyboard.press(self.config["right_key"])
                time.sleep(0.03)
                keyboard.press(self.config["sprint_key"])
                time.sleep(0.4)
                keyboard.release(self.config["right_key"])
                time.sleep(0.03)
                keyboard.release(self.config["sprint_key"])
            
            # Crouch
            time.sleep(0.03)
            keyboard.press(self.config["crouch_key"])
            time.sleep(0.03)
            keyboard.release(self.config["crouch_key"])
            time.sleep(0.1)
            
            # Wait until configured time has passed
            while self.running and not self.paused:
                elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
                if elapsed_time >= self.config["wait_time"]:
                    break
                time.sleep(1)
            
            # Press E to use elevator
            keyboard.press(self.config["use_key"])
            time.sleep(0.06)
            keyboard.release(self.config["use_key"])
            time.sleep(1)
            
            # Check if game is still running
            if not self.process_exists(self.config["game_process"]):
                print(f"{self.config['game_process']} not running. Exiting script...")
                self.exit_script()
                return
            
            # Enable OPK
            keyboard.press(self.config["opk_enable1"])
            time.sleep(0.03)
            keyboard.release(self.config["opk_enable1"])
            time.sleep(1)
            keyboard.press(self.config["opk_enable2"])
            time.sleep(0.03)
            keyboard.release(self.config["opk_enable2"])
            time.sleep(1)
            
            # Wait for loading screen
            load_time = random.randint(self.config["load_screen_min"], self.config["load_screen_max"]) / 1000
            time.sleep(load_time)
    
    def register_hotkeys(self):
        """Register hotkeys for controlling the script"""
        if not self.hotkeys_registered:
            keyboard.add_hotkey(self.config["pause_hotkey"], self.pause_toggle)
            keyboard.add_hotkey(self.config["exit_hotkey"], self.exit_script)
            keyboard.add_hotkey(self.config["start_hotkey"], self.start_automation)
            keyboard.add_hotkey(self.config["reload_hotkey"], self.reload_script)
            self.hotkeys_registered = True
    
    def unregister_hotkeys(self):
        """Unregister hotkeys"""
        if self.hotkeys_registered:
            keyboard.remove_hotkey(self.config["pause_hotkey"])
            keyboard.remove_hotkey(self.config["exit_hotkey"])
            keyboard.remove_hotkey(self.config["start_hotkey"])
            keyboard.remove_hotkey(self.config["reload_hotkey"])
            self.hotkeys_registered = False
    
    def run(self):
        """Main method to run the automation with hotkeys"""      
        self.register_hotkeys()
        
        try:
            # Keep the script running
            keyboard.wait()
        except KeyboardInterrupt:
            # Handle Ctrl+C
            pass
        finally:
            self.unregister_hotkeys()

# If this script is run directly
if __name__ == "__main__":
    # Need to import os for reload functionality
    import os
    
    # Create and run the automation
    westek = PrimaryWestTek()
    westek.run()