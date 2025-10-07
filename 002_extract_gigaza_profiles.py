#!/usr/bin/env python3
"""
Extract profile pictures from gigaza-org.html and save them with their gigaza names.
"""

import os
import re
import requests
import time


def parse_gigaza_html(html_content):
    """Parse HTML to extract names and image URLs."""
    entries = []

    # Pattern to match image followed by heading
    pattern = r'<img[^>]*src="([^"]+)"[^>]*>[\s\S]*?<h2[^>]*class="elementor-heading-title[^>]*>([^<]+)</h2>'

    matches = re.finditer(pattern, html_content)

    for match in matches:
        image_url = match.group(1)
        name = match.group(2).strip()
        entries.append({'name': name, 'imageUrl': image_url})

    return entries


def sanitize_filename(name):
    """Remove or replace characters that are problematic in filenames."""
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = name.strip()
    return name


def download_image(url, filepath):
    """Download image from URL to filepath."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        with open(filepath, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        raise Exception(f"Failed to download: {e}")


def main():
    print('Starting gigaza.org profile extraction...\n')

    # Read HTML file
    with open('000_gigaza_org.html', 'r', encoding='utf-8') as f:
        html_content = f.read()

    gigaza_entries = parse_gigaza_html(html_content)
    print(f'Found {len(gigaza_entries)} entries in gigaza-org.html\n')

    # Create output directory
    output_dir = 'profile_pictures'
    os.makedirs(output_dir, exist_ok=True)

    # Check existing files
    existing_files = os.listdir(output_dir)
    existing_names = set(re.sub(r'\.(jpg|png|jpeg)$', '', f, flags=re.IGNORECASE)
                        for f in existing_files)

    downloaded = 0
    skipped = 0
    failed = 0

    # Process each gigaza entry
    for entry in gigaza_entries:
        gigaza_name = entry['name']
        safe_name = sanitize_filename(gigaza_name)

        # Check if we already have this file
        if safe_name in existing_names:
            print(f"⊘ Skipped (already exists): {gigaza_name}")
            skipped += 1
            continue

        # Determine file extension from URL
        ext = '.jpg'
        if '.png' in entry['imageUrl'].lower():
            ext = '.png'
        elif '.jpeg' in entry['imageUrl'].lower():
            ext = '.jpeg'

        filename = f"{safe_name}{ext}"
        filepath = os.path.join(output_dir, filename)

        try:
            download_image(entry['imageUrl'], filepath)
            print(f"✓ Downloaded: {gigaza_name}")
            downloaded += 1
        except Exception as e:
            print(f"✗ Failed: {gigaza_name} - {e}")
            failed += 1

        # Small delay to avoid overwhelming the server
        time.sleep(0.1)

    # Generate report
    print(f"Total entries processed: {len(gigaza_entries)}")
    print(f"Successfully downloaded: {downloaded}")
    print(f"Skipped (already exists): {skipped}")
    print(f"Failed downloads: {failed}")


if __name__ == '__main__':
    main()
