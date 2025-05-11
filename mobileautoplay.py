import pyautogui
import cv2
import numpy as np
import time
from PIL import Image
import mss
from ppadb.client import Client as AdbClient

# Configure PyAutoGUI
pyautogui.FAILSAFE = True  # Move mouse to top-left corner to stop
pyautogui.PAUSE = 0.01

# Define the region of the scrcpy window (adjust based on your setup)
monitor = {"top": 46, "left": 1436, "width": 407, "height": 938}

# Initialize ADB
adb = AdbClient(host="127.0.0.1", port=5037)
devices = adb.devices()
if not devices:
    raise Exception("No devices connected via ADB")
device = devices[0]

# Screen dimensions of the mobile device (adjust based on your device)
SCREEN_WIDTH = 720
SCREEN_HEIGHT = 1280

def simulate_swipe(start_x, start_y, end_x, end_y, duration=100):
    """Simulate a swipe on the mobile device using ADB."""
    command = f"input swipe {start_x} {start_y} {end_x} {end_y} {duration}"
    device.shell(command)

def perform_jump():
    """Simulate a swipe up to jump."""
    center_x = SCREEN_WIDTH // 2
    start_y = SCREEN_HEIGHT * 3 // 4
    end_y = start_y - 300
    simulate_swipe(center_x, start_y, center_x, end_y)
    print("Jump!")

def perform_slide():
    """Simulate a swipe down to slide."""
    center_x = SCREEN_WIDTH // 2
    start_y = SCREEN_HEIGHT * 3 // 4
    end_y = start_y + 300
    simulate_swipe(center_x, start_y, center_x, end_y)
    print("Slide!")

def move_left():
    """Simulate a swipe left to move left."""
    center_y = SCREEN_HEIGHT * 3 // 4
    start_x = SCREEN_WIDTH * 3 // 4
    end_x = start_x - 300
    simulate_swipe(start_x, center_y, end_x, center_y)
    print("Move left!")

def move_right():
    """Simulate a swipe right to move right."""
    center_y = SCREEN_HEIGHT * 3 // 4
    start_x = SCREEN_WIDTH // 4
    end_x = start_x + 300
    simulate_swipe(start_x, center_y, end_x, center_y)
    print("Move right!")

def capture_screen():
    """Capture the scrcpy window."""
    with mss.mss() as sct:
        screenshot = sct.grab(monitor)
        img = np.array(Image.frombytes("RGB", screenshot.size, screenshot.rgb))
        return cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

def detect_obstacle_or_train(image):
    """Detect obstacles or trains, ignoring coins."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    height, width = gray.shape
    
    # ROI for obstacles/trains (middle of screen, where they appear)
    roi = gray[int(height * 0.4):int(height * 0.7), int(width * 0.2):int(width * 0.8)]
    
    # Edge detection for trains/obstacles (trains are large, obstacles have sharp edges)
    edges = cv2.Canny(roi, 50, 150)
    
    # Detect significant edges (indicating trains or obstacles)
    edge_pixels = np.sum(edges == 255)
    total_pixels = edges.size
    edge_ratio = edge_pixels / total_pixels
    
    # Trains are large and dark; check for dark regions in ROI
    dark_roi = gray[int(height * 0.4):int(height * 0.7), int(width * 0.2):int(width * 0.8)]
    dark_pixels = np.sum(dark_roi < 80)  # Dark threshold
    dark_ratio = dark_pixels / dark_roi.size
    
    return edge_ratio > 0.03 or dark_ratio > 0.2  # Adjust thresholds

def detect_obstacle_lane(image):
    """Determine which lane has an obstacle or train."""
    height, width = image.shape[:2]
    section_width = width // 3
    
    # ROI for obstacle detection in each lane (middle screen)
    left_roi = image[int(height * 0.4):int(height * 0.7), 0:section_width]
    center_roi = image[int(height * 0.4):int(height * 0.7), section_width:2*section_width]
    right_roi = image[int(height * 0.4):int(height * 0.7), 2*section_width:]
    
    # Convert to grayscale and apply edge detection
    left_gray = cv2.cvtColor(left_roi, cv2.COLOR_BGR2GRAY)
    center_gray = cv2.cvtColor(center_roi, cv2.COLOR_BGR2GRAY)
    right_gray = cv2.cvtColor(right_roi, cv2.COLOR_BGR2GRAY)
    
    left_edges = cv2.Canny(left_gray, 50, 150)
    center_edges = cv2.Canny(center_gray, 50, 150)
    right_edges = cv2.Canny(right_gray, 50, 150)
    
    # Calculate edge density for each lane
    left_edge_ratio = np.sum(left_edges == 255) / left_edges.size
    center_edge_ratio = np.sum(center_edges == 255) / center_edges.size
    right_edge_ratio = np.sum(right_edges == 255) / right_edges.size
    
    # Return the lane with the highest edge density (likely has obstacle/train)
    max_ratio = max(left_edge_ratio, center_edge_ratio, right_edge_ratio)
    if max_ratio < 0.03:  # No significant obstacle
        return None
    elif max_ratio == left_edge_ratio:
        return "left"
    elif max_ratio == center_edge_ratio:
        return "center"
    else:
        return "right"

def detect_current_lane(image):
    """Determine the player's current lane."""
    height, width = image.shape[:2]
    section_width = width // 3
    bottom_roi = image[int(height * 0.8):, :]
    
    left_section = bottom_roi[:, 0:section_width]
    center_section = bottom_roi[:, section_width:2*section_width]
    right_section = bottom_roi[:, 2*section_width:]
    
    left_brightness = np.mean(cv2.cvtColor(left_section, cv2.COLOR_BGR2GRAY))
    center_brightness = np.mean(cv2.cvtColor(center_section, cv2.COLOR_BGR2GRAY))
    right_brightness = np.mean(cv2.cvtColor(right_section, cv2.COLOR_BGR2GRAY))
    
    max_brightness = max(left_brightness, center_brightness, right_brightness)
    if max_brightness == left_brightness:
        return "left"
    elif max_brightness == center_brightness:
        return "center"
    else:
        return "right"

def main():
    print("Starting script in 5 seconds... Move mouse to top-left to stop.")
    time.sleep(5)
    
    while True:
        # Capture the scrcpy window
        screen = capture_screen()
        
        # Detect obstacles or trains
        if detect_obstacle_or_train(screen):
            # Check if obstacle is above or below (simplified: jump for now)
            perform_jump()  # Could add slide logic for low obstacles
            
        # Detect which lane has an obstacle/train
        obstacle_lane = detect_obstacle_lane(screen)
        current_lane = detect_current_lane(screen)
        
        # Move only to avoid obstacles/trains
        if obstacle_lane and obstacle_lane == current_lane:
            # Obstacle in current lane; move to an adjacent lane
            if current_lane == "left":
                move_right()
            elif current_lane == "right":
                move_left()
            elif current_lane == "center":
                # Randomly choose left or right
                if np.random.rand() > 0.5:
                    move_left()
                else:
                    move_right()
        
        # Small delay to avoid overwhelming the game
        time.sleep(0.1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Script stopped by user.")