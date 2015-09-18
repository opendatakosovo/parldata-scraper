# -*- coding: utf-8 -*-
from app.mod_scraper import scraper
import belarus_upperhouse_parser
from progressbar import ProgressBar, Percentage, ETA, Counter, Bar
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

    def scrape_chamber(self):
        print "\n\tScraping chambers from Belarus Upperhouse parliament...\n"
        chambers_list = []
        chambers = parser.chambers_list()
        widgets = ['        Progress: ', Percentage(), ' ', Bar(marker='#', left='[', right=']'),
                   ' ', ETA(), '             ']
        pbar = ProgressBar(widgets=widgets)
        for chamber in pbar(chambers):
            chamber_json = self.build_organization_doc("chamber", chambers[chamber]['name'], chamber,
                                                       chambers[chamber]['start_date'], chambers[chamber]['end_date'],
                                                       chambers[chamber]['url'], "", "")
            if chambers[chamber]["end_date"]:
                del chamber_json['dissolution_date']

            del chamber_json['contact_details']
            del chamber_json['parent_id']
            chambers_list.append(chamber_json)
        print "\n\tScraping completed! \n\tScraped " + str(len(chambers_list)) + " chambers"
        return chambers_list

    def scrape_committee(self):
        print "\n\tScraping committee groups from Belarus Upperhouse parliament...\n"
        committe_list = parser.committe_list()
        committees = []
        widgets = ['        Progress: ', Percentage(), ' ', Bar(marker='#', left='[', right=']'),
                                   ' ', ETA(), " - Processed: ", Counter(), ' items             ']
        pbar = ProgressBar(widgets=widgets)
        for committee in pbar(committe_list):
            committee_json = self.build_organization_doc("committe", committee['name'], committee['identifier'],
                                                         committee['start_date'], committee['end_date'],
                                                         committee['url'], "", committee['parent_id'])
            del committee_json['contact_details']
            if committee['start_date'] == "":
                del committee_json['founding_date']
            committees.append(committee_json)
        print "\n\tScraping completed! \n\tScraped " + str(len(committees)) + " chambers"
        return committees

    def build_organization_doc(self, classification, name, identifier, founding_date,
                               dissolution_date, url, email, parent_id):
        return {
            "classification": classification,
            "name": name,
            "identifiers": [{
                "identifier": identifier,
                "scheme": "house.by"
            }],
            "founding_date": founding_date,
            "contact_details": [{
                "label": "E-mail",
                "type": "email",
                "value": email
            }],
            "dissolution_date": dissolution_date,
            "sources": [{
                "note": "сайт",
                "url": url
            }],
            "parent_id": parent_id
        }

    def scrape_mp_bio_data(self):
        print "\n\tScraping people data from Belarus Upper House parliament..."
        print "\tPlease wait. This may take a few minutes...\n"
        mps_list = parser.mps_list()
        members = []
        for member in mps_list:
            member_json = self.build_json_doc(member['member_id'], member['name'], member['given_name'],
                                              member['family_name'], member['url'], member['image_url'],
                                              "", member['gender'], "")
            if 'phone_number' in member:
                phone_number = {
                    "type": "tel",
                    "label": "служебный телефон"
                }
                if member['phone_number']:
                    member_json['contact_details'] = []
                    phone_number['value'] = member['phone_number']
                    member_json['contact_details'].append(phone_number)
                else:
                    del member_json['contact_details']
            else:
                del member_json['contact_details']

            if 'fax' in member:
                if member['fax']:
                    fax_number = {
                        "type": "tel",
                        "label": "факс",
                        "value": member['fax']
                    }
                    if member['phone_number']:
                        member_json['contact_details'] = []
                        member_json['contact_details'].append(fax_number)
                    else:
                        member_json['contact_details'].append(fax_number)

            if 'birth_date' not in member:
                del member_json['birth_date']
            else:
                if member['birth_date']:
                    member_json['birth_date'] = member['birth_date']
                else:
                    del member_json['birth_date']
            members.append(member_json)
        print "\n\tScraping completed! \n\tScraped " + str(len(members)) + " members"
        return members

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