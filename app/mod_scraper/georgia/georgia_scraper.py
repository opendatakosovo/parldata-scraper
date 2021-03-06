# -*- coding: utf-8 -*-
from pymongo import MongoClient
from app.mod_scraper import scraper
from urllib2 import urlopen
import vpapi
import json
import re
from bs4 import BeautifulSoup
import dateutil.parser
from datetime import date
from progressbar import ProgressBar, Percentage, ETA, Counter, Bar

client = MongoClient()
db = client.ge
scrape = scraper.Scraper()

class GeorgiaScraper():
    def effective_date(self):
        return date.today().isoformat()

    names_to_fix_json = {
        "როლანდი ახალაია": "როლანდ ახალაია",
        "მახირ დარზიევი": "მახირი დარზიევი",
        "დავითი დარცმელიძე": "დავით დარცმელიძე",
        "ლევან თარხნიშვილი": "ლევანი თარხნიშვილი",
        "თამარ კორძაია": "თამარი კორძაია",
        "ვახტანგი ლემონჯავა": "ვახტანგ ლემონჯავა",
        "ტარიელი ლონდარიძე": "ტარიელ ლონდარიძე",
        "თემურ მაისურაძე": "თემური მაისურაძე",
        "მიხეილი მაჭავარიანი": "მიხეილ მაჭავარიანი",
        "თამაზ მეჭიაური": "თამაზი მეჭიაური",
        "გურამი მისაბიშვილი": "გურამ მისაბიშვილი",
        "თეიმურაზ ნერგაძე": "თეიმურაზი ნერგაძე",
        "მირიანი წიკლაური": "მირიან წიკლაური",
        "დარეჯან ჩხეტიანი": "დარეჯანი ჩხეტიანი",
        "ოთარ ჩრდილელი": "ოთარი ჩრდილელი",
        "ზურაბი ჩილინგარაშვილი": "ზურაბ ჩილინგარაშვილი",
        "თამაზ შიოშვილი": "თამაზი შიოშვილი",
        "ნიკოლოზ ყიფშიძე": "ნიკოლოზი ყიფშიძე",
        "გედევან ფოფხაძე": "გედევანი ფოფხაძე",
        "გიორგი ჟვანია": "გოგლა ჟვანია",
        "ფრიდონ საყვარელიძე": "ფრიდონი საყვარელიძე",
        "სამველ პეტროსიან": "სამველ პეტროსიანი",
    }

    def local_to_utc(self, dt_str):
        # Function that converts a date string to utc and returns date string
        dt = dateutil.parser.parse(dt_str, dayfirst=True)
        if ':' in dt_str:
            return vpapi.local_to_utc(dt, to_string=True)
        else:
            return dt.strftime('%Y-%m-%d')

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

    def names_to_fix(self, name):
        # Names of MP that needs to fix, different names are in different pages for one MP.
        if name in self.names_to_fix_json:
            first_name = self.names_to_fix_json[name]
        else:
            first_name = name
        return first_name

    def mps_list(self):
        # Returns MP list with the basic information data for each member of Georgia's parliament.
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
                full_name_final = self.names_to_fix(full_name)
                url = each.get('href')
                membership = each.find('p').next.encode('utf-8')
                image_url = each.find('img').get('src')
                person_id_from_url = url.index('p/')
                gender = self.guess_gender(first_name)
                person_id = url[person_id_from_url + 2:]

                if full_name_final.decode('utf-8') in mp_list:
                    member_id = mp_list[full_name_final.decode('utf-8')]
                else:
                    member_id = person_id

                identifiers = {
                    "identifier": member_id.encode('utf-8'),
                    "scheme": "parliament.ge"
                }

                mp_json = {
                    "name": full_name_final,
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
        # Returns the json document which can translate the membership labels from georgian language to english..
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
        # Returns members list with all the information needed data for each member
        # with the json structure that Visegrad+ API accepts for Armenia's parliament.
        print "\n\tScraping people data from Georgia's parliament..."
        mps_list = self.mps_list()
        db.mps_list.remove({})
        scrape = scraper.Scraper()
        deputies = []
        widgets = ['        Progress: ', Percentage(), ' ', Bar(marker='#', left='[', right=']'),
                   ' ', ETA(), " - Processed: ", Counter(), ' items             ']
        pbar = ProgressBar(widgets=widgets)
        #iterate through each deputy in the deputies list.
        for json in pbar(mps_list): #iterate over loop [above sections]8
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
        # Returns the list of parliamentary groups with basic information for each
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
        # Returns the list of committee groups with basic information for each
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
        # Scrapes parliamentary groups and returns the list of
        # parliamentary groups with all the information needed for each
        print "\n\tScraping parliamentary groups data from Georgia's parliament..."
        parties_list = []
        parties = self.parliamentary_grous_list()
        widgets = ['        Progress: ', Percentage(), ' ', Bar(marker='#', left='[', right=']'),
                   ' ', ETA(), " - Processed: ", Counter(), ' groups of parties             ']
        pbar = ProgressBar(widgets=widgets)
        for party in pbar(parties):
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

    def scrape_committee(self):
        # Scrapes committee groups and returns the list of
        # committee groups with all the information needed for each.
        committees_list = []
        committees = self.parliamentary_committes_list()
        print "\n\tScraping committees data from Georgia's parliament..."
        widgets = ['        Progress: ', Percentage(), ' ', Bar(marker='#', left='[', right=']'),
                   ' ', ETA(), " - Processed: ", Counter(), ' items             ']
        pbar = ProgressBar(widgets=widgets)
        for committee in pbar(committees):
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
        # Returns chambers membership list with all the information data
        # needed for each member of Georgia's parliament.
        membership_array = []
        mp_list = self.get_member_id()
        members_list = self.mps_list()
        parties = self.scrape_parliamentary_groups()
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
                widgets = ['        Progress: ', Percentage(), ' ', Bar(marker='#', left='[', right=']'),
                           ' ', ETA(), " - Processed: ", Counter(), ' items             ']
                pbar = ProgressBar(widgets=widgets)
                for item in pbar(data_collections[collection]):
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
                widgets = ['        Progress: ', Percentage(), ' ', Bar(marker='#', left='[', right=']'),
                           ' ', ETA(), " - Processed members from: ", Counter(), ' ' + collection + '             ']
                pbar = ProgressBar(widgets=widgets)
                for item in pbar(data_collections[collection]):
                    if collection == "parties":
                        url = item['sources'][0]['url']
                    else:
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
                                full_name_final = self.names_to_fix(full_name)
                                member = each_a.find('p').next.encode('utf-8')
                                url_m = each_a.get('href').encode('utf-8')
                                person_id_from_url = url_m.index('p/')
                                person_id = url[person_id_from_url + 2:]
                                if full_name_final.decode('utf-8') in mp_list:
                                    member_id = mp_list[full_name_final.decode('utf-8')]
                                else:
                                    member_id = person_id

                                o_id = self.get_id("organizations", name.encode('utf-8'))
                                p_id = self.get_id("people", member_id)
                                role = membership_groups[member]
                                if p_id != "Not found" and o_id != "Not found":
                                    membership_json = self.build_memberships_doc(p_id, o_id, member, role, url_members)
                                    membership_array.append(membership_json)
        print "\n\tScraping completed! \n\tScraped " + str(len(membership_array)) + " members"
        return membership_array

    def build_memberships_doc(self, person_id, organization_id, label, role, url):
        # Returns the json structure of membership document that Visegrad+ API accepts
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

    def laws(self):
        # Returns the list of the json structure of motions and
        # vote events document with all the information data needed for both.
        laws_url = "http://votes.parliament.ge/en/search/passed_laws?sEcho=1&iColumns=7&sColumns=&iDisplayStart=0" \
                   "&iDisplayLength=3000000&mDataProp_0=0&mDataProp_1=1&mDataProp_2=2&mDataProp_3=3&mDataProp_4=4" \
                   "&mDataProp_5=5&mDataProp_6=6&sSearch=&bRegex=false&sSearch_0=&bRegex_0=false" \
                   "&bSearchable_0=true&sSearch_1=&bRegex_1=false&bSearchable_1=true&sSearch_2=" \
                   "&bRegex_2=false&bSearchable_2=true&sSearch_3=&bRegex_3=false&bSearchable_3=true&sSearch_4=" \
                   "&bRegex_4=false&bSearchable_4=true&sSearch_5=&bRegex_5=false&bSearchable_5=true&sSearch_6=" \
                   "&bRegex_6=false&bSearchable_6=true&iSortCol_0=0&sSortDir_0=desc&iSortingCols=1&bSortable_0=true" \
                   "&bSortable_1=true&bSortable_2=true&bSortable_3=true&bSortable_4=true&bSortable_5=true" \
                   "&bSortable_6=true&parliament=1&start_date=&end_date=&_=1440146282982"

        result = urlopen(laws_url).read()
        json_result = json.loads(result)
        laws_array = []
        last_item = vpapi.getfirst("vote-events", sort="-start_date")

        index_counter = 0
        if last_item:
            law_url = "/en/laws/" + last_item['id']
            for element in json_result['aaData']:
                soup = BeautifulSoup(element[1], "html.parser")
                url_soup = soup.find('a').get('href')
                if law_url == url_soup:
                    break
                index_counter += 1
        else:
            index_counter = len(json_result['aaData'])

        existing = vpapi.getfirst("organizations", where={"identifiers": {"$elemMatch": {"identifier": "8", "scheme": "parliament.ge"}}})
        if existing:
            organization_id = existing['id']

        widgets = ['        Progress: ', Percentage(), ' ', Bar(marker='#', left='[', right=']'),
                   ' ', ETA(), " - Processed: ", Counter(), ' items             ']
        pbar = ProgressBar(widgets=widgets)
        if len(json_result['aaData'][:index_counter]) > 0:
            for item in pbar(json_result['aaData'][:index_counter]):
                soup = BeautifulSoup(item[1], 'html.parser')
                api_name = soup.get_text()
                url = "http://votes.parliament.ge" + soup.find('a').get('href')
                index_of_id = url.index('laws/')
                index = index_of_id + 5
                motion_id = url[index:]
                date = self.local_to_utc(item[0] + " 04:00")
                votes_for = item[3]
                votes_against = item[4]
                # votes_abstain = str(item[5])
                votes_not_present = item[6]
                json_motion = {
                    "date": date,
                    "start_date": date,
                    "sources": [{
                        "url": url,
                        "note": "ვებგვერდი"
                    }],
                    "id": motion_id,
                    "identifier": motion_id,
                    "motion_id": motion_id,
                    "organization_id": organization_id,
                    "text": api_name,
                    "result": "pass",
                    "counts": [
                        {
                            "option": "yes",
                            "value": votes_for
                        },
                        {
                            "option": "no",
                            "value": votes_against
                        },
                        {
                            "option": "absent",
                            "value": votes_not_present
                        }
                    ]
                }
                laws_array.append(json_motion)
        return laws_array

    def events(self):
        return []

    def vote_events(self):
        # Returns the list with the json structure of vote events, deleting
        # some keys that we will not need for posting to the Visegrad+ API accepts
        print "\n\n\tScraping Vote Events data from Georgia's parliament..."
        laws_list = self.laws()
        vote_events = []
        for law in laws_list:
            del law['text']
            del law['sources']
            del law['date']
            vote_events.append(law)
        if len(vote_events) > 0:
            print "\n\tScraping completed! \n\tScraped " + str(len(vote_events)) + " vote events"
        else:
            print "\n\tThere are no new vote events."
        return vote_events

    def motions(self):
        # Returns the list with the json structure of motions, deleting
        # some keys that we will not need for posting to the Visegrad+ API accepts
        print "\n\n\tScraping Motions data from Georgia's parliament..."
        laws_list = self.laws()
        motions = []
        for motion in laws_list:
            del motion['counts']
            del motion['motion_id']
            del motion['start_date']
            motions.append(motion)
        if len(motions) > 0:
            print "\n\tScraping completed! \n\tScraped " + str(len(motions)) + " motions"
        else:
            print "\n\tThere are no new motions."

        return motions

    def get_group_id(self):
        # Returns the json with all the organization IDs
        groups = {}
        parties_ids = []
        all_groups = vpapi.getall("organizations", where={"classification": "parliamentary group"})
        for group in all_groups:
            parties_ids.append(group['id'])

        memberships = vpapi.getall("memberships")
        for member in memberships:
            if member['organization_id'] in parties_ids:
                groups[member['person_id']] = member['organization_id']
            else:
                groups[member['person_id']] = None
        return groups

    def get_all_member_ids_for_votes(self):
        members = {}
        api_members = vpapi.getall("people")

        for member in api_members:
            members[member['identifiers'][0]['identifier']] = member['id']

        return members

    def scrape_votes(self):
        # Scrapes votes and returns the list of votes with the json structure that Visegrad+ API accepts
        print "\n\n\tScraping votes data from Georgia's parliament...\n\tPlease wait. This may take a few minutes..."
        vote_events = self.vote_events()
        memberships = self.get_group_id()
        members = self.get_all_member_ids_for_votes()
        votes_array = []
        options_correction = {
            "Yes": "yes",
            "No": "no",
            "Abstain / Not Present*": "absent"
        }

        for law in vote_events:
            voting_results_url = "http://votes.parliament.ge/en/search/voting_results/%s?get_all_3_sessions=false" \
                             "&iDisplayLength=200000" % str(law['id'])
            result = urlopen(voting_results_url).read()
            json_result = json.loads(result)
            for item in json_result['aaData']:
                a_tag = BeautifulSoup(item[0], 'html.parser')
                url = a_tag.find('a').get('href')
                index = url.index('members/')
                member_id = url[index + 8:]
                option = item[1]
                if member_id in members:
                    member_id_API = members[member_id]
                    group_id = memberships[member_id_API]
                    if group_id:
                        json_doc = {
                            "vote_event_id": law['id'],
                            "option": options_correction[option],
                            "voter_id": member_id_API,
                            "group_id": group_id
                        }
                        votes_array.append(json_doc)
        print "\n\tScraping completed! \n\tScraped " + str(len(votes_array)) + " votes"
        return votes_array

    def get_chamber_identifier(self, founding_year):
        # Returns the chamber identifier
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
        # Returns the list with the json structure of vote events, deleting some keys
        # that we will not need for posting to the Visegrad+ API accepts
        print "\n\tScraping chamber's data from Georgia's parliament..."
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
        chamber_list_html = "http://www.parliament.ge/ge/parlamentarebi/wina-mowvevis-parlamentebi"
        soup = scrape.download_html_file(chamber_list_html)
        widgets = ['        Progress: ', Percentage(), ' ', Bar(marker='#', left='[', right=']'),
                   ' ', ETA(), " - Processed: ", Counter(), ' items             ']
        pbar = ProgressBar(widgets=widgets)
        for each_a in pbar(soup.find("div", {"class": "submenu_list"})):
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
        # Returns the json structure of an organization document that Visegrad+ API accepts
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
        # Returns the json structure of an chamber document that Visegrad+ API accepts
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
        # Returns the json structure of member document that Visegrad+ API accepts
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
        # Returns gender of a member based on his/her first name.
        females = ["მანანა", "ეკა", "თინათინ", "ხათუნა", "ნინო", "მარიკა", "ჩიორა", "თამარ", "გუგული",
                   "ანი", "ირმა", "მარიამ", "ნანა", "ელისო", "დარეჯან", "ფატი", "ეკატერინე"]
        if name in females:
            return "female"
        else:
            return "male"
