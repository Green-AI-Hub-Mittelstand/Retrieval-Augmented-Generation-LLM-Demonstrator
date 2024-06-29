import requests  
import traceback 
from bs4 import BeautifulSoup  
from urllib.parse import urljoin 
from models import session, Mitteilung
from datetime import datetime
from sqlalchemy.exc import IntegrityError



class Crawl():

    def __init__(self, url_1):
        # Initialize with the starting URL
        self.start_url = url_1
        # Stack to keep track of URLs to crawl
        self.stack = [url_1]
        # Set to keep track of visited URLs
        self.visited = set()

    def crawl(self):
        # Main crawling method
        while len(self.stack) != 0:
        # Pop a URL from the stack
            url = self.stack.pop()

            # Check if the URL has not been visited
            if url not in self.visited:
                #print(url)
                #print(url)

                # Mark the URL as visited
                self.visited.add(url)

                # Make a request to the URL
                content = requests.get(url, timeout=10)

                # Check if the request was successful (status code 200)
                if content.status_code == 200:
                    # Parse the HTML content
                    html_page = content.text
                    soup = BeautifulSoup(html_page, 'html.parser')
                    if url.startswith('https://www.bmuv.de/PM'):
                        try:
                            text = BeautifulSoup(content.text, "html.parser")
                            date_element = soup.find('span', class_='c-hero__rubric')
                            if date_element:
                                # Extrahieren Sie den Textinhalt des Elements, der das Datum enthält
                                date = datetime.strptime(date_element.text.strip(), '%d.%m.%Y')

                            content = soup.find('div', itemprop="description", class_="c-ce-formated")
                            mitteilung = Mitteilung(title=text.title.string, content = content.get_text(), date = date)
                            session.add(mitteilung)
                            session.commit() 
                            print(text.title.string,":::", date)
        
                        except IntegrityError:
                            print("Ignoring duplicate title: " + text.title.string)
                            session.rollback()

                            #pass
                    if url.startswith('https://www.bmuv.de/presse/pressemitteilungen'):
                        # Extract links from the page and add to the stack
                        for l in soup.find_all("a"):
                            href = l.get('href')

                            if href:
                                # Check if it's an absolute or relative link
                                if href.startswith('http') or href.startswith('https'):
                                    absolute_link = href
                                else:
                                    absolute_link = urljoin(url, href)
                                #print(absolute_link)

                                # Check if the link is within the specified domain
                                if absolute_link.startswith('https://www.bmuv.de/PM') or absolute_link.startswith('https://www.bmuv.de/presse/pressemitteilungen'):
                                    self.stack.append(absolute_link)

print("start")        
crawler = Crawl('https://www.bmuv.de/presse/pressemitteilungen')
crawler.crawl()
