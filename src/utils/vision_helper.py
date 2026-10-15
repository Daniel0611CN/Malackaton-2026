import cv2
import numpy as np

def get_spin_coordinates(screen_width: int, screen_height: int) -> tuple:
    """
    Calculates the exact position of the Spin button based on static screen proportions.
    This O(1) approach replaces heavy visual search, making the pipeline scalable.
    
    Args:
        screen_width (int): The width of the game canvas or viewport.
        screen_height (int): The height of the game canvas or viewport.
        
    Returns:
        tuple: A tuple containing (x, y) coordinates for the automated click.
    """
    # Proportions for Pragmatic Play (e.g., button at 85% width, 80% height)
    # In a scalable architecture, these ratios would be loaded from a config file
    width_ratio = 0.85
    height_ratio = 0.80
    
    # Calculate exact pixels
    x_coordinate = int(screen_width * width_ratio)
    y_coordinate = int(screen_height * height_ratio)
    
    # Single return variable
    target_coordinates = (x_coordinate, y_coordinate)
    
    return target_coordinates


def verify_spin_movement(image_path_before: str, image_path_after: str, movement_threshold: int = 50000) -> bool:
    """
    Verifies if the game reels moved by comparing matrix differences between two screenshots.
    
    Args:
        image_path_before (str): File path to the pre-spin screenshot.
        image_path_after (str): File path to the post-spin screenshot.
        movement_threshold (int): Minimum pixel difference sum to consider it a valid spin.
        
    Returns:
        bool: True if movement is detected above the threshold, False otherwise.
    """
    has_movement = False
    
    # Load images as grayscale matrices
    img_before = cv2.imread(image_path_before, cv2.IMREAD_GRAYSCALE)
    img_after = cv2.imread(image_path_after, cv2.IMREAD_GRAYSCALE)
    
    if img_before is not None and img_after is not None:
        # Matrix algebra: calculate the absolute difference between both images
        difference_matrix = cv2.absdiff(img_before, img_after)
        
        # Sum all pixel differences to calculate movement magnitude
        total_change = np.sum(difference_matrix)
        print(f"Total movement magnitude detected: {total_change}")
        
        if total_change > movement_threshold:
            has_movement = True
    else:
        print("Error: Could not load the images for movement verification.")
        
    return has_movement