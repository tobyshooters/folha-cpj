### Memorial Jornalistas

Generates a memorial PDF with one page per journalist, including their photo
and information from the Committee to Protect Journalists database.

Cross-references with GiGaza to get more images.

The CSV file is downloaded from CPJ's database via the "Download this database"
butotn.

https://cpj.org/data/killed/2025/?status=Killed&motiveConfirmed%5B%5D=Confirmed&motiveUnconfirmed%5B%5D=Unconfirmed&type%5B%5D=Journalist&type%5B%5D=Media%20Worker&cc_fips%5B%5D=IS&start_year=2023&end_year=2025&group_by=location

### Dependencies

```bash
pip install requests-html reportlab pillow
```

- `download_images.py` uses `requests-html` to handle JavaScript-rendered images
- `create_pdf.py` uses ReportLab for reliable PDF generation with embedded images
