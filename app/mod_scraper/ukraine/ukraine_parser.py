# -*- coding: utf-8 -*-
from app.mod_scraper import scraper
import sys
from bs4 import BeautifulSoup
import requests
import re
import vpapi
from progressbar import ProgressBar, Percentage, ETA, Counter, Bar

scrape = scraper.Scraper()


class UkraineParser():
    def download_html_file(self, url):
        response = requests.get(url)
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup

    def chambers(self):
        chambers = {
            "9": {
                "url": "http://w1.c1.rada.gov.ua/pls/site2/p_deputat_list?skl=9",
                "name": "VIII скликання (2014-)",
                "start_date": "2014",
                "end_date": ""
            }
        }
        url = "http://w1.c1.rada.gov.ua/pls/site2/p_deputat_list"
        soup = self.download_html_file(url)
        for each_li in soup.find("div", {"class": "col-half col-last"}).find('ul').findAll("li"):
            name = each_li.find('a').get_text()
            url = each_li.find('a').get("href")
            if ".htm" in url:
                identifier = url.replace(".htm", "")[-1:]
            else:
                identifier = url[-1:]
            print identifier

            index_start = name.index("(") + 1
            index_end = name.index(")")
            years = name[index_start:index_end].split("-")
            start_date = years[0]
            end_date = years[1]
            print name
            print "----------------------------"
            chambers[identifier] = {
                "url": url,
                "name": name,
                "start_date": start_date,
                "end_date": end_date
            }
        return chambers

    def mps_list(self):
        chambers = self.chambers()
        guess_gender = {
            "1": "male",
            "2": "female"
        }
        for term in list(reversed(sorted(chambers))):
            print term
            if int(term) > 4:
                for i in range(1, 3):
                    url = "http://w1.c1.rada.gov.ua/pls/site2/fetch_mps?skl_id=%s&gender=%s" % (term, str(i))
                    print url
                    soup = self.download_html_file(url)
                    for each_li in soup.find("ul", {"class": "search-filter-results search-filter-results-thumbnails"}).findAll("li"):
                        print each_li.find("p", {"class": "thumbnail"}).find("img").get('src')
                        print each_li.find("p", {"class": "title"}).find("a").get('href')
                        print each_li.find("p", {"class": "title"}).find("a").get_text()
                        print "-----------------------------------------------"
            else:
                soup = self.download_html_file(chambers[term]['url'])