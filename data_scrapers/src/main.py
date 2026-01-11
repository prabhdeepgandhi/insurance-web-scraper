import json
import sys
import os
from dataclasses import asdict

from generic_scraper import GenericScraper

def main():
    input_urls = []
    # Create a text file called urls.txt with the urls to scrape    
    input_file = 'urls.txt'
   

    with open(input_file, 'r') as f:
        input_urls = [line.strip() for line in f if line.strip()]

    scraper = GenericScraper()
    results = []

    print(f"Starting generic scrape for {len(input_urls)} urls...")

    for url in input_urls:

        try:
            path_parts = url.split('/')
            if len(path_parts) > 2:
                carrier_slug = path_parts[-2]
                carrier = carrier_slug.replace('_', ' ').title()
            else:
                carrier = "Unknown Carrier"
        except:
            carrier = "Unknown URL"
        
        try:
            print(f"\nProcessing ({url})...")
            result = scraper.scrape(url)
         
            result_dict = asdict(result)
            
         
            result_dict["source_url"] = url
            

            results.append(result_dict)
            # print(f"Successfully scraped {carrier}")
            
        except Exception as e:
            print(f"Failed to scrape {carrier}: {e}")


    print("\n--- Final JSON Output ---")
    print(json.dumps(results, indent=2))
    
    # Save to file
    with open('output.json', 'w') as f:
        json.dump(results, f, indent=2)
        print("\nSaved to output.json")

if __name__ == "__main__":
    main()
