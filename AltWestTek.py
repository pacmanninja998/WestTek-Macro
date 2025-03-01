import time
import random
import keyboard
import datetime
import threading
import sys
import psutil

class Alt:
    def __init__(self, config=None):
        # Default configuration
        self.default_config = {
            "walk_min_time": 63,
            "walk_max_time": 88,
            "sleep_min_time": 80,
            "sleep_max_time": 100,
            "walk_cycles": 8,
            "wait_time": 60000,  # 60 seconds in milliseconds
            "action_key": "e",
            "action_press_time": 60,  # in milliseconds
            "action_cycles": 15,
            "backward_key": "s",  # The parameter name in your original code
            "right_key": "d",
            "start_hotkey": "f3",
            "stop_hotkey": "f2",
            "game_process": "Fallout76.exe"  # Added game process check
        }
        
        # Use provided config or default
        self.config = config if config else self.default_config
        self.running = False
        self.hotkeys_registered = False
        self.registered_hotkeys = []  # Track which hotkeys were successfully registered
    
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
    
    def start_automation(self):
        """Function that gets called when start hotkey is pressed"""
        self.running = True
        
        # Check if game is running before starting
        if not self.process_exists(self.config["game_process"]):
            print(f"{self.config['game_process']} not running. Exiting script...")
            self.running = False
            return
        
        # First loop - countdown until seconds = 01
        while self.running:
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
        
        # Second loop - continuous movement and key presses
        while self.running:
            # Check if game is running
            if not self.process_exists(self.config["game_process"]):
                print(f"{self.config['game_process']} not running. Exiting script...")
                self.stop_automation()
                return
                
            start_time = time.time()
            
            # Walking pattern
            for _ in range(self.config["walk_cycles"]):
                ran_walk = random.randint(self.config["walk_min_time"], self.config["walk_max_time"]) / 1000
                walk_sleep = random.randint(self.config["sleep_min_time"], self.config["sleep_max_time"]) / 1000
                
                # Fixed the variable name here to match the config
                keyboard.press(self.config["backward_key"])
                time.sleep(ran_walk)
                keyboard.press(self.config["right_key"])
                time.sleep(walk_sleep)
                keyboard.release(self.config["backward_key"])
                time.sleep(ran_walk)
                keyboard.release(self.config["right_key"])
                time.sleep(ran_walk)
            
            # Wait until configured time has passed
            while self.running:
                elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
                if elapsed_time >= self.config["wait_time"]:
                    break
                time.sleep(1)
            
            # Press action key multiple times
            for _ in range(self.config["action_cycles"]):
                keyboard.press(self.config["action_key"])
                time.sleep(self.config["action_press_time"] / 1000)
                keyboard.release(self.config["action_key"])
    
    def stop_automation(self):
        """Function that gets called when stop hotkey is pressed"""
        self.running = False
        
        # Make sure to release all keys
        try:
            time.sleep(0.09)  # 90ms
            keyboard.release(self.config["backward_key"])
            time.sleep(0.09)  # 90ms
            keyboard.release(self.config["right_key"])
            time.sleep(0.09)  # 90ms
            keyboard.release(self.config["action_key"])
        except Exception as e:
            print(f"Error releasing keys: {e}")

    def register_hotkeys(self):
        """Register hotkeys for starting and stopping automation"""
        if not self.hotkeys_registered:
            try:
                # Register start hotkey
                start_hotkey = keyboard.add_hotkey(
                    self.config["start_hotkey"], 
                    self.start_automation
                )
                self.registered_hotkeys.append(self.config["start_hotkey"])
                
                # Register stop hotkey
                stop_hotkey = keyboard.add_hotkey(
                    self.config["stop_hotkey"], 
                    self.stop_automation
                )
                self.registered_hotkeys.append(self.config["stop_hotkey"])
                
                self.hotkeys_registered = True
                print(f"Registered hotkeys: {self.config['start_hotkey']} and {self.config['stop_hotkey']}")
            except Exception as e:
                print(f"Error registering hotkeys: {e}")
            
    def unregister_hotkeys(self):
        """Unregister hotkeys"""
        if self.hotkeys_registered:
            try:
                # Only attempt to remove hotkeys that were successfully registered
                for hotkey in self.registered_hotkeys:
                    keyboard.remove_hotkey(hotkey)
                self.registered_hotkeys = []
                self.hotkeys_registered = False
                print("Hotkeys unregistered")
            except Exception as e:
                print(f"Error unregistering hotkeys: {e}")
    
    def run(self):
        """Main method to run the automation with hotkeys"""
        print(f"Alt WestTek Script running. Press {self.config['start_hotkey']} to start, {self.config['stop_hotkey']} to stop.")
        
        # Check if game is running before registering hotkeys
        if not self.process_exists(self.config["game_process"]):
            print(f"{self.config['game_process']} not running. Exiting script...")
            return
            
        self.register_hotkeys()
        
        try:
            # Keep the script running
            keyboard.wait(self.config["stop_hotkey"])
        except KeyboardInterrupt:
            # Handle Ctrl+C
            pass
        finally:
            self.unregister_hotkeys()
    
    def start_directly(self):
        """Start automation without waiting for hotkey"""
        self.start_automation()

    def stop_directly(self):
        """Stop automation without using hotkey"""
        self.stop_automation()


# If this script is run directly
if __name__ == "__main__":
    # Create an instance with default config
    automation = Alt()
    automation.run()