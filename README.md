# CPJ Journalists Memorial

Generates a memorial PDF with one page per journalist, including their photo
and information from the Committee to Protect Journalists database.

## Data Source

The CSV file is downloaded from CPJ's database:

https://cpj.org/data/killed/2025/?status=Killed&motiveConfirmed%5B%5D=Confirmed&motiveUnconfirmed%5B%5D=Unconfirmed&type%5B%5D=Journalist&type%5B%5D=Media%20Worker&cc_fips%5B%5D=IS&start_year=2023&end_year=2025&group_by=location

Click "Download this database" button to get the CSV file.

## Files

- `cpj-people-list-2025-10-07_02-08-13.csv` - Source data (197 journalists)
- `download_images.py` - Scrapes profile pictures from CPJ.org
- `create_pdf.py` - Generates memorial PDF with photos and info
- `profile_pictures/` - Downloaded images (created by script)
- `lambelambe.pdf` - Final output

## Usage

### 1. Install Dependencies

```bash
pip install requests-html reportlab pillow
```

### 2. Download Profile Pictures

```bash
python3 001_download_images.py
```

Scrapes each journalist's CPJ.org profile page using `requests-html` to render
JavaScript, extracts the profile photo, and saves to `profile_pictures/`.

### 3. Generate PDF

```bash
python3 002_create_pdf.py
```

## Technical Details

- `download_images.py` uses `requests-html` to handle JavaScript-rendered images
- `create_pdf.py` uses ReportLab for reliable PDF generation with embedded images
- Images are automatically scaled to fit while preserving aspect ratio
- Text is centered and wrapped automatically for long affiliations
