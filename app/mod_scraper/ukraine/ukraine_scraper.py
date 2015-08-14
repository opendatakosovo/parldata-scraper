from app.mod_scraper import scraper
from bs4 import BeautifulSoup

class UkraineScraper():
    def scrape_mp_bio_data(self):
        url = 'http://www.att.com/shop/wireless/devices/smartphones.html'
        scrape = scraper.Scraper()
        soup = scrape.download_html_file(url)
        try:
            print soup.find('div', {"id": "search_results"})
        except BaseException as e:
            print e.message
    def scrape_organization(self):
        print "scraping Ukraine Votes data"