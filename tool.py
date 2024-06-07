import os
import subprocess
import re
import json
from time import sleep
from colorama import init, Fore, Style

init(autoreset=True)

# Load configuration from config.json
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

def auto_connect_devices(adb_path):
    connected_devices = []
    try:
        output = subprocess.check_output(f"{adb_path} devices").decode("utf-8")
        lines = output.strip().split('\n')[1:]  # Remove header
        for line in lines:
            if 'device' in line:
                device = line.split('\t')[0]
                connected_devices.append(device)
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
    return connected_devices

def mumu12_control_api_backend(mumu_install_dir, vms_dir):
    try:
        # Check if installation and vms directories exist
        if not os.path.isdir(mumu_install_dir):
            raise FileNotFoundError("MuMu Player installation directory not found")
        if not os.path.isdir(vms_dir):
            raise FileNotFoundError("MuMu Player vms directory not found")
        
        # Specify the path to MuMuManager.exe
        exe_path = os.path.join(mumu_install_dir, "MuMuManager.exe")
        
        # Check if MuMuManager.exe exists
        if not os.path.isfile(exe_path):
            raise FileNotFoundError("MuMuManager executable not found")
        
        # List all directories in the vms directory and extract instance numbers
        instance_numbers = []
        for entry in os.listdir(vms_dir):
            match = re.match(r'MuMuPlayerGlobal-12.0-(\d+)', entry)
            if match:
                instance_numbers.append(int(match.group(1)))
        
        if not instance_numbers:
            raise FileNotFoundError("No MuMuPlayerGlobal instances found")
        
        # Construct and execute the connect_adb command for each instance
        for instance_number in instance_numbers:
            command = f'"{exe_path}" adb -v {instance_number} connect'
            process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            
            if process.returncode == 0:
                adb_connection_info = stdout.decode().strip()
                print(f"Connected {adb_connection_info} successfully")

    except FileNotFoundError as fnf_error:
        print(fnf_error)
    except ValueError as ve:
        print(ve)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

# Example usage
if __name__ == "__main__":
    mumu12_control_api_backend(config["mumu_install_dir"], config["vms_dir"])

    while True:
        emulators = auto_connect_devices(config["ADB_PATH"])
        if emulators:
            for emulator in emulators:
                try:
                    subprocess.check_output(f"{config['ADB_PATH']} -s {emulator} shell pidof com.roblox.client")
                except subprocess.CalledProcessError:
                    subprocess.call(f"{config['ADB_PATH']} -s {emulator} shell am start -a android.intent.action.VIEW -d roblox://placeId={config['place_id']}", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True)
                    print(f"{Fore.LIGHTMAGENTA_EX}{emulator}{Style.RESET_ALL} rejoin")
        sleep(config["CHECK_DELAY"])
