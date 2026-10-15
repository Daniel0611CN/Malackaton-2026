import cv2
import easyocr
import re

# Initialize the OCR reader globally.
# Loading the PyTorch model once in memory ensures constant time O(1) performance during tests.
ocr_reader = easyocr.Reader(['en', 'es'], gpu=False)

def read_financial_zone(screenshot_path: str, crop_zone: tuple) -> float:
    """
    Crops a specific area of the screen using matrix slicing and extracts the numeric value.
    
    Args:
        screenshot_path (str): File path to the full screenshot.
        crop_zone (tuple): A tuple containing (y_start, y_end, x_start, x_end).
        
    Returns:
        float: The numeric value extracted from the image, or 0.0 if reading fails.
    """
    final_value = 0.0
    
    # Load the full screenshot
    image = cv2.imread(screenshot_path)
    
    if image is not None:
        # Unpack the crop zone coordinates
        y1, y2, x1, x2 = crop_zone
        
        # Mathematical matrix slicing to isolate the target area
        cropped_image = image[y1:y2, x1:x2]
        
        # Visual processing: Convert to grayscale and apply binary threshold (pure black/white)
        grayscale_image = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2GRAY)
        _, binary_image = cv2.threshold(grayscale_image, 150, 255, cv2.THRESH_BINARY_INV)

        # Read text from the small, processed image box
        ocr_results = ocr_reader.readtext(binary_image, detail=0)
        
        if len(ocr_results) > 0:
            raw_text = ocr_results[0]
            
            # Regular expression to clean the text, keeping only digits and decimals
            clean_numbers = re.sub(r'[^\d.]', '', raw_text.replace(',', '.'))
            
            try:
                if clean_numbers:
                    final_value = float(clean_numbers)
            except ValueError:
                print(f"Warning: Could not convert extracted text '{clean_numbers}' to float.")
    else:
        print(f"Error: Screenshot not found at path '{screenshot_path}'.")
        
    return final_value