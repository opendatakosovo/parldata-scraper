# -*- coding: utf-8 -*-
from app.mod_scraper import scraper
import belarus_lowerhouse_parser

parser = belarus_lowerhouse_parser.BelarusLowerhouseParser()
scrape = scraper.Scraper()

class BelarusLowerhouseScraper():
    def scrape_mp_bio_data(self):
        mps_list = parser.mp()
        for member in mps_list:
            member_json = self.build_json_doc(member['identifier'], member['name'], member['given_name'],
                                              member['family_name'], member['url'], member['image_url'])
            # if member['email'] != "":

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