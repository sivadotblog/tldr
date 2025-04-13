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
    content = BeautifulSoup(html_content, 'html.parser')
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
    if len(sys.argv) < 4:
        raise IndexError("Not enough arguments provided. Usage: script.py <category> <from_date> <to_date>")
    category = sys.argv[1]
    from_date = datetime.strptime(sys.argv[2], '%Y-%m-%d')
    to_date = datetime.strptime(sys.argv[3], '%Y-%m-%d')

    current_date = from_date
    while current_date <= to_date:
        date_str = current_date.strftime('%Y-%m-%d')
        html_content = fetch_newsletter(category, date_str)
        markdown_content = parse_html_to_markdown(html_content)
        save_markdown(category, date_str, markdown_content)
        current_date += timedelta(days=1)
