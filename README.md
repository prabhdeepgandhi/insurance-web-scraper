# Insurance Web Scraper

## Overview
A Python web scraper that extracts insurance carrier data from dynamic web pages using Playwright and BeautifulSoup. It is designed as a learning project and **intended for personal experimentation only**.

## Personal‑Use Disclaimer
This repository is provided **solely for personal use and educational purposes**. It is **not** intended for production deployment, commercial use, or handling of sensitive personal data. Use at your own risk.

## Setup & Installation
```bash
# Clone the repository
git clone https://github.com/prabhdeepgandhi/insurance-web-scraper.git
cd insurance-web-scraper

# Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt  # or: pip install beautifulsoup4 playwright

# Install Playwright browsers
playwright install chromium
```

## Usage
1. Add the URLs you wish to scrape to `data_scrapers/src/urls.txt`, one per line.
2. Run the scraper:
```bash
python data_scrapers/src/main.py
```
3. The results are printed to the console and saved to `output.json`.

## Removing URLs / PII Before Publishing
- The file `data_scrapers/src/urls.txt` is listed in `.gitignore` and will not be committed.
- Ensure that `output.json` does **not** contain any hard‑coded URLs or email addresses before pushing the repository publicly. You can clear or delete `output.json` after verifying the scraped data.

## License
[Insert license information here]

## Contributing
Feel free to open issues or submit pull requests for improvements or bug fixes.
