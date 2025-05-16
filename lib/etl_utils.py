# Language native package
import re
from datetime import datetime
from typing import List, Dict


# Standardize the names of the weekdays
WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thur', 'Fri', 'Sat', 'Sun']


def expand_days(day_str: str) -> List[str]:
    """
    Expand strings like 'Mon - Fri' or 'Mon, Wed, Fri' into a list of individual weekdays.
    :param day_str: A string representing the days of the week.    
    """
    days = []
    segments = [seg.strip() for seg in day_str.split(',')]
    for seg in segments:
        if '-' in seg:
            start_day, end_day = seg.split('-')
            start_index = WEEKDAYS.index(start_day.strip())
            end_index = WEEKDAYS.index(end_day.strip())
            # Support for cross-week (e.g., Fri - Mon)
            if start_index <= end_index:
                days += WEEKDAYS[start_index:end_index + 1]
            else:
                days += WEEKDAYS[start_index:] + WEEKDAYS[:end_index + 1]
        else:
            days.append(seg)
    return days


def parse_schedule(schedule_str: str) -> List[Dict]:
    """
    Parse the raw time string into a structured dictionary.
    :param schedule_str: A string representing the schedule, e.g., "Mon - Fri 08:00 - 12:00"
    """
    results = []
    parts = [p.strip() for p in schedule_str.split('/')]
    
    for part in parts:
        match = re.match(r'^(.+?)\s+(\d{2}:\d{2})\s*-\s*(\d{2}:\d{2})$', part)
        if match:
            day_part, start_time, end_time = match.groups()
            days = expand_days(day_part)
            for day in days:
                results.append({
                    "day_of_week": day,
                    "start_time": datetime.strptime(start_time, "%H:%M").time(),
                    "end_time": datetime.strptime(end_time, "%H:%M").time()
                })
        else:
            raise ValueError(f"Error format: {part}")
    
    return results


def parse_product_string(product_str: str) -> Dict:
    """
    Parse the product string into a structured dictionary.
    
    :param product_str: A string representing the product, e.g., "True Barrier (green) (3 per pack)"
    :return: Dictionary with brand, color, and pack_size
    :raises ValueError: If any required information is missing in the string
    """
    bracket_regex = r'\([^)]+\)'
    color_regex = r'\(([^)]+)\)'
    quantity_regex = r'(\d+)\s*per\s*pack'

    results = {}
    
    brand_text = re.sub(bracket_regex, '', product_str).strip()
    if brand_text:
        results['brand'] = brand_text
    else:
        raise ValueError(f"Could not extract brand name from: {product_str}")

    color_match = re.search(color_regex, product_str)
    if color_match:
        results['color'] = color_match.group(1)
    else:
        raise ValueError(f"Could not extract color from: {product_str}")

    quantity_match = re.search(quantity_regex, product_str)
    if quantity_match:
        results['pack_size'] = int(quantity_match.group(1))
    else:
        raise ValueError(f"Could not extract pack size from: {product_str}")

    return results
