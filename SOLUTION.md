# Insurance Carrier Web Scraper


## Setup and Running

### 1. Prerequisites
- Python 3.9+ 


### 2. Copy and Initialize

```bash
# Enter the project directory
cd adapt-engineering-take-home-qzqgqc/data_scrapers

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install dependencies
pip install beautifulsoup4 playwright

# Install Playwright browser binaries
playwright install chromium
```

### 3. Run the Scraper
The scraper reads from a list of URLs defined in `src/main.py`.

```bash
# Run the main script
python src/main.py
```

The results will be saved to `src/output.json`.

---

## Implementation Summary

The application follows a modular, heuristic-driven architecture to maximize extensibility across different website designs.
Application is intended to be moduler with a main.py as a starting point and generic_scraper.py as the engine for scraping. It also has a models.py for defining formatted data models. Although we can get raw_data and don't necesarily need a Data model but it would be cleaner solution to have a data model.

### Core Components
1. **`generic_scraper.py`**: It fetches content, parses HTML into a generic JSON-like structure and maps that structure to Data models.
2. **`models.py`**: Data structures defining the schema for `Insured`, `Agency`, and `Policy`. Also has a `ScrapeResult` class that stores the final result and raw_data.
3. **`main.py`**: Entry point that allows scraping multiple URLs and saves the final result. Final result is stored in a JSON file and printed to console. For fiesibility it prints the raw_data as well as Formated in Data models.

---

## Considerations & Tradeoffs
- I used Playwright over Requests to get html content of the page.I initially used requests and worked fine for one example but failed when there was pagination and dynamic content loading from javascript

- Using Data model wasn't necessary but it helped me with reconcilation. For eg when I was quering dynamic content with details, it used to read the label as one continous string instead of reading it as label and value. Having a data model helped me with reconcilation
