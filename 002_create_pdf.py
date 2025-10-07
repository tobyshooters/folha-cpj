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

IMAGE_HEIGHT_INCHES = 7.5  # Height of photo in inches (A4 height is ~11.7 inches)


def sanitize_filename(name):
    """Convert name to safe filename."""
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = name.strip()
    return name


def find_image_file(name, image_dir):
    """Find the image file for a given person name."""
    safe_name = sanitize_filename(name)

    # Try common image extensions
    for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
        filepath = os.path.join(image_dir, f"{safe_name}{ext}")
        if os.path.exists(filepath):
            return filepath

    return None


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

    for idx, person in enumerate(journalists, 1):
        name = person['Name']
        date = person['Date']
        affiliation = person['Journalist or Media Worker']

        print(f"[{idx}/{total_pages}] Adding page for {name}")

        image_path = find_image_file(name, image_dir)
        add_journalist_page(c, name, date, affiliation, image_path)

        # Start new page (except for last one)
        if idx < total_pages:
            c.showPage()

    # Save PDF
    c.save()
    print(f"\nPDF created: {output_pdf}")
    print(f"Total pages: {total_pages}")

if __name__ == '__main__':
    main()
