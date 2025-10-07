#!/usr/bin/env python3
"""
Generate a PDF with one page per journalist showing their photo and information.
"""

import csv
import os
import re
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from PIL import Image
from difflib import SequenceMatcher

IMAGE_HEIGHT_INCHES = 7.5  # Height of photo in inches (A4 height is ~11.7 inches)


def sanitize_filename(name):
    """Convert name to safe filename."""
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = name.strip()
    return name


def similarity(str1, str2):
    """Calculate similarity ratio between two strings."""
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()


def normalize_name(name):
    """Normalize name for better matching."""
    return re.sub(r'\s+', ' ', name.lower().replace('-', ' ').replace('.', ' ')).strip()


def load_crossreference_cache(cache_file):
    """Load the crossreference cache from CSV.
    Returns a dict mapping cpj_name to either gigaza_name (if accepted) or None (if rejected).
    """
    cache = {}
    if not os.path.exists(cache_file):
        return cache

    with open(cache_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['accepted'] == 'yes':
                cache[row['cpj_name']] = row['gigaza_name']
            elif row['accepted'] == 'no':
                cache[row['cpj_name']] = None  # Mark as rejected

    return cache


def get_available_pictures(image_dir):
    """Get all available profile pictures with their base names."""
    pictures = {}
    if not os.path.exists(image_dir):
        return pictures

    for filename in os.listdir(image_dir):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
            # Remove extension to get the name
            base_name = re.sub(r'\.(jpg|jpeg|png|gif|webp)$', '', filename, flags=re.IGNORECASE)
            pictures[base_name] = os.path.join(image_dir, filename)

    return pictures


def find_image_file(name, image_dir, available_pictures=None, crossref_cache=None):
    """Find the image file for a given person name, with fuzzy matching fallback.
    Returns tuple: (filepath, source) where source is 'cpj', 'gigaza', or None
    """
    safe_name = sanitize_filename(name)

    # Try exact match first
    for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        filepath = os.path.join(image_dir, f"{safe_name}{ext}")
        if os.path.exists(filepath):
            return (filepath, 'cpj')

    # Check crossreference cache
    if crossref_cache and name in crossref_cache:
        cached_filename = crossref_cache[name]
        if cached_filename is None:
            # Previously rejected, skip fuzzy matching
            return (None, None)
        filepath = os.path.join(image_dir, cached_filename)
        if os.path.exists(filepath):
            return (filepath, 'gigaza')

    # If no exact match and we have available pictures, try fuzzy matching
    if available_pictures:
        normalized_name = normalize_name(name)
        best_match = None
        best_score = 0.7  # Minimum threshold for matching

        for pic_name, pic_path in available_pictures.items():
            normalized_pic = normalize_name(pic_name)
            score = similarity(normalized_name, normalized_pic)

            if score > best_score:
                best_score = score
                best_match = pic_path

        if best_match:
            print(f"  Fuzzy match score: {best_score:.2f} {name:<33} {os.path.basename(best_match)}")

            # If score is less than 0.8, ask for manual approval
            response = input(f"    Accept this match? (y/n): ").strip().lower()
            if response == 'y' or response == 'yes':
                return (best_match, 'gigaza')

            print(f"    Ignored")
            return (None, None)

    return (None, None)


def wrap_text(c, text, font_name, font_size, max_width):
    """Wrap text into multiple lines if needed."""
    words = text.split()
    lines = []
    line = ""

    for word in words:
        test_line = line + " " + word if line else word
        if c.stringWidth(test_line, font_name, font_size) <= max_width:
            line = test_line
        else:
            if line:
                lines.append(line)
            line = word

    if line:
        lines.append(line)

    return lines


def add_journalist_page(c, name, date, affiliation, image_path):
    """Add a page for one journalist to the PDF."""
    width, height = A4

    # Font sizes
    name_size = int(IMAGE_HEIGHT_INCHES * 5.5)
    date_size = int(IMAGE_HEIGHT_INCHES * 3.5)
    affiliation_size = int(IMAGE_HEIGHT_INCHES * 3.2)

    # Fixed position for name: 2/3 down the page
    name_y_position = height * (1 - 2/3)

    # Text area setup
    max_text_width = width - 1 * inch

    # Wrap name text
    name_lines = wrap_text(c, name, "Helvetica-Bold", name_size, max_text_width)

    # Calculate text block height
    text_y = name_y_position

    # Draw name (bold, wrapped)
    c.setFont("Helvetica-Bold", name_size)
    for line in name_lines:
        c.drawCentredString(width/2, text_y, line)
        text_y -= (name_size * 1.3)

    # Add date
    c.setFont("Helvetica", date_size)
    c.drawCentredString(width/2, text_y, date)
    text_y -= (date_size * 1.3)

    # Add affiliation (italic, wrapped by comma)
    c.setFont("Helvetica-Oblique", affiliation_size)
    if affiliation:
        words = affiliation.split(',')
        line = ""
        for word in words:
            word = word.strip()
            test_line = line + ", " + word if line else word

            if c.stringWidth(test_line, "Helvetica-Oblique", affiliation_size) < max_text_width:
                line = test_line
            else:
                if line:
                    c.drawCentredString(width/2, text_y, line)
                    text_y -= (affiliation_size * 1.2)
                line = word

        if line:
            c.drawCentredString(width/2, text_y, line)

    # Add image if available - fill top portion above name
    if image_path and os.path.exists(image_path):
        try:
            img = Image.open(image_path)
            img_width, img_height = img.size

            # Available space: from top to just above name position
            top_margin = 0.5 * inch
            image_bottom_margin = 0.3 * inch

            available_height = (height - top_margin) - (name_y_position + name_size * len(name_lines) * 1.3 + image_bottom_margin)
            max_width_img = width - (2 * 0.5 * inch)

            # Calculate scaled dimensions preserving aspect ratio
            aspect = img_width / img_height
            if aspect > max_width_img / available_height:
                display_width = max_width_img
                display_height = max_width_img / aspect
            else:
                display_height = available_height
                display_width = available_height * aspect

            # Center the image horizontally
            x_pos = (width - display_width) / 2
            # Position from top
            y_pos = height - top_margin - display_height

            c.drawImage(image_path, x_pos, y_pos,
                       width=display_width, height=display_height,
                       preserveAspectRatio=True, mask='auto')

        except Exception as e:
            print(f"  Error adding image for {name}: {e}")

def main():
    csv_file = '000_cpj-people-list-2025-10-07_02-08-13.csv'
    image_dir = 'profile_pictures'
    output_pdf = 'lambelambe.pdf'
    crossref_file = 'cpj_gigaza_crossreference.csv'

    # Load crossreference cache
    print("Loading crossreference cache...")
    crossref_cache = load_crossreference_cache(crossref_file)
    print(f"Found {len(crossref_cache)} cached matches\n")

    # Get all available pictures for fuzzy matching
    print("Loading available profile pictures...")
    available_pictures = get_available_pictures(image_dir)
    print(f"Found {len(available_pictures)} profile pictures\n")

    # Read all journalists from CSV
    journalists = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            journalists.append(row)

    total_pages = len(journalists)

    # Create PDF
    c = canvas.Canvas(output_pdf, pagesize=A4)

    print(f"Creating PDF with {total_pages} pages...")

    # Track statistics
    stats = {
        'total': 0,
        'with_image': 0,
        'cpj_images': 0,
        'gigaza_images': 0,
        'no_image': 0
    }

    for idx, person in enumerate(journalists, 1):
        name = person['Name']
        date = person['Date']
        affiliation = person['Journalist or Media Worker']

        print(f"[{idx}/{total_pages}] Adding page for {name}")

        image_path, source = find_image_file(name, image_dir, available_pictures, crossref_cache)
        add_journalist_page(c, name, date, affiliation, image_path)

        # Track statistics
        stats['total'] += 1
        if image_path:
            stats['with_image'] += 1
            if source == 'cpj':
                stats['cpj_images'] += 1
            elif source == 'gigaza':
                stats['gigaza_images'] += 1
        else:
            stats['no_image'] += 1

        # Start new page (except for last one)
        if idx < total_pages:
            c.showPage()

    # Save PDF
    c.save()
    print(f"\nPDF created: {output_pdf}")
    print(f"Total pages: {total_pages}")
    print(f"Pages with images: {stats['with_image']}/{stats['total']}")
    print(f"  - From CPJ: {stats['cpj_images']}")
    print(f"  - From Gigaza: {stats['gigaza_images']}")
    print(f"Pages without images: {stats['no_image']}")

if __name__ == '__main__':
    main()
