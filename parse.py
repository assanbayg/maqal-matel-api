import requests
from bs4 import BeautifulSoup

url = "https://bilim-all.kz/quote/proverb"

response = requests.get(url)

if response.status_code == 200:
    soup = BeautifulSoup(response.text, "html.parser")
    blockquotes = soup.find_all("blockquote")

    makal_matel_list = []

    for i, b in enumerate(blockquotes, 1):
        makal_matel_text = b.text.strip()
        # Split text into text and topics using "Ілмектер:" as a benchmark
        text_part, topics_part = map(str.strip, makal_matel_text.split("Ілмектер:"))
        topics = [topic.strip() for topic in topics_part.split(",")]

        # Create a dictionary for the current makal matel
        makal_matel_dict = {"text": text_part, "topics": topics}
        makal_matel_list.append(makal_matel_dict)

    for saying in makal_matel_list:
        print(saying)
else:
    print(f"Failed to retrieve the page. Status code: {response.status_code}")
