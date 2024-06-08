import os
import subprocess
import re
import cv2
import json
from time import sleep
from colorama import init, Fore, Style

init(autoreset=True)


def load_config(file_path):
    with open(file_path, "r") as f:
        config = json.load(f)
    return config

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

def capture_screenshot(emulator, filename):
    """Capture a screenshot of the emulator."""
    try:
        with open(filename, "wb") as f:
            subprocess.run(f"{ADB_PATH} -s {emulator} exec-out screencap -p", shell=True, stdout=f)
        print(f"{Fore.GREEN}Screenshot saved for {emulator} as {filename}{Style.RESET_ALL}")
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}Failed to capture screenshot for {emulator}: {e}{Style.RESET_ALL}")

def save_screenshot(emulator):
    """Save a screenshot of the emulator."""
    screenshot_filename = os.path.join(SCREENSHOTS_DIR, f"{emulator.replace(':', '_')}.png")
    capture_screenshot(emulator, screenshot_filename)

def check_app_running(emulator):
    """Check if the Roblox app is running on the emulator."""
    try:
        subprocess.check_output(f"{ADB_PATH} -s {emulator} shell pidof com.roblox.client", shell=True)
        return True
    except subprocess.CalledProcessError:
        return False

def compare_images(screenshot_path, reference_image_paths, delay=2):
    screenshot = cv2.imread(screenshot_path)
    screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)

    for reference_image_path in reference_image_paths:
        reference_image = cv2.imread(reference_image_path)
        reference_gray = cv2.cvtColor(reference_image, cv2.COLOR_BGR2GRAY)

        # Use template matching
        result = cv2.matchTemplate(screenshot_gray, reference_gray, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        # Define a threshold for matching
        threshold = 0.8
        if max_val >= threshold:
            return True

        # Add a delay between comparisons
        sleep(delay)

    return False

def get_reference_image_paths():
    return ["img/Home_White_Eng.png",
             "img/Home_Dark_Eng.png",
             "img/Home_Mini_White_Eng.png",
             "img/Home_Mini_Dark_Eng.png",
             "img/Join_Error_Eng.png",
             "img/Kick.png"
            ]

if __name__ == "__main__":
    config = load_config("config.json")
    mumu_install_dir = config["mumu_install_dir"]
    vms_dir = config["vms_dir"]
    ADB_PATH = config["ADB_PATH"]
    PLACE_ID = config["PLACE_ID"]
    CHECK_DELAY = config["CHECK_DELAY"]
    SCREENSHOTS_DIR = config["SCREENSHOTS_DIR"]
    RECHECK_COUNT = config["RECHECK_COUNT"]
    check_counts = config["check_counts"]


    mumu12_control_api_backend(mumu_install_dir, vms_dir)

    while True:
        emulators = auto_connect_devices(ADB_PATH)
        if emulators:
            reference_image_paths = get_reference_image_paths()
            for emulator in emulators:
                try:
                    subprocess.check_output(f"{ADB_PATH} -s {emulator} shell pidof com.roblox.client")
                except subprocess.CalledProcessError:
                    subprocess.call(f"{ADB_PATH} -s {emulator} shell am start -a android.intent.action.VIEW -d roblox://placeId={PLACE_ID}", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True)
                    print(f"{Fore.LIGHTMAGENTA_EX}{emulator}{Style.RESET_ALL} rejoin")

                # Capture screenshot after checking if the app is running
                save_screenshot(emulator)

                # Compare screenshot with reference images
                screenshot_path = os.path.join(SCREENSHOTS_DIR, f"{emulator.replace(':', '_')}.png")
                if compare_images(screenshot_path, reference_image_paths):
                    print(f"{Fore.GREEN}Reference image matched in {emulator}, restarting the app...{Style.RESET_ALL}")
                    subprocess.call(
                        f"{ADB_PATH} -s {emulator} shell am force-stop com.roblox.client", 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL, 
                        shell=True
                    )
                    subprocess.call(
                        f"{ADB_PATH} -s {emulator} shell am start -a android.intent.action.VIEW -d roblox://placeId={PLACE_ID}", 
                        stderr=subprocess.DEVNULL, 
                        shell=True
                    )

                # Assuming you're not checking for the presence of target images anymore
                # Just print a message indicating the screenshot was captured
                print(f"{Fore.GREEN}Screenshot captured for {emulator}{Style.RESET_ALL}")

                # Reset the check count as there's no target image check anymore
                check_counts[emulator] = 0

                # Rejoin if the check count exceeds the threshold (as before)
                if check_counts[emulator] >= RECHECK_COUNT:
                    print(f"{Fore.RED}Exceeded {RECHECK_COUNT} checks without finding target images in {emulator}'s screenshot, rejoining...{Style.RESET_ALL}")
                    subprocess.call(
                        f"{ADB_PATH} -s {emulator} shell am force-stop com.roblox.client", 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL, 
                        shell=True
                    )
                    subprocess.call(
                        f"{ADB_PATH} -s {emulator} shell am start -a android.intent.action.VIEW -d roblox://placeId={PLACE_ID}", 
                        stdout=subprocess.DEVNULL, 
                        stderr=subprocess.DEVNULL, 
                        shell=True
                    )
                    # Reset the check count after rejoining
                    check_counts[emulator] = 0
        else:
            print(f"{Fore.RED}No connected devices found{Style.RESET_ALL}")
        sleep(CHECK_DELAY)
