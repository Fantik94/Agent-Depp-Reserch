import requests
from bs4 import BeautifulSoup

def scrap_url(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        paragraphs = soup.find_all('p')
        text = "\n".join([p.get_text() for p in paragraphs])
        return text[:2000]
    else:
        return f"Erreur lors de la récupération de {url} : {response.status_code}" 