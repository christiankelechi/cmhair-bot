import re

def parse_template(text: str) -> dict:
    """
    Parses a structured product template text.
    Returns a dict with product fields.
    """
    data = {}
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    
    mapping = {
        r'product name': 'name',
        r'no': 'product_name',
        r'item no': 'product_name',
        r'original price': 'original_price',
        r'cost price': 'price',
        r'price': 'price',
        r'stock': 'stock',
        r'capsize': 'cap_sizes',
        r'category': 'category_name',
        r'inches': 'lengths',
        r'bundles': 'bundles',
        r'colors': 'colors',
        r'badge': 'badge',
        r'description': 'description',
        r'videos': 'videos',
    }
    
    for line in lines:
        if ':' not in line:
            continue
        key_part, val_part = line.split(':', 1)
        key_part = key_part.lower().strip()
        val_part = val_part.strip()
        
        # Special case for "inches" which mapped to "lengths"
        # and "capsize" which mapped to "cap_sizes" 
        
        for pattern, field in mapping.items():
            if pattern in key_part:
                if field in ('cap_sizes', 'lengths', 'bundles', 'colors'):
                    # Handle multiple values separated by commas or just single value
                    vals = [v.strip() for v in val_part.split(',') if v.strip()]
                    # If it's something like "26" for inches, we store as ["26"]
                    data[field] = vals
                elif field in ('price', 'original_price'):
                    # Remove currency symbols and commas
                    val = re.sub(r'[^\d.]', '', val_part.replace(',', ''))
                    try:
                        data[field] = float(val)
                    except ValueError:
                        pass
                elif field == 'stock':
                    val = re.sub(r'[^\d]', '', val_part)
                    try:
                        data[field] = int(val)
                    except ValueError:
                        pass
                else:
                    data[field] = val_part
                break
    return data

def get_template_example() -> str:
    return (
        "Product name: curls\n"
        "No: CMH 570\n"
        "Original Price: $1320\n"
        "Cost Price: $1270\n"
        "Stock: 1\n"
        "Capsize: Medium\n"
        "Category: Wigs\n"
        "Inches: 26\n"
        "Bundles: 3.5\n"
        "Colors: Natural color, Custom Made\n"
        "DESCRIPTION: 26/3.5 SSW CLOSURE WIG NATURAL COLOR"
    )
