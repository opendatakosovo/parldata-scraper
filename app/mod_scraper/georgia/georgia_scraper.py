# -*- coding: utf-8 -*-
from pymongo import MongoClient
from app.mod_scraper import scraper
from urllib2 import urlopen
import vpapi
import json
import re


client = MongoClient()
db = client.ge
scrape = scraper.Scraper()

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
                membership = each.find('p').next.encode('utf-8')
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
                    "source_url": url,
                    "membership": membership
                }
                mps_list.append(mp_json)
        return mps_list

    def membership_correction(self):
        return {
            "პარლამენტის თავმჯდომარე": "chairman",
            "პარლამენტის თავმჯდომარის მოადგილე": "vice-chairman",
            "პარლამენტის წევრი": "member",
            "პარლამენტის თავმჯდომარის პირველი მოადგილე": 'first-vice-chairwomen',
            "კომიტეტის თავმჯდომარე": "chairman",
            "კომიტეტის თავმჯდომარის პირველი მოადგილე": 'first-vice-chairman',
            "კომიტეტის თავმჯდომარის მოადგილე": "vice-chairman",
            "კომიტეტის წევრი": "member",
            "ფრაქციის თავმჯდომარე": "chairman",
            "ფრაქციის თავმჯდომარის მოადგილე": "vice-chairman",
            "ფრაქციის მდივანი": "secretary",
            "ფრაქციის წევრი": "member"
        }

    def scrape_mp_bio_data(self):
        '''
        Scraping members data of the Georgian Parliament.
        '''
        mps_list = self.mps_list()
        db.mps_list.remove({})
        scrape = scraper.Scraper()
        deputies = []
        print "\n\tScraping people data from Georgia's parliament..."
        #iterate through each deputy in the deputies list.
        for json in mps_list: #iterate over loop [above sections]8
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
            deputies.append(json_doc)

            if phone == "":
                del json_doc['contact_details']

        print "\n\tScraping completed! \n\tScraped " + str(len(deputies)) + " members"
        return deputies

    def get_id(self, collection, identifier, type=None):
        if collection != "organizations":
            existing = vpapi.getfirst(collection, where={'identifiers': {'$elemMatch': {'identifier': identifier}}})
        else:
            if type:
                existing = vpapi.getfirst(collection, where={'identifiers': {'$elemMatch': {'identifier': identifier}}})
            else:
                existing = vpapi.getfirst(collection, where={'name': identifier})

        if existing:
            p_id = existing['id']
        else:
            p_id = "Not found"
        return p_id

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

    def parliamentary_committes_list(self):
        parties_list_url = "http://www.parliament.ge/ge/saparlamento-saqmianoba/komitetebi"
        scrape = scraper.Scraper()

        soup = scrape.download_html_file(parties_list_url)
        committes = []
        for div_elements in soup.find("div", {"class": "submenu_list"}):
            if div_elements.find("a"):
                continue
            else:
                committe_json = {
                    "name": div_elements.get_text(),
                    "url": div_elements.get('href')
                }
                committes.append(committe_json)
        return committes

    def scrape_parliamentary_groups(self):
        '''
        Scapres organisation data from the official web page of Georgian parliament
        '''
        parties_list = []
        scrape = scraper.Scraper()
        parties = self.parliamentary_grous_list()
        print "\n\tScraping parliamentary groups data from Georgia's parliament..."
        for party in parties:
            if "qartuli-ocneba-tavisufali-demokratebi" not in party['url']:
                soup = scrape.download_html_file(party['url'])
                for each_a in soup.find("div", {"class": "submenu_list"}):
                    if each_a.find('a'):
                        continue
                    else:
                        name = each_a.get_text()
                        faction_url = each_a.get('href')
                        parliamentary_group = self.build_organizations_doc("parliamentary group", name, faction_url)
                        parties_list.append(parliamentary_group)
            else:
                parliamentary_group = self.build_organizations_doc("parliamentary group", party['name'], party['url'])
                parties_list.append(parliamentary_group)

        print "\n\tScraping completed! \n\tScraped " + str(len(parties_list)) + " parliamentary groups"
        return parties_list

    def scrape_committe(self):
        scrape = scraper.Scraper()
        committees_list = []
        committees = self.parliamentary_committes_list()
        print "\n\tScraping committees data from Georgia's parliament..."
        for committee in committees:
            # if committee['url'] != "http://www.parliament.ge/ge/saparlamento-saqmianoba/komitetebi/diasporisa-da-kavkasiis-sakitxta-komiteti":
            soup_committees = scrape.download_html_file(committee['url'])
            contact = soup_committees.find('a', text="დაგვიკავშირდით")
            if contact:
                soup_committee_contact = scrape.download_html_file(contact.get('href'))
                if soup_committee_contact('div', {'class': 'txt'}):
                    for each_p in soup_committee_contact('div', {'class': 'txt'}):
                        if each_p.find('a'):
                            email = each_p.find('a').get_text()
                            committee_json = self.build_organizations_doc("committe", committee['name'], committee['url'])
                            committee_json['contact_details'] = [{
                                'type': "email",
                                'value': email
                            }]
                            committees_list.append(committee_json)

                        else:
                            committee_json = self.build_organizations_doc("committe", committee['name'], committee['url'])
                            committees_list.append(committee_json)
                else:
                    committee_json = self.build_organizations_doc("committe", committee['name'], committee['url'])
                    committees_list.append(committee_json)
            else:
                committee_json = self.build_organizations_doc("committe", committee['name'], committee['url'])
                committees_list.append(committee_json)

        print "\n\tScraping completed! \n\tScraped " + str(len(committees_list)) + " committees"
        return committees_list

    def scrape_membership(self):
        scrape = scraper.Scraper()
        membership_array = []
        mp_list = self.get_member_id()
        members_list = self.mps_list()
        parties = self.parliamentary_grous_list()
        committees = self.parliamentary_committes_list()
        data_collections = {
            "chambers": members_list,
            "parties": parties,
            "committes": committees
        }
        membership_groups = self.membership_correction()
        print "\n\tScraping membership's data from Georgia's parliament..."
        for collection in data_collections:
            print "\n\t\tScraping %s membership\n\n" % collection
            if collection == "chambers":
                for item in data_collections[collection]:
                    identifier = item['identifiers']['identifier']
                    o_id = self.get_id("organizations", "8", "chamber")
                    p_id = self.get_id("people", identifier)
                    member = item['membership']
                    role = membership_groups[item['membership']]
                    url = "http://www.parliament.ge/ge/parlamentarebi/deputatebis-sia"
                    if p_id != "Not found" and o_id != "Not found":
                        membership_json = self.build_memberships_doc(p_id, o_id, member, role, url)
                        membership_array.append(membership_json)
            else:
                for item in data_collections[collection]:
                    url = item['url']
                    name = item['name']
                    soup_faction = scrape.download_html_file(url)
                    div = soup_faction.find("div", {"class": "submenu_list"})
                    members_tag = div.find('a').get_text(strip=True)
                    if "წევრები" in members_tag.encode('utf-8'):
                        # or div.find('a').get_text().encode('utf-8') == "კომიტეტის წევრები":
                        url_members = div.find('a').get("href")
                        # print url_members
                        soup_members = scrape.download_html_file(url_members)
                        for each_a in soup_members.find("div", {"class": "mps_list"}):
                            if each_a.find('a'):
                                continue
                            else:
                                full_name = each_a.find('h4').next.encode('utf-8')
                                member = each_a.find('p').next.encode('utf-8')
                                url = each_a.get('href').encode('utf-8')
                                person_id_from_url = url.index('p/')
                                person_id = url[person_id_from_url + 2:]
                                if full_name.decode('utf-8') in mp_list:
                                    member_id = mp_list[full_name.decode('utf-8')]
                                else:
                                    member_id = person_id

                                o_id = self.get_id("organizations", name.encode('utf-8'))
                                p_id = self.get_id("people", member_id)
                                role = membership_groups[member]
                                if p_id != "Not found" and o_id != "Not found":
                                    membership_json = self.build_memberships_doc(p_id, o_id, member, role, url_members)
                                    membership_array.append(membership_json)
        print membership_array
        print "\n\tScraping completed! \n\tScraped " + str(len(membership_array)) + " members"
        return membership_array

    def build_memberships_doc(self, person_id, organization_id, label, role, url):
        json_doc = {
            "person_id": person_id,
            "organization_id": organization_id,
            "label": label,
            "role": role,
            "sources": [{
                "url": url,
                "note": "ვებგვერდი"
            }]
        }
        return json_doc

    def events_list(self):
        url = "http://www.parliament.ge/ge/saparlamento-saqmianoba/plenaruli-sxdomebi/plenaruli-sxdomis-dgis-wesrigi"
        soup = scrape.download_html_file(url)
        events = []
        pages = soup.find('div', {'class': 'paging'}).findAll('a')
        latest_page_url = pages[len(pages) - 1].get('href')
        latest_page_index = latest_page_url.index('0/')
        latest_page = latest_page_url[latest_page_index + 2:]

        names_array = []
        for i in range(0, int(latest_page) + 10, 10):
            url_pages = url + "/0/" + str(i)
            soup_pages = scrape.download_html_file(url_pages)
            for each_a in soup_pages.find('div', {'class': 'news_list'}).findAll('a', {'class': "item"}):
                url_motion = each_a.get('href')
                name = each_a.get_text().strip().replace("  ", " ")
                name = name.replace("                                    ", "")
                start_date = ""
                if name not in names_array:
                    names_array.append(name)
                    json_event = {
                        "name": name,
                        "url": url_motion,
                        "start_date": start_date
                    }
                    events.append(json_event)
        #             print json_event
        #             print "---------------------------\n"
        #
        # print len(names_array)
        return events

    def scrape_events(self):
        events_list = self.events_list()
        url_array = []
        counter = 0
        for event in events_list:
            print "event nr: %s ---------------------->" % str(counter)
            soup = scrape.download_html_file(event['url'])
            a_tag = soup.find('div', {'class': 'inner_page'}).findAll('a')
            if len(a_tag) > 0:
                for each_a in a_tag:
                    url = each_a.get('href')
                    if url and "/ge/law/" in url and url not in url_array:
                        url_array.append(url)
            counter += 1
        print len(url_array)

    def get_chamber_identifier(self, founding_year):
        if founding_year == "2008":
            return "7"
        elif founding_year == "2004":
            return "6"
        elif founding_year == "1999":
            return "5"
        elif founding_year == "1995":
            return "4"
        elif founding_year == "1992":
            return "3"
        elif founding_year == "1990":
            return "2"

    def scrape_chamber(self):
        chambers_list = []
        chambers_list.append({
            "classification": "chamber",
            "name": "საქართველოს პარლამენტი - 2012-2016 წწ.",
            "identifiers": [{
                    "identifier": "8",
                    "scheme": "parliament.ge"
                }],
            "founding_date": "2012",
            "dissolution_date": "2016-10",
        })
        chamber_list_html = "http://www.parliament.ge/ge/parlamentarebi/saqartvelos-wina-mowvevis-parlamentebi-1317"
        scrape = scraper.Scraper()

        soup = scrape.download_html_file(chamber_list_html)

        print "\n\tScraping chamber's data from Georgia's parliament..."
        for each_a in soup.find("div", {"class": "submenu_list"}):
            if each_a.find('a'):
                continue
            else:
                name = each_a.get_text()
                years = re.findall(r'\d+', name)
                source_url = each_a.get('href')
                founding_year = years[0]
                dissolution_date = years[1]
                identifier = self.get_chamber_identifier(founding_year)
                identifiers = {
                    "identifier": identifier,
                    "scheme": "parliament.ge"
                }

                chamber_json = self.build_chamber_doc(name, identifiers, founding_year, dissolution_date, source_url)
                chambers_list.append(chamber_json)
        print "\n\tScraping completed! \n\tScraped " + str(len(chambers_list)) + " chambers"
        return chambers_list

    def build_organizations_doc(self, classification, name, url):
        json_doc = {
            "classification": classification,
            "name": name,
            "sources": [{
                "note": "ვებგვერდი",
                "url": url
            }]
        }
        return json_doc

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