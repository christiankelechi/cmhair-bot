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
        r'slug': 'slug',
        r'product code': 'product_code',
        r'code': 'product_code',
        r'no': 'product_code',
        r'item no': 'product_code',
        r'original price': 'original_price',
        r'discount price': 'price',
        r'cost price': 'price',
        r'price': 'price',
        r'stock': 'stock',
        r'capsize': 'cap_sizes',
        r'category': 'category_name',
        r'inches': 'lengths',
        r'length': 'lengths',
        r'bundles': 'bundles',
        r'colors': 'colors',
        r'color': 'colors',
        r'parting': 'parting_options',
        r'styling': 'styling',
        r'style': 'styling',
        r'unavailable lengths': 'unavailable_lengths',
        r'out of stock': 'unavailable_lengths',
        r'image color mapping': 'image_color_mapping',
        r'color mapping': 'image_color_mapping',
        r'badge': 'badge',
        r'description': 'description',
        r'desc': 'description',
        r'videos': 'videos',
    }
    
    # Sort patterns by length descending to match most specific first
    sorted_patterns = sorted(mapping.keys(), key=len, reverse=True)
    
    for line in lines:
        if ':' not in line:
            continue
        key_part, val_part = line.split(':', 1)
        key_part = key_part.lower().strip()
        val_part = val_part.strip()
        
        # Special case for "inches" which mapped to "lengths"
        # and "capsize" which mapped to "cap_sizes" 
        
        for pattern in sorted_patterns:
            if pattern in key_part:
                field = mapping[pattern]
                if field in ('cap_sizes', 'lengths', 'bundles', 'colors', 'parting_options', 'styling', 'unavailable_lengths'):
                    vals = [v.strip() for v in val_part.split(',') if v.strip()]
                    
                    if field == 'lengths' or field == 'unavailable_lengths':
                        parsed_vals = []
                        length_prices = []
                        for v in vals:
                            # Clean "inches"/"in" from the value
                            v_clean = re.sub(r'(?i)\s*(inches|inch|in)\s*', '', v).strip()
                            
                            if field == 'lengths' and (':' in v or '$' in v):
                                # example: "10:$150" or "10: 150"
                                parts = v.split(':') if ':' in v else v.split('$')
                                if len(parts) >= 2:
                                    length = re.sub(r'(?i)\s*(inches|inch|in)\s*', '', parts[0].replace('$', '')).strip()
                                    price_str = re.sub(r'[^\d.]', '', parts[1])
                                    if price_str:
                                        length_prices.append({"length": length, "price": float(price_str)})
                                        parsed_vals.append(length)
                                    else:
                                        parsed_vals.append(v_clean)
                            else:
                                parsed_vals.append(v_clean)
                        data[field] = parsed_vals
                        if length_prices:
                            data['length_prices'] = length_prices
                    else:
                        data[field] = vals
                elif field == 'image_color_mapping':
                    # input format: "red":"1","blue":"2"
                    # We want to extract it as a dict or keep it for the handler to process
                    # Let's parse it into a dict of {color: index_str}
                    mapping_dict = {}
                    # Simple regex to find "key":"val" pairs
                    pairs = re.findall(r'"([^"]+)":"([^"]+)"', val_part)
                    for k, v in pairs:
                        mapping_dict[k.strip()] = v.strip()
                    data[field] = mapping_dict
                elif field in ('price', 'original_price'):
                    # Remove currency symbols and commas
                    val = re.sub(r'[^\d.]', '', val_part.replace(',', ''))
                    try:
                        data[field] = float(val)
                    except ValueError:
                        pass
                elif field == 'stock':
                    slower = val_part.lower()
                    if 'available' in slower:
                        data[field] = 99
                        data['is_preorder'] = False
                    elif 'pre' in slower:
                        data[field] = 0
                        data['is_preorder'] = True
                    else:
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
        "Slug: curls-2024\n"
        "Product Code: CMH 570\n"
        "Original Price: $1320\n"
        "Cost Price: $1270\n"
        "Stock: 1\n"
        "Capsize: Medium\n"
        "Category: Wigs\n"
        "Inches: 26:$1270, 28:$1350\n"
        "Unavailable Lengths: 10, 12\n"
        "Styling: Body Wave, Deep Wave Layers\n"
        "Parting: Middle Part, Side Part\n"
        "Bundles: 3.5\n"
        "Colors: Natural color, Custom Made\n"
        "Image Color Mapping: \"Natural color\":\"1\", \"Custom Made\":\"2\"\n"
        "Description: 26/3.5 SSW CLOSURE WIG NATURAL COLOR"
    )
