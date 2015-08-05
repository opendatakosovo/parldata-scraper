# -*- coding: utf-8 -*-
from pymongo import MongoClient
import scraper
from urllib2 import urlopen
import os
import vpapi
from datetime import date
import json
import pprint


client = MongoClient()
db = client.ge


class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return json.JSONEncoder.default(self, o)


class GeorgiaScraper():
    def get_member_id(self):
        url = "http://votes.parliament.ge/ka/api/v1/members"
        result = urlopen(url).read()
        json_result = json.loads(result)
        mp_list = {}
        for item in json_result:
            full_name = item['name'].split(" ")
            first_name = full_name[1]
            last_name = full_name[0]
            mp = first_name + " " + last_name
            member_id = item['id']
            mp_list[mp] = str(member_id)
        return mp_list

    def scrape_mp_bio_data(self, people, votes, base_dir):
        global effective_date
        effective_date = date.today().isoformat()
        print effective_date
        '''
        Scraping members data of the Georgian Parliament.
        '''
        if people == "yes":
            with open(os.path.join(base_dir, 'access.json')) as f:
                creds = json.load(f)
            try:
                vpapi.parliament('ge/parliament')
                vpapi.timezone('Etc/GMT+4')
                vpapi.authorize(creds['georgia']['api_user'], creds['georgia']['password'])
                mp_list = self.get_member_id()
                db.mps_list.remove({})
                print "\nScraping members (people) of Georgia's parliament..."
                # resp = vpapi.delete('people')
                # print resp
                deputy_list_url = "http://www.parliament.ge/ge/parlamentarebi/deputatebis-sia"
                scrape = scraper.Scraper()

                soup = scrape.download_html_file(deputy_list_url)
                counter = 0
                mps = []
                #iterate through each deputy in the deputy list.
                for each in soup.find("div", {"class": "mps_list"}): #iterate over loop [above sections]
                    if each.find('a'):
                        continue
                    else:
                        counter += 1
                        full_name = each.find('h4').next.encode('utf-8')
                        first_last_name = full_name.split(' ')

                        first_name = first_last_name[0]
                        last_name = first_last_name[1]

                        url = each.get('href')
                        image_url = each.find('img').get('src')
                        person_id_from_url = url.index('p/')
                        person_id = url[person_id_from_url + 2:]

                        soup_deputy = scrape.download_html_file(url)

                        phone = ""
                        date_of_birth = ""

                        #iterate through each element of deputy information in the page and store data to the database.
                        for div_elements in soup_deputy.findAll("div", {"class": "info_group"}):
                            for li_element in div_elements.findAll('ul'):
                                element = li_element.get_text(strip=True)
                                encoded_element = element.encode("utf-8")
                                if "ტელეფონი" in encoded_element:
                                    phone = encoded_element.replace('ტელეფონი', '')
                                    if phone == "":
                                        phone = ""
                                elif "დაბადების თარიღი" in encoded_element:
                                    date_of_birth = encoded_element.replace('დაბადების თარიღი', '')
                                # elif "საარჩევნო ფორმა" in encoded_element:
                                #     election_form = encoded_element.replace('საარჩევნო ფორმა', '')
                                # elif "საარჩევნო ბლოკი" in encoded_element:
                                #     election_block = encoded_element.replace('საარჩევნო ბლოკი', '')

                        gender = self.guess_gender(first_name)
                        if full_name.decode('utf-8') in mp_list:
                            member_id = mp_list[full_name.decode('utf-8')]
                        else:
                            member_id = person_id
                        identifier = {
                            "identifier": member_id.encode('utf-8'),
                            "scheme": "parliament.ge"
                        }
                        json_doc = self.build_json_doc(identifier, full_name, first_name, last_name, url,
                                                       image_url, phone, date_of_birth, gender)

                        if phone == "":
                            del json_doc['contact_details']
                        pp = pprint.PrettyPrinter()
                        pp.pprint(json_doc)

                        existing = vpapi.getfirst('people', where={'identifiers': {'$elemMatch': identifier}})
                        print existing
                        if not existing:
                            resp = vpapi.post('people', json_doc)
                        else:
                            # update by PUT is preferred over PATCH to correctly remove properties that no longer exist now
                            resp = vpapi.put('people', existing['id'], json_doc, effective_date=effective_date)
                        print "---------------------------------------------------------------------------------"

                        db.mps_list.insert(json_doc)

                print "\n\tScraping completed! \n\tScraped " + str(counter) + " deputies"
            except Exception as e:
                print "\n" + str(e)


    def build_json_doc(self, identifier, full_name, first_name, last_name, url, image_url,
                       phone_number, date_of_birth, gender):
        json_doc = {
            "identifiers": [identifier],
            "gender": gender,
            "name": full_name,
            "given_name": first_name,
            "family_name": last_name,
            "sources": [{
                "note": "ვებგვერდი",
                "url": url
            }],
            "image": image_url,
            "contact_details": [{
                "label": "ტელეფონი",
                "type": "tel",
                "value": phone_number.replace(" ", '')
            }],
            "sort_name": last_name + ", " + first_name,
            "birth_date": date_of_birth,
        }
        return json_doc

    def guess_gender(self, name):
        females = ["მანანა", "ეკა", "თინათინ", "ხათუნა", "ნინო", "მარიკა", "ჩიორა", "თამარ", "გუგული",
                   "ანი", "ირმა", "მარიამ", "ნანა", "ელისო", "დარეჯან", "ფატი", "ეკატერინე"]
        if name in females:
            return "female"
        else:
            return "male"

    '''
    sample_identifier = {
        'identifier': '046454286',
        'scheme': 'SIN'
    }
    sample_link = {
        'url': 'http://en.wikipedia.org/wiki/John_Q._Public',
        'note': 'Wikipedia page'
    }
    sample_image_url = 'http://www.google.com/images/srpr/logo11w.png'
    sample_person = {
        'name': 'Mr. John Q. Public, Esq.',
        'identifiers': [
            sample_identifier
        ],
        'email': 'jqpublic@xyz.example.com',
        'gender': 'male',
        'birth_date': '1920-01',
        'death_date': '2010-01-01',
        'image': sample_image_url,
        'summary': 'A hypothetical member of society deemed a "common man"',
        'biography': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. ...',
        'national_identity': 'Scottish',
        'contact_details': [
            {
                'label': 'Mobile number',
                'type': 'tel',
                'value': '+1-555-555-0100',
                'note': 'Free evenings and weekends'
            }
        ],
        'links': [
            sample_link
        ]
    }
    person_with_id = {
        'id': 'bilbo-baggins',
        'name': 'Bilbo Baggins',
    }
    sample_organization = {
        "name": "ABC, Inc.",
        "founding_date": "1950-01-01",
        "dissolution_date": "2000-01-01",
    }
    sample_membership = {
        "label": "Kitchen assistant at ABC, Inc.",
        "role": "Kitchen assistant",
        "start_date": "1970-01",
        "end_date": "1971-12-31",
    }
    '''