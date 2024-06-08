import subprocess
from colorama import Fore, Style

# Replace this with your target place ID
place_id = "623823800"

def rejoin_game():
    try:
        # Check if Roblox is running
        subprocess.check_output("adb shell pidof com.roblox.client", shell=True)
        print(f"{Fore.LIGHTGREEN_EX}Roblox is already running.{Style.RESET_ALL}")
    except subprocess.CalledProcessError:
        # Start Roblox and rejoin the game
        subprocess.call(f"adb shell am start -a android.intent.action.VIEW -d roblox://placeId={place_id}", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, shell=True)
        print(f"{Fore.LIGHTMAGENTA_EX}Rejoining game with place ID: {place_id}{Style.RESET_ALL}")

if __name__ == "__main__":
    rejoin_game()
