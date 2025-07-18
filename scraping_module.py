from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def scrap_url(url):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')
    options.add_argument('user-agent=Mozilla/5.0')
    driver = webdriver.Chrome(options=options)
    try:
        driver.get(url)
        paragraphs = driver.find_elements(By.TAG_NAME, 'p')
        text = "\n".join([p.text for p in paragraphs])
        return text[:2000]
    except Exception as e:
        return f"Erreur lors de la récupération de {url} : {str(e)}"
    finally:
        driver.quit()