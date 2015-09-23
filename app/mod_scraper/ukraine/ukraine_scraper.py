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
        members = []
        for member in mp_list:
            member_json = self.build_json_doc(member['member_id'], member['name'], member['given_name'],
                                              member['family_name'], member['url'], member['image_url'],
                                              member['email'], member['gender'], member['birth_date'])

            if not member['image_url']:
                del member_json['image']

            if not member['email']:
                del member_json['contact_details']

            if 'birth_date' not in member:
                del member_json['birth_date']

            if not member['birth_date']:
                del member_json['birth_date']

            members.append(member_json)
        print "\n\tScraping completed! \n\tScraped " + str(len(members)) + " members"
        return members

    def build_json_doc(self, identifier, full_name, first_name, last_name, url, image_url, email, gender, birth_date):
        json_doc = {
            "identifiers": [{
                "identifier": identifier,
                "scheme": "rada.ua"
            }],
            "gender": gender,
            "birth_date": birth_date,
            "name": full_name,
            "given_name": first_name,
            "family_name": last_name,
            "contact_details": [{
                "type": "email",
                "label": "Ел. пошта",
                "value": email
            }],
            "sources": [{
                "note": "веб-сторінка",
                "url": url
            }],
            "image": image_url,
            "sort_name": last_name + ", " + first_name
        }
        return json_doc

    def scrape_organization(self):
        parser.chamber_membership()