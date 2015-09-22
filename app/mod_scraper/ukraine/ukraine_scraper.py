# -*- coding: utf-8 -*-
from app.mod_scraper import scraper
from bs4 import BeautifulSoup
from progressbar import ProgressBar, Percentage, ETA, Counter, Bar
import ukraine_parser

parser = ukraine_parser.UkraineParser()

class UkraineScraper():
    def scrape_mp_bio_data(self):
        print "\n\tScraping people data from Ukraine's House parliament..."
        print "\tPlease wait. This may take a few minutes...\n"
        mp_list = parser.members_list()
        print "\n\tScraping completed! \n\tScraped " + str(len(mp_list)) + " members"

    def scrape_organization(self):
        parser.chamber_membership()