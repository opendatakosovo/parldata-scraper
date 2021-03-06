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
        # Iterates in every chamber json document and returns the
        # list with the json document structure that Visegrad+ API accepts
        print "\n\tScraping chambers from Belarus Upperhouse parliament...\n"
        chambers_list = []
        chambers = parser.chambers_list()
        widgets = ['        Progress: ', Percentage(), ' ', Bar(marker='#', left='[', right=']'),
                   ' ', ETA(), " - Processed: ", Counter(), ' items             ']
        pbar = ProgressBar(widgets=widgets)
        for chamber in pbar(chambers):
            chamber_json = self.build_organization_doc("chamber", chambers[chamber]['name'], chamber,
                                                       chambers[chamber]['start_date'], chambers[chamber]['end_date'],
                                                       chambers[chamber]['url'], "", "")
            if len(chambers[chamber]["end_date"]) == 0:
                del chamber_json['dissolution_date']

            del chamber_json['contact_details']
            del chamber_json['parent_id']
            chambers_list.append(chamber_json)
        print "\n\tScraping completed! \n\tScraped " + str(len(chambers_list)) + " chambers"
        return chambers_list

    def scrape_parliamentary_group_membership(self):
        # Returns an empty list because there are no parliamentary groups data available in the official website.
        return []

    def scrape_committee_members(self):
        # Iterates in every committee member json doc and returns the
        # list with the json document structure that Visegrad+ API accepts
        print "\n\tScraping committee groups from Belarus Upperhouse parliament...\n"
        members = {}
        committee_membership = []
        all_members = vpapi.getall("people")
        for member in all_members:
            if member['identifiers'][0]['identifier'] not in members:
                members[member['identifiers'][0]['identifier']] = member['id']
            else:
                continue

        committee_membership_list = parser.committee_membership()
        widgets = ['        Progress: ', Percentage(), ' ', Bar(marker='#', left='[', right=']'),
                   ' ', ETA(), " - Processed: ", Counter(), ' items             ']
        pbar = ProgressBar(widgets=widgets)

        print "\n\tProcessing members of committee groups from Belarus Upperhouse parliament...\n"
        for member in pbar(committee_membership_list):

            if member['identifier'] in members:
                p_id = members[member['identifier']]
            else:
                p_id = None
            existing = vpapi.getfirst("organizations", where={"name": member['committee_name'], "parent_id": member['committee_parent_id']})
            if existing:
                o_id = existing['id']
            else:
                o_id = None

            if p_id and o_id:
                committee_membership_json = self.build_memberships_doc(p_id, o_id, member['membership'],
                                                                       member['role'], member['url'])
                committee_membership.append(committee_membership_json)
            else:
                continue
        print "\n\tScraping completed! \n\tScraped " + str(len(committee_membership)) + " members"
        return committee_membership

    def scrape_membership(self):
        # Iterates in chamber member json document and
        # returns the list with the json document structure that Visegrad+ API accepts
        print "\n\tScraping chambers membership's data from Belarus Upperhouse parliament...\n"
        members = {}
        all_members = vpapi.getall("people")
        for member in all_members:
            members[member['name']] = member['id']

        chambers = {}
        all_chambers = vpapi.getall("organizations", where={"classification": "chamber"})
        for chamber in all_chambers:
            chambers[chamber['identifiers'][0]['identifier']] = chamber['id']
        terms = parser.terms
        mps_list = parser.members_list()
        chambers_membership = []

        widgets = ['        Progress: ', Percentage(), ' ', Bar(marker='#', left='[', right=']'),
                   ' ', ETA(), " - Processed: ", Counter(), ' items             ']
        pbar = ProgressBar(widgets=widgets)
        for member in pbar(mps_list):
            p_id = members[member['name']]
            o_id = chambers[member['term']]
            url = terms[member['term']]['url']
            membership_label = member['membership']
            role = member['role']
            chamber_membership_json = self.build_memberships_doc(p_id, o_id, membership_label, role, url)
            chambers_membership.append(chamber_membership_json)
        print "\n\tScraping completed! \n\tScraped " + str(len(chambers_membership)) + " members"
        return chambers_membership

    def scrape_committee_membership(self):
        # Returns the list of scraped and structured committee groups membership
        committee_membership = parser.committee_membership()

    def build_memberships_doc(self, person_id, organization_id, label, role, url):
        # Returns the json structure of membership document that Visegrad+ API accepts
        json_doc = {
            "person_id": person_id,
            "organization_id": organization_id,
            "label": label,
            "role": role,
            "sources": [{
                "url": url,
                "note": "сайт"
            }]
        }
        return json_doc

    def scrape_committee(self):
        # Iterates in every committee member json doc and returns the
        # list with the json document structure that Visegrad+ API accepts
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
        print "\n\tScraping completed! \n\tScraped " + str(len(committees)) + " committees"
        return committees

    def build_organization_doc(self, classification, name, identifier, founding_date,
                               dissolution_date, url, email, parent_id):
        # Returns the json structure of organization document that Visegrad+ API accepts
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

    def scrape_parliamentary_groups(self):
        # Returns an empty list because there are no parliamentary groups data available in the official website.
        return []

    def scrape_mp_bio_data(self):
        # Iterates in every MP json doc and returns the MP list which
        # was built with the json document structure that Visegrad+ API accepts
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
        # Returns the json structure of a member document that Visegrad+ API accepts
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
        # Returns gender of a member based on his/her first name.
        females = ["Наталля"]
        if name[-1] == "а".decode('utf-8') or name.encode('utf-8') in females:
            return "female"
        else:
            return "male"