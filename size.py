import pyautogui
import time

print("Move your mouse to the TOP-LEFT corner of the scrcpy window...")
time.sleep(5)  # Give you 5 seconds to position mouse
print("Top-left corner:", pyautogui.position())

print("Now move your mouse to the BOTTOM-RIGHT corner of the scrcpy window...")
time.sleep(5)
print("Bottom-right corner:", pyautogui.position())
