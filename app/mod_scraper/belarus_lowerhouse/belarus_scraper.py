# -*- coding: utf-8 -*-
from app.mod_scraper import scraper
import belarus_lowerhouse_parser

parser = belarus_lowerhouse_parser.BelarusLowerhouseParser()
scrape = scraper.Scraper()


class BelarusLowerhouseScraper():

    def scrape_mp_bio_data(self):
        mps_list = parser.mp()
        members = []
        for member in mps_list:
            member_json = self.build_json_doc(member['identifier'], member['name'], member['given_name'],
                                              member['family_name'], member['url'], member['image_url'],
                                              "", member['gender'], "")
            if 'email' in member:
                if member['email']:
                    member_json['contact_details'][0]['value'] = member['email']
                else:
                    del member_json['contact_details']
            else:
                del member_json['contact_details']

            if 'birth_date' in member:
                member_json['birth_date'] = member['birth_date']
            else:
                del member_json['birth_date']
            members.append(member_json)
        return members

    def build_json_doc(self, identifier, full_name, first_name, last_name, url, image_url, email, gender, birth_date):
        json_doc = {
            "identifiers": [{
                "identifier": identifier,
                "scheme": "house.by"
            }],
            "gender": gender,
            "birth_date": birth_date,
            "name": full_name,
            "given_name": first_name,
            "family_name": last_name,
            "contact_details": [{
                "type": "email",
                "label": "E-mail",
                "value": email
            }],
            "sources": [{
                "note": "сайт",
                "url": url
            }],
            "image": image_url,
            "sort_name": last_name + ", " + first_name
        }
        return json_doc