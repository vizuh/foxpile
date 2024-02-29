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
    Extract text from an image with specified preprocessing conditions, including Cyrillic characters.
    """
    original_image = Image.open(image_path)

    # Apply specified settings directly
    options = {'filter_type': 'SHARPEN', 'gamma': 0.8}
    contrast_level = 2.5


    image = preprocess_image(original_image, **options)
    enhancer = ImageEnhance.Contrast(image)
    enhanced_image = enhancer.enhance(contrast_level)

    # Add 'rus' to the lang option to include Russian (Cyrillic)
    text = pytesseract.image_to_string(enhanced_image, config='--psm 3', lang='eng+rus')

    lines = text.split('\n')
    found_texts = []

    for line in lines:
        # Adjust the regex to include Cyrillic and use re.UNICODE flag
        clean_line = re.sub(r'[\\\/\.,]', '', line, flags=re.UNICODE).strip()
        if len(clean_line) >= 3 and re.match(r'^[A-Za-z0-9 А-Яа-я:]+$', clean_line, flags=re.UNICODE):
            found_texts.append(clean_line)

    if len(found_texts) > 1:
        index_with_6_digit = -1
        for i, text in enumerate(found_texts):
            if re.search(r'\d{6}', text):
                modified_text = re.sub(r'\D', '', text)
                found_texts[i] = modified_text
                index_with_6_digit = i
                break

        if index_with_6_digit != -1:
            found_texts.insert(1, found_texts.pop(index_with_6_digit))


    return found_texts, options, contrast_level