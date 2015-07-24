from pymongo import MongoClient
import mechanize
from bs4 import BeautifulSoup
from app.mod_scraper import georgia_scraper

client = MongoClient()
db = client.ge


def scrape():
    # execute MP's bio data.
    scraper = georgia_scraper.GeorgiaScraper()
    scraper.scrape_mp_bio_data()

    # Download bio images and render thumbnails.
    #download_bio_images()


# Funtction which will scrape MP's bio data

scrape()