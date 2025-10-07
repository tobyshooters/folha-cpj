#!/usr/bin/env python3
"""
Download profile pictures from CPJ people pages.
"""

import csv
import os
import re
import requests
from requests_html import HTMLSession
from urllib.parse import urlparse
import time


def sanitize_filename(name):
    # Remove or replace characters that are problematic in filenames
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = name.strip()
    return name


def download_image(url, filepath):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        with open(filepath, 'wb') as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"  Error downloading image: {e}")
        return False


def get_profile_image(session, person_url):
    try:
        response = session.get(person_url)
        response.raise_for_status()

        # Render JavaScript to load dynamic content
        response.html.render(timeout=20, sleep=2)

        # Look for the image using CSS selector
        img = response.html.find('img#photoUrl', first=True)
        if img and img.attrs.get('src'):
            return img.attrs['src']

        return None
    except Exception as e:
        print(f"  Error fetching page: {e}")
        return None


def main():
    csv_file = '000_cpj-people-list-2025-10-07_02-08-13.csv'
    output_dir = 'profile_pictures'

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Create session for requests-html
    session = HTMLSession()

    # Track statistics
    total = 0
    downloaded = 0
    no_image = 0
    failed = 0

    # Read CSV and process each person
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)

        for row in reader:
            total += 1
            name = row['Name']
            cpj_url = row['cpj.org URL']

            print(f"\n[{total}] Processing: {name}")
            print(f"  URL: {cpj_url}")

            # Get image URL
            image_url = get_profile_image(session, cpj_url)
            if not image_url:
                print(f"  No image found")
                no_image += 1
                continue

            print(f"  Image URL: {image_url}")

            # Determine file extension from URL
            parsed = urlparse(image_url)
            ext = os.path.splitext(parsed.path)[1]
            if not ext or ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
                ext = '.jpg'  # Default to jpg

            # Create filename
            safe_name = sanitize_filename(name)
            filename = f"{safe_name}{ext}"
            filepath = os.path.join(output_dir, filename)

            # Download image
            if download_image(image_url, filepath):
                print(f"  Downloaded: {filename}")
                downloaded += 1
            else:
                failed += 1

            # Be polite - add a small delay between requests
            time.sleep(0.5)

    # Print summary
    print(f"Total people: {total}")
    print(f"Successfully downloaded: {downloaded}")
    print(f"No image found: {no_image}")
    print(f"Failed downloads: {failed}")

if __name__ == '__main__':
    main()
