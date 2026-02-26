import json
import re

import requests
from bs4 import BeautifulSoup

base_url = "https://bilim-all.kz/quote/proverb?page={}"
total_pages = 496

maqal_mattel_list = []

for page_number in range(1, total_pages + 1):
    url = base_url.format(page_number)
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        blockquotes = soup.find_all("blockquote")

        # Check if there are blockquotes just in case
        if not blockquotes:
            break

        for i, b in enumerate(blockquotes, 1):
            maqal_mattel_text = b.text.strip()
            # Split text into text and topics using "Ілмектер:" as a benchmark
            text_part, topics_part = map(
                str.strip, maqal_mattel_text.split("Ілмектер:")
            )
            # Split at both # and comma
            topics = re.split(r"#|,", topics_part)
            topics = [topic.strip() for topic in topics if topic]

            # Create a dictionary for the current maqal mattel
            maqal_mattel_dict = {"text": text_part, "topics": topics}
            maqal_mattel_list.append(maqal_mattel_dict)
    else:
        print(
            f"Failed to retrieve the page number {page_number}. Status code: {response.status_code}"
        )
        break

# Save the list to a JSON file
with open("maqal_mattel_data.json", "w", encoding="utf-8") as json_file:
    json.dump(maqal_mattel_list, json_file, ensure_ascii=False, indent=2)

print(f"Data successfully saved to 'maqal_mattel_data.json' from {total_pages} pages.")
