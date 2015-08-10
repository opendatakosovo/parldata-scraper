# -*- coding: utf-8 -*-
from pymongo import MongoClient
import scraper
from urllib2 import urlopen
import os
import vpapi
from datetime import date
import json
import re


client = MongoClient()
db = client.ge


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

    def mps_list(self):
        mps_list = []
        deputy_list_url = "http://www.parliament.ge/ge/parlamentarebi/deputatebis-sia"
        scrape = scraper.Scraper()
        soup = scrape.download_html_file(deputy_list_url)
        mp_list = self.get_member_id()
        for each in soup.find("div", {"class": "mps_list"}): #iterate over loop [above sections]
            if each.find('a'):
                continue
            else:
                full_name = each.find('h4').next.encode('utf-8')
                first_last_name = full_name.split(' ')

                first_name = first_last_name[0]
                last_name = first_last_name[1]
                url = each.get('href')
                image_url = each.find('img').get('src')
                person_id_from_url = url.index('p/')
                gender = self.guess_gender(first_name)
                person_id = url[person_id_from_url + 2:]

                if full_name.decode('utf-8') in mp_list:
                    member_id = mp_list[full_name.decode('utf-8')]
                else:
                    member_id = person_id

                identifiers = {
                    "identifier": member_id.encode('utf-8'),
                    "scheme": "parliament.ge"
                }

                mp_json = {
                    "name": full_name,
                    "identifiers": identifiers,
                    "given_name": first_name,
                    "family_name": last_name,
                    "gender": gender,
                    "image": image_url,
                    "source_url": url
                }
                mps_list.append(mp_json)
        return mps_list

    def scrape_mp_bio_data(self):
        '''
        Scraping members data of the Georgian Parliament.
        '''
        mps_list = self.mps_list()
        db.mps_list.remove({})
        print "\nScraping members data of the Georgian Parliament\nThis may take few moments, Please wait..."
        scrape = scraper.Scraper()
        counter = 0
        deputies = []
        #iterate through each deputy in the deputies list.
        for json in mps_list: #iterate over loop [above sections]8
            counter += 1
            soup_deputy = scrape.download_html_file(json['source_url'])
            phone = ""
            date_of_birth = ""
            #iterate through each element of deputy information in the page and store data to the database.
            for div_elements in soup_deputy.findAll("div", {"class": "info_group"}):
                for li_element in div_elements.findAll('ul'):
                    element = li_element.get_text(strip=True)
                    encoded_element = element.encode("utf-8")
                    if "ტელეფონი" in encoded_element:
                        phone = encoded_element.replace('ტელეფონი', '')
                    elif "დაბადების თარიღი" in encoded_element:
                        date_of_birth = encoded_element.replace('დაბადების თარიღი', '')

            json_doc = self.build_json_doc(json['identifiers'], json['name'], json['given_name'], json['family_name'],
                                           json['source_url'], json['image'], phone, date_of_birth, json['gender'])
            print json_doc
            print "\n--------------------------------------"
            deputies.append(json_doc)

            if phone == "":
                del json_doc['contact_details']

        print "\n\tScraping completed! \n\tScraped " + str(counter) + " deputies"
        return deputies

    def parliamentary_grous_list(self):
        parties_list_url = "http://www.parliament.ge/ge/saparlamento-saqmianoba/fraqciebi-6"
        scrape = scraper.Scraper()

        soup = scrape.download_html_file(parties_list_url)
        parties = []
        for div_elements in soup.find("div", {"class": "submenu_list"}):
            if div_elements.find("a"):
                continue
            else:
                party_json = {
                    "name": div_elements.get_text(),
                    "url": div_elements.get('href')
                }
                parties.append(party_json)
        return parties


    def scrape_organization(self):
        '''
        Scapres organisation data from the official web page of Georgian parliament
        '''
        parties_list = []
        scrape = scraper.Scraper()
        parties = self.parliamentary_grous_list()
        for party in parties:
            if "qartuli-ocneba-tavisufali-demokratebi" not in party['url']:
                soup = scrape.download_html_file(party['url'])
                for each_a in soup.find("div", {"class": "submenu_list"}):
                    if each_a.find('a'):
                        continue
                    else:
                        name = each_a.get_text()
                        faction_url = each_a.get('href')
                        parliamentary_group = self.build_parliamentary_group_doc(name, faction_url)
                        parties_list.append(parliamentary_group)
                        # soup_faction = scrape.download_html_file(faction_url)
                        # div = soup_faction.find("div", {"class": "submenu_list"})
                        # if div.find('a').get_text().encode('utf-8') == "ფრაქციის წევრები":
                        #     url_members = div.find('a').get("href")
                        #     print url_members
                        #     soup_members = scrape.download_html_file(url_members)
                        #     for each_attr in soup_members.find("div", {"class": "mps_list"}):
                        #         if each_attr.find('a'):
                        #             continue
                        #         else:
                        #             full_name = each_attr.find('h4').next.encode('utf-8')
                        #             print full_name
            else:
                parliamentary_group = self.build_parliamentary_group_doc(party['name'], party['url'])
                parties_list.append(parliamentary_group)
                # soup_faction = scrape.download_html_file(party['url'])
                # div = soup_faction.find("div", {"class": "submenu_list"})
                # if div.find('a').get_text().encode('utf-8') == "ფრაქციის წევრები":
                #     url_members = div.find('a').get("href")
                #     print url_members
                #     soup_members = scrape.download_html_file(url_members)
                #     for each_a in soup_members.find("div", {"class": "mps_list"}):
                #         if each_a.find('a'):
                #             continue
                #         else:
                #             full_name = each_a.find('h4').next.encode('utf-8')
                #             print full_name

        print "\n\tScraping of Faction groups complete!"
        return parties_list

    def scrape_chamber(self):
        chambers_list = []
        chambers_list.append({
            "classification": "chamber",
            "name": "საქართველოს პარლამენტი - 2012-2016 წწ.",
            "identifiers": [{
                    "identifier": "2012",
                    "scheme": "parliament.ge"
                }],
            "founding_date": "2012",
            "dissolution_date": "2016-10",
        })
        chamber_list_html = "http://www.parliament.ge/ge/parlamentarebi/saqartvelos-wina-mowvevis-parlamentebi-1317"
        scrape = scraper.Scraper()

        soup = scrape.download_html_file(chamber_list_html)

        for each_a in soup.find("div", {"class": "submenu_list"}):
            if each_a.find('a'):
                continue
            else:
                name = each_a.get_text()
                years = re.findall(r'\d+', name)
                source_url = each_a.get('href')
                founding_year = years[0]
                dissolution_date = years[1]
                identifier = source_url[-4:]
                if source_url[-2:] == "ww":
                    identifier = "1990"
                identifiers = {
                    "identifier": identifier,
                    "scheme": "parliament.ge"
                }

                chamber_json = self.build_chamber_doc(name, identifiers, founding_year, dissolution_date, source_url)
                chambers_list.append(chamber_json)
        return chambers_list


    def build_parliamentary_group_doc(self, name, url):
        return {
            "classification": "parliamentary group",
            "name": name,
            "sources": [{
                "note": "ვებგვერდი",
                "url": url
            }]
        }

    def build_chamber_doc(self, name, identifiers, founding_date, dissolution_date, url):
        return {
            "classification": "chamber",
            "name": name,
            "identifiers": [identifiers],
            "founding_date": founding_date,
            "dissolution_date": dissolution_date,
            "sources": [{
                "note": "ვებგვერდი",
                "url": url
            }]
        }

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