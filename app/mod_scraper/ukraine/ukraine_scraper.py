# -*- coding: utf-8 -*-
from app.mod_scraper import scraper
from bs4 import BeautifulSoup
import ukraine_parser

parser = ukraine_parser.UkraineParser()

class UkraineScraper():
    def scrape_mp_bio_data(self):
        parser.mps_list()

    def scrape_organization(self):
        print "scraping Ukraine Votes data"