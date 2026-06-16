import requests
from bs4 import BeautifulSoup
import pandas as pd
import os.path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def scrape_alternet_politics(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com",
        "Connection": "keep-alive",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
    }

    if url == 'https://www.thedailybeast.com/category/politics/':
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        try:
            driver.get(url)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            #return soup
        finally:
            driver.quit()
    else:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"Failed to fetch the page: {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")

    # Find the articles
    articles = []
    for article in soup.find_all('a'):
        try:
            # Extract headline
            if url == 'https://www.motherjones.com/politics/':
                title = article.get('title')
                title = title.replace('Permalink to ', '') if title else ''
            elif article.get('class') and 'AnchorLink' in article.get('class'):
                # For the specific HTML structure provided
                title = article.text.strip()  # Use the text inside the anchor tag
            elif article.find('h2', class_='wide-tease-item__headline'):
                # For the specific HTML structure provided
                title = article.find('h2', class_='wide-tease-item__headline').text.strip()
            elif article.get('class') and 'gnt_m_th_a' in article.get('class'):
                # Specifically for articles with class "gnt_m_th_a"
                title = article.contents[0].strip()  # Extract only the text part before any child div
            else:
                title = article.get('aria-label') or article.text.strip()

            # Extract link
            if url == 'https://www.thedailybeast.com/category/politics/':
                link = 'https://www.thedailybeast.com' + article.get('href')
            elif url == 'https://www.theguardian.com/us-news/us-politics':
                link = 'https://www.theguardian.com' + article.get('href')
            elif url == 'https://www.usatoday.com/news/nation/':
                link = 'https://www.usatoday.com' + article.get('href')  # Adjust base URL for relative paths
            else:
                link = article.get('href')

            # Append to the list
            if (("None" not in title) and ("Link to" not in title) and ("alternet feed" not in title) and ("show search" not in title)\
            and ("Open facebook" not in title) and ("Open twitter" not in title) and ("google plus icon" not in title) and ("Open instagram" not in title)\
            and ("Open pinterest" not in title) and ("youtube icon" not in title) and ("snapchat icon" not in title) and ("home page" not in title)\
            and ("No Title" not in title) and (len(title) > 30) and ("The Daily Beast" not in title) and ("Newsletters" not in title) and ("cheatsheet" not in title) \
            and ("login" not in title) and ("Search" not in title) and ("Subscription" not in title) and ("Crossword" not in title) and ("Podcasts" not in title) \
            and ("Follow us on" not in title) and ("Go to HuffPost News" not in title) and ("Log In" not in title) and ("Previous page" not in title)
            and ("https://" in link) and ("Go to Homepage" not in title) and ("By " not in title) and ("Posts by" not in title) and ("Donate" not in title)
            and ("Subscribe" not in title) and ("Go to" not in title) and ("View the current issue:" not in title) and ("Your US State Privacy Rights" not in title)
            and ("Do Not Sell or Share My Personal Information" not in title) and ("Children's Online Privacy Policy" not in title) and ("Listen" not in title)
            and ("Keyboard shortcuts for audio player" not in title) and ("The NPR Politics Podcast" not in title) and ("Wild Card with" not in title)
            and ("We're always working to improve your experience" not in title) and ("Responsible Disclosure" not in title) and ("Submitting letters to the editor" not in title)
            and ("Privacy" not in title) and ("Terms of" not in title) and ("Opens in new window" not in title) and ("Visit The" not in title) and ("Watch The" not in title)
            ):
                articles.append({
                'Title': title,
                'Link': link,
                })
        except Exception as e:
            print(f"Error parsing an article: {e}")

    return articles

def get_article_text_selenium(url, div):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        driver.get(url)

        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, div))
        )

        # Find the main article content
        article_content = driver.find_element(By.CLASS_NAME, div)
        paragraphs = article_content.find_elements(By.TAG_NAME, "p")
        article_text = " ".join([p.text for p in paragraphs])

        return article_text
    except Exception as e:
        print(f"Error fetching article with Selenium")
        return "Error fetching article"
    finally:
        driver.quit()

def main(name, url, div, bias):
    print("Scraping Politics section on " + str(name))
    articles = scrape_alternet_politics(url)

    for article in articles:
        print(f"Fetching article: {article['Title']}")
        article['Text'] = get_article_text_selenium(article['Link'], div)

    df = pd.DataFrame(articles)
    df = df.drop_duplicates()
    file_name = 'C:/developer/Kaggle/Dataset/'+ str(name) +'_'+ str(bias) +'.csv'
    if os.path.isfile(file_name):
        df.to_csv(file_name, index=False, mode='a')
        print(f"Saved {len(articles)} articles to " + str(file_name))
    else:
        df.to_csv(file_name, index=False, mode='w')
        print(f"Created file " + str(file_name) +" with "+ str(len(articles)) +" articles.")

pages = [
         ['cnbc', 'https://www.cnbc.com/politics/', 'group', 'center'],
         ['reason', 'https://reason.com/', 'entry-content', 'center'],
         ['StraightArrowNews', 'https://san.com/politics/', 'san-syndication-wrapper', 'center'],
         ['TheDispatch', 'https://thedispatch.com/category/policy/', 'tight-template', 'lean_right'],
         ['TheFreePress', 'https://www.thefp.com/s/us-politics', 'body', 'lean_right'],
         ['NewYorkPost', 'https://nypost.com/us-news/', 'single__content', 'lean_right'],
         ['BlazeMedia', 'https://www.theblaze.com/news/', 'body-description', 'right'],
         ['BreitBart', 'https://www.breitbart.com/politics/', 'entry-content', 'right'],
         ['TheFederalist', 'https://thefederalist.com/category/politics/', 'article-content', 'right'],
         ['IndependentJournalReview', 'https://ijr.com/tag/politics/', 'content-inner', 'right'],
         ['TheWashingtonFreeBeacon', 'https://freebeacon.com/politics/', 'article-content', 'right'],
         ['Alternet', "https://www.alternet.org/News-politics/", 'body-description', 'left'],
         ['APnews', 'https://apnews.com/politics', 'RichTextStoryBody', 'left'],
         ['TheDailyBeast', 'https://www.thedailybeast.com/category/politics/', 'b-article-body', 'left'],
         ['Huffpost', 'https://www.huffpost.com/news/politics', 'entry__content-list', 'left'],
         ['MotherJones', 'https://www.motherjones.com/politics/', 'entry-content', 'left'],
         ['TheNation', 'https://www.thenation.com/politics/', 'blocks-wrapper', 'left'],
         ['abcnews', 'https://abcnews.go.com/Politics', 'xvlfx', 'lean_left'],
         ['nbcnews', 'https://www.nbcnews.com/latest-stories/', 'article-body__content', 'lean_left'],
         ['npr', 'https://www.npr.org/sections/politics/', 'storytext', 'lean_left'],
         ['usatoday', 'https://www.usatoday.com/news/nation/', 'gnt_ar_b', 'lean_left']
         ]

for page in pages:
    name = page[0]
    url = page[1]
    div = page[2]
    bias = page[3]
    try:
        main(name, url, div, bias)
    except:
        print('Next one')
