import subprocess
import ctypes
import sys
import json
import os
import logging
from datetime import datetime
from tqdm import tqdm

# Setup logging
logging.basicConfig(filename='debloat_log.txt', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Check if the script is running as administrator
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception as e:
        logging.error(f"Admin check failed: {e}")
        return False

# Request admin privileges if not running as admin
def request_admin():
    if not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, ' '.join(sys.argv), None, 1)
        sys.exit()

# Create a system restore point
def create_restore_point():
    try:
        logging.info("Creating system restore point...")
        subprocess.run(['powershell', '-Command', 'Checkpoint-Computer -Description "Pre-Debloat Restore Point" -RestorePointType "MODIFY_SETTINGS"'], check=True)
        logging.info("System restore point created successfully.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to create restore point: {e}")

# Function to remove a single app using PowerShell
def remove_app(package_name):
    try:
        subprocess.run(['powershell', '-Command', f"Get-AppxPackage {package_name} | Remove-AppxPackage"], check=True)
        logging.info(f"Removed: {package_name}")
    except subprocess.CalledProcessError:
        logging.warning(f"Failed to remove or not installed: {package_name}")

# Function to check and install apps via winget
def ensure_installed(app_name, winget_id):
    try:
        result = subprocess.run(['winget', 'list', '--exact', '--id', winget_id], capture_output=True, text=True)
        if winget_id.lower() not in result.stdout.lower():
            choice = input(f"{app_name} is not installed. Do you want to install it? (y/n): ").lower()
            if choice == 'y':
                subprocess.run(['winget', 'install', '--id', winget_id, '-e', '--accept-source-agreements', '--accept-package-agreements'], check=True)
                logging.info(f"Installed {app_name}")
            else:
                logging.info(f"Skipped installation of {app_name}")
        else:
            logging.info(f"{app_name} is already installed.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to install {app_name}: {e}")

# Backup and load user preferences
def backup_preferences(prefs):
    with open('user_preferences.json', 'w') as f:
        json.dump(prefs, f)
    logging.info("User preferences backed up.")

def load_preferences():
    if os.path.exists('user_preferences.json'):
        with open('user_preferences.json', 'r') as f:
            return json.load(f)
    else:
        return {}

# Undo changes using restore point
def undo_changes():
    logging.info("Initiating system restore...")
    subprocess.run(['powershell', '-Command', 'rstrui.exe'])

# Main debloat function
def debloat(category):
    create_restore_point()

    prefs = load_preferences()

    apps_to_remove = prefs.get("apps_to_remove", [
        "Microsoft.549981C3F5F10", "Microsoft.BingWeather", "Microsoft.GetHelp",
        "Microsoft.MixedReality.Portal", "Microsoft.SkypeApp", "Microsoft.WindowsFeedbackHub",
        "Microsoft.XboxApp", "Microsoft.ZuneMusic", "Microsoft.ZuneVideo"
    ])

    optional_installs = {
        "Gaming & Debloated": [("Discord", "Discord.Discord"), ("Steam", "Valve.Steam")],
        "Development & Debloated": [("Visual Studio Code", "Microsoft.VisualStudioCode"), ("Git", "Git.Git")],
        "Productivity & Debloated": [("Notion", "Notion.Notion"), ("Adobe Acrobat Reader", "Adobe.Acrobat.Reader.64-bit")]
    }

    logging.info(f"Starting debloating process for {category}")

    for app in tqdm(apps_to_remove, desc="Removing apps"):
        remove_app(app)

    for app_name, winget_id in optional_installs.get(category, []):
        ensure_installed(app_name, winget_id)

    backup_preferences({"apps_to_remove": apps_to_remove})

    generate_report(category, apps_to_remove)
    logging.info("Debloating and optimizations completed successfully.")

# Generate detailed report
def generate_report(category, removed_apps):
    report_name = f"debloat_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_name, 'w') as report:
        report.write(f"Debloating Report - {category}\n")
        report.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        report.write("Removed Applications:\n")
        for app in removed_apps:
            report.write(f"- {app}\n")
    logging.info(f"Report generated: {report_name}")

# Enhanced main menu
def main_menu():
    menu_text = """
========================================
        🚀 Windows 11 Debloater 🚀
========================================

Choose a debloating profile to optimize your system:

  [1] 🎮 Gaming & Debloated
      - Discord, Steam

  [2] 💻 Development & Debloated
      - Visual Studio Code, Git

  [3] 📅 Productivity & Debloated
      - Notion, Adobe Acrobat Reader

  [4] ⚡ Minimal & Debloated
      - Essential apps only, minimal clutter

  [5] ↩️ Undo Changes (System Restore)

========================================
"""
    print(menu_text)
    choice = input("✨ Enter your choice (1-5): ")

    profiles = {
        "1": "Gaming & Debloated",
        "2": "Development & Debloated",
        "3": "Productivity & Debloated",
        "4": "Minimal & Debloated",
        "5": "Undo"
    }

    if choice in profiles:
        if choice == "5":
            undo_changes()
        else:
            debloat(profiles[choice])
    else:
        logging.warning("Invalid choice entered")
        print("\n❌ Invalid choice. Exiting...")

if __name__ == "__main__":
    request_admin()
    main_menu()
