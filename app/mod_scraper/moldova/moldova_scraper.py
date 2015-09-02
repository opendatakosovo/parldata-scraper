# -*- coding: utf-8 -*-
from pymongo import MongoClient
from app.mod_scraper import scraper
import re

client = MongoClient()
db = client.parlament_md
scrape = scraper.Scraper()


class MoldovaScraper():

    # def sk_to_utc(self, dt_str):
    #     """Converts Slovak date(-time) string into ISO format in UTC time."""
    #     match = re.search(SK_MONTHS_REGEX, dt_str, re.IGNORECASE)
    #     if match:
    #         month = match.group(0)
    #         dt_str = dt_str.replace(month, '%s.' % SK_MONTHS[month[:3].lower()])
    #     dt = dateutil.parser.parse(dt_str, dayfirst=True)
    #     if ':' in dt_str:
    #         return vpapi.local_to_utc(dt, to_string=True)
    #     else:
    #         return dt.strftime('%Y-%m-%d')

    def guess_gender(self, first_name):
        if first_name[-1:] == "a":
            return "female"
        else:
            return "male"

    def build_json_doc(self, identifier, full_name, first_name, last_name, url, image_url, gender):
        json_doc = {
            "identifiers": [{
                "identifier": identifier,
                "scheme": "parlament.md"
            }],
            "gender": gender,
            "name": full_name,
            "given_name": first_name,
            "family_name": last_name,
            "sources": [{
                "note": "pagină web",
                "url": url
            }],
            "image": image_url,
            "sort_name": last_name + ", " + first_name
        }
        return json_doc

    def mps_list(self):
        deputy_list = []
        deputy_list_url = "http://www.parlament.md/StructuraParlamentului/Deputies/tabid/87/language/ro-RO/Default.aspx"
        soup = scrape.download_html_file(deputy_list_url)
        each = soup.find("div", {"class": "allTitle"}).find("table", {"cellspacing": "4"}).findAll('tr')

        for tr in each:
            name = tr.find("td").find("img").get("alt")
            link = tr.find("td", {"valign": "top"}).find("a").get("href")
            # fraction_link = tr.find("td", {"valign": "top"}).find("a", {"class": "FractionLink"}).get("href")
            # fraction = tr.find("td", {"valign": "top"}).find("a", {"class": "FractionLink"}).next
            image_url = "http://www.parlament.md" + tr.find("td").find("img").get("src")
            names = name.split(' ')
            first_name = names[1]
            last_name = names[0]
            sort_name = names[0] + ", " + names[1]
            name_ordered = first_name + " " + last_name
            gender = self.guess_gender(first_name)
            index_start = link.index('Id/')
            index_end = link.index('/la')
            member_id = link[index_start + 3:index_end]
            soup_deputy = scrape.download_html_file(link)
            membership = soup_deputy.find("span", {"id": "dnn_ctr476_ViewDeputat_lblPosition"})
            deputy_json = {
                "membership": membership.get_text(),
                "identifier": member_id,
                "name": name_ordered,
                "sort_name": sort_name,
                "gender": gender,
                "url": link,
                "image_url": image_url,
                "given_name": first_name,
                "family_name": last_name,
            }
            deputy_list.append(deputy_json)
        return deputy_list

    def scrape_mp_bio_data(self):
        mps_list = self.mps_list()
        members = []
        print "\n\tScraping people data from Moldova's parliament..."
        print "\tThis may take a few minutes..."
        for member in mps_list:
            # identifier, full_name, first_name, last_name, url, image_url, gender
            member_json = self.build_json_doc(member['identifier'], member['name'], member['given_name'],
                                              member['family_name'], member['url'], member['image_url'],
                                              member['gender'])
            members.append(member_json)
        print "\n\tScraping completed! \n\tScraped " + str(len(members)) + " members"
        return members
        # print "Scraped %s members" % str(counter)
