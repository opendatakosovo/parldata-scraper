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
    def download_html_file(self, url, encoding_type=None):
        response = requests.get(url)
        if encoding_type:
            response.encoding = "utf-8"
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

    def build_ordered_name(self, name):
        encoded_name = name.encode('utf-8')
        names = encoded_name.split(" ")
        first_name = names[1]
        middle_name = names[2]
        last_name = names[0]
        return first_name + " " + middle_name + " " + last_name

    def first_chamber_mps_list(self):
        first_chamber_mps = []
        url = "http://static.rada.gov.ua/zakon/new/NEWSAIT/DEPUTAT1/spisok1.htm"
        soup = self.download_html_file(url, "utf-8")
        for each_div in soup.findAll('div', {"class": "topTitle"})[1:]:
            if each_div.find("table"):
                all_tr_elements = each_div.find("table").findAll('tr')
                for each_tr in all_tr_elements[1:len(all_tr_elements)-1]:
                    all_td_elements = each_tr.findAll('td')
                    name = all_td_elements[0].find("p").find('a').get_text().replace("\n", "").replace("                   ", " ")
                    encoded_name = name.encode('utf-8')
                    names = encoded_name.split(" ")
                    first_name = names[1]
                    middle_name = names[2]
                    last_name = names[0]
                    name_ordered = first_name + " " + middle_name + " " + last_name
                    print name_ordered
                    url = "http://static.rada.gov.ua/zakon/new/NEWSAIT/DEPUTAT1/" + \
                          all_td_elements[0].find("p").find('a').get("href")
                    print "----------------------------------------------"
        return first_chamber_mps

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
                        print guess_gender[str(i)]
                        print "-----------------------------------------------"
            else:
                if str(term) != "1":
                    soup = self.download_html_file(chambers[term]['url'])
                else:
                    first_chambers_mps = self.first_chamber_mps_list()