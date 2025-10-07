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


def add_journalist_page(c, name, date, affiliation, image_path):
    """Add a page for one journalist to the PDF."""
    width, height = A4

    # All dimensions derived from IMAGE_HEIGHT_INCHES
    top_margin = 0.5 * inch
    image_text_gap = IMAGE_HEIGHT_INCHES * 0.08 * inch
    name_size = int(IMAGE_HEIGHT_INCHES * 5.5)
    date_size = int(IMAGE_HEIGHT_INCHES * 3.5)
    affiliation_size = int(IMAGE_HEIGHT_INCHES * 3.2)

    # Calculate vertical start
    y_start = height - top_margin

    # Add image if available
    has_image = image_path and os.path.exists(image_path)

    if has_image:
        try:
            img = Image.open(image_path)
            img_width, img_height = img.size

            # Calculate scaled dimensions based on IMAGE_HEIGHT_INCHES
            max_width = width - (2 * 0.5 * inch)  # 0.5 inch margin on each side
            max_height = IMAGE_HEIGHT_INCHES * inch

            # Calculate aspect ratio
            aspect = img_width / img_height
            if aspect > max_width / max_height:
                display_width = max_width
                display_height = max_width / aspect
            else:
                display_height = max_height
                display_width = max_height * aspect

            # Center the image horizontally
            x_pos = (width - display_width) / 2
            y_pos = y_start - display_height

            c.drawImage(image_path, x_pos, y_pos,
                       width=display_width, height=display_height,
                       preserveAspectRatio=True, mask='auto')

            # Update y position for text below image
            y_start = y_pos - image_text_gap

        except Exception as e:
            print(f"  Error adding image for {name}: {e}")
            has_image = False

    if not has_image:
        # If no image, center text vertically
        total_text_height = name_size * 1.3 + date_size * 1.3 + affiliation_size * 2.5
        y_start = height / 2 + total_text_height / 2

    # Add name (bold, scaled)
    c.setFont("Helvetica-Bold", name_size)
    c.drawCentredString(width/2, y_start, name)
    y_start -= (name_size * 1.3)

    # Add date (scaled)
    c.setFont("Helvetica", date_size)
    c.drawCentredString(width/2, y_start, date)
    y_start -= (date_size * 1.3)

    # Add affiliation (italic, scaled)
    c.setFont("Helvetica-Oblique", affiliation_size)

    # Simple text wrapping for affiliation
    max_line_width = width - 1*inch
    if affiliation:
        words = affiliation.split(',')
        line = ""
        for word in words:
            word = word.strip()
            test_line = line + ", " + word if line else word

            # Simple check - if too long, print line and start new one
            if c.stringWidth(test_line, "Helvetica-Oblique", affiliation_size) < max_line_width:
                line = test_line
            else:
                if line:
                    c.drawCentredString(width/2, y_start, line)
                    y_start -= (affiliation_size * 1.2)
                line = word

        # Print remaining line
        if line:
            c.drawCentredString(width/2, y_start, line)

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
