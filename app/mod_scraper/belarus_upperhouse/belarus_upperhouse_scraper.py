# -*- coding: utf-8 -*-
from app.mod_scraper import scraper
import belarus_upperhouse_parser
import vpapi

parser = belarus_upperhouse_parser.BelarusUpperhouseParser()
scrape = scraper.Scraper()

class BelarusUpperhouseScraper():
    months_correction = {
        "студзеня": "01",
        "лютага": "02",
        "сакавіка": "03",
        "Красавік": "04",
        "красавіка": "04",
        "мая": "05",
        "чэрвеня": "06",
        "ліпеня": "07",
        "жніўня": "08",
        "верасня": "09",
        "кастрычніка": "10",
        "лістапада": "11",
        "снежня": "12"
    }

    def chambers(self):
        print "\n\tScraping people data from Belarus Upper House parliament..."
        print "\tPlease wait. This may take a few minutes..."
        mps_list = parser.mps_list()
        members = []
        for member in mps_list:
            members.append(member)
        print "\n\tScraping completed! \n\tScraped " + str(len(members)) + " members"

    def guess_gender(self, name):
        females = ["Наталля"]
        if name[-1] == "а".decode('utf-8') or name.encode('utf-8') in females:
            return "female"
        else:
            return "male"