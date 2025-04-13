import os
import requests
from bs4 import BeautifulSoup
import markdownify
from datetime import datetime
import logging

def fetch_newsletter(category, date):
    url = f"https://tldr.tech/{category}/{date}"
    response = requests.get(url)
    if response.status_code == 200:
        if response.url != url:
            return None
        return response.text
    else:
        raise Exception(f"Failed to fetch newsletter for {category} on {date}")

def parse_html_to_markdown(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    content = soup.find('div', {'class': 'newsletter-content'})
    markdown_content = markdownify.markdownify(str(content), heading_style="ATX")
    return markdown_content

def save_markdown(category, date, markdown_content):
    directory = f"tldr/{category}"
    if not os.path.exists(directory):
        os.makedirs(directory)
    file_path = f"{directory}/{date}.md"
    with open(file_path, 'w') as file:
        file.write(markdown_content)

if __name__ == "__main__":
    import sys
    logging.basicConfig(level=logging.INFO)
    try:
        category = sys.argv[1]
        date = sys.argv[2]
        mode = sys.argv[3] if len(sys.argv) > 3 else "daily"
        logging.info(f"Running {mode} mode for category: {category} on date: {date}")
        html_content = fetch_newsletter(category, date)
        if html_content is None:
            logging.info(f"No newsletter found for {category} on {date}, skipping file creation.")
        else:
            markdown_content = parse_html_to_markdown(html_content)
            save_markdown(category, date, markdown_content)
            logging.info(f"Successfully processed {category} newsletter for {date}")
    except Exception as e:
        logging.error(f"Error processing {category} newsletter for {date}: {e}")
