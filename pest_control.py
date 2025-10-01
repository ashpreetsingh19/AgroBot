import requests
from bs4 import BeautifulSoup

class PestControl:
    def __init__(self):
        self.url = "https://sites.google.com/view/pest-advice/home"

    def fetch_pest_advice(self, crop):
        try:
            response = requests.get(self.url)
            response.raise_for_status()  # Raise an error for bad responses

            # Parse the website content using BeautifulSoup
            soup = BeautifulSoup(response.content, 'html.parser')

            # Extract content from the site
            content = []
            for item in soup.find_all(['h2', 'h3', 'p']):  # Example: fetching headings and paragraphs
                text = item.get_text(strip=True)
                if crop.lower() in text.lower():  # Case-insensitive search for crop name
                    content.append(text)

            return "\n".join(content) if content else "No advice found for this crop."

        except requests.RequestException as e:
            print(f"Error fetching the site: {e}")
            return "Error fetching pest advice."

    def get_advice(self, crop):
        return self.fetch_pest_advice(crop)
