import os
import requests
from bs4 import BeautifulSoup
import markdownify
from datetime import datetime, timedelta

def fetch_newsletter(category, date):
    url = f"https://tldr.tech/{category}/{date}"
    response = requests.get(url)
    if response.status_code == 200:
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
    category = sys.argv[1]
    date = sys.argv[2]
    html_content = fetch_newsletter(category, date)
    markdown_content = parse_html_to_markdown(html_content)
    save_markdown(category, date, markdown_content)
