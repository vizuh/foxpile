import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
import re

def apply_gamma_correction(image, gamma=1.0):
    """
    Apply gamma correction to the image, ensuring compatibility with its mode.
    Always ensure the image is in RGB mode for consistent LUT application.
    """
    image = image.convert('RGB')  # Ensure image is in RGB mode for gamma correction
    inv_gamma = 1.0 / gamma
    lut = [int((i / 255.0) ** inv_gamma * 255) for i in range(256)] * 3  # LUT for RGB
    image = image.point(lut)
    return image

def preprocess_image(image, filter_type=None, gamma=1.0):
    """
    Preprocess the image by applying gamma correction and optional filters.
    """
    image = apply_gamma_correction(image, gamma=gamma)
    if filter_type:
        if filter_type == 'GAUSSIAN':
            image = image.filter(ImageFilter.GaussianBlur(1))
        elif filter_type == 'SHARPEN':
            image = image.filter(ImageFilter.SHARPEN)
        elif filter_type == 'EDGE_ENHANCE':
            image = image.filter(ImageFilter.EDGE_ENHANCE)
        elif filter_type == 'BRIGHTNESS':
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(1.5)
    return image

def extract_text_with_conditions(image_path):
    """
    Extract text from an image with specified preprocessing conditions.
    """
    original_image = Image.open(image_path)

    # Apply specified settings directly
    options = {'filter_type': 'EDGE_ENHANCE', 'gamma': 0.8}
    contrast_level = 3.0

    image = preprocess_image(original_image, **options)
    enhancer = ImageEnhance.Contrast(image)
    enhanced_image = enhancer.enhance(contrast_level)
    text = pytesseract.image_to_string(enhanced_image, config='--psm 3')

    lines = text.split('\n')
    found_texts = []

    for line in lines:
        clean_line = re.sub(r'[\\\/\.,]', '', line).strip()
        if len(clean_line) >= 3 and re.match(r'^[A-Za-z0-9 :]+$', clean_line):
            found_texts.append(clean_line)

    if len(found_texts) > 1:
        # Initialize a variable to store the index of the string with a 6-digit number
        index_with_6_digit = -1
        # Iterate through found_texts to find a string with a 6-digit number
        for i, text in enumerate(found_texts):
            if re.search(r'\d{6}', text):
                # Remove all non-numeric characters from the string
                modified_text = re.sub(r'\D', '', text)
                # Update the list at the current index with the modified string
                found_texts[i] = modified_text
                index_with_6_digit = i
                break

        if index_with_6_digit != -1:
            # If a string with a 6-digit number was found and modified, rearrange the list
            found_texts.insert(1, found_texts.pop(index_with_6_digit))


    return found_texts, options, contrast_level
