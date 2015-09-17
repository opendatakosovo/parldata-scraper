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

    def ordered(self):
        json1 = {
            "1": "Александр",
            "2": "Сергей"
        }

        json2 = {
            "2": "Сергей",
            "1": "Александр"
        }

        if json1 == json2:
            print "EQUALS"
        else:
            print "NOT EQUALS"

    def scrape_mp_bio_data(self):
        print "\n\tScraping people data from Belarus Upper House parliament..."
        print "\tPlease wait. This may take a few minutes..."
        mps_list = parser.mps_list()
        members = []
        for member in mps_list:
            member_json = self.build_json_doc(member['member_id'], member['name'], member['given_name'],
                                              member['family_name'], member['url'], member['image_url'],
                                              member['phone_number'], member['gender'], member['birth_date'])
            if member['phone_number'] == "":
                del member_json['contact_details']
            if member['fax'] != "":
                fax_number = {
                    "type": "fax",
                    "label": "факс",
                    "value": member['fax']
                }
                if member['phone_number'] == "":
                    member_json['contact_details'] = []
                    member_json['contact_details'].append(fax_number)
                else:
                    member_json['contact_details'].append(fax_number)
            if member['birth_date'] != "":
                del member_json['birth_date']
            members.append(member_json)
        print "\n\tScraping completed! \n\tScraped " + str(len(members)) + " members"

    def build_json_doc(self, identifier, full_name, first_name, last_name, url, image_url, phone, gender, birth_date):
        json_doc = {
            "identifiers": [{
                "identifier": identifier,
                "scheme": "sovrep.by"
            }],
            "gender": gender,
            "birth_date": birth_date,
            "name": full_name,
            "given_name": first_name,
            "family_name": last_name,
            "contact_details": [{
                "type": "tel",
                "label": "служебный телефон",
                "value": phone
            }],
            "sources": [{
                "note": "сайт",
                "url": url
            }],
            "image": image_url,
            "sort_name": last_name + ", " + first_name
        }
        return json_doc

    def guess_gender(self, name):
        females = ["Наталля"]
        if name[-1] == "а".decode('utf-8') or name.encode('utf-8') in females:
            return "female"
        else:
            return "male"