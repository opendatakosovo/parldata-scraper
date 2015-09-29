# -*- coding: utf-8 -*-
from progressbar import ProgressBar, Percentage, ETA, Counter, Bar
import vpapi
import ukraine_parser
import pprint

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

    def scrape_committee(self):
        print "\n\tScraping committee groups from Ukraine's parliament...\n"
        committee_list = parser.committees()
        committees = []
        for committee in committee_list:
            committee_json = self.build_organization_doc("committe", committee['name'], committee['identifier'],
                                                         committee['start_date'], committee['end_date'],
                                                         committee['url'], "", committee['parent_id'])
            del committee_json['contact_details']

            if committee['start_date']:
                del committee_json['founding_date']

            if committee['end_date']:
                del committee_json['dissolution_date']

            committees.append(committee_json)
        print "\n\tScraping completed! \n\tScraped " + str(len(committees)) + " committees"
        return committees

    def scrape_parliamentary_group_membership(self):
        print "\n\tScraping parliamentary groups membership from Ukraine's parliament...\n"
        parties_membership = parser.parliamentary_group_membership()
        memberships = []
        for member in parties_membership:
            party_membership_json = self.build_memberships_doc(member['person_id'], member['organization_id'],
                                                               member['membership'], member['role'], member['url'])
            if not member['role']:
                del party_membership_json['role']

            if member['start_date']:
                party_membership_json['start_date'] = member['start_date']

            if member['end_date']:
                party_membership_json['end_date'] = member['end_date']
            memberships.append(party_membership_json)
        print "\n\tScraping completed! \n\tScraped " + str(len(memberships)) + " members"
        return memberships

    def scrape_membership(self):
        print "\n\tScraping chambers membership's data from Ukraine's parliament..."
        print "\tPlease wait. This may take a few moments...\n"
        members = {}
        all_members = vpapi.getall("people")
        for member in all_members:
            members[member['name']] = member['id']

        chambers = {}
        all_chambers = vpapi.getall("organizations", where={"classification": "chamber"})
        for chamber in all_chambers:
            chambers[chamber['identifiers'][0]['identifier']] = chamber['id']
        terms = parser.chambers()
        mps_list = parser.mps_list()
        chambers_membership = []

        widgets = ['        Progress: ', Percentage(), ' ', Bar(marker='#', left='[', right=']'),
                   ' ', ETA(), " - Processed: ", Counter(), ' items             ']
        pbar = ProgressBar(widgets=widgets)
        for member in pbar(mps_list):
            if member['name'] in members:
                p_id = members[member['name']]
                o_id = chambers[member['term']]
                url = terms[member['term']]['url']
                membership_label = member['membership']
                role = member['role']
                chamber_membership_json = self.build_memberships_doc(p_id, o_id, membership_label, role, url)
                chambers_membership.append(chamber_membership_json)
        print "\n\tScraping completed! \n\tScraped " + str(len(chambers_membership)) + " members"
        return chambers_membership

    def build_memberships_doc(self, person_id, organization_id, label, role, url):
        json_doc = {
            "person_id": person_id,
            "organization_id": organization_id,
            "label": label,
            "role": role,
            "sources": [{
                "url": url,
                "note": "веб-сайт"
            }]
        }
        return json_doc

    def test_ids(self):
        committees_ids = {}
        all_committees = vpapi.getall("organizations", where={'classification': "committe"})
        for committe in all_committees:
            committees_ids[committe['identifiers'][0]['identifier']] = committe['id']
        print len(committees_ids)

    def scrape_committee_members(self):
        print "\n\tScraping committee groups membership from Ukraine's parliament...\n"
        committee_membership = parser.committee_membership()
        memberships = []
        for member in committee_membership:
            # person_id, organization_id, label, role, url
            committee_membership_json = self.build_memberships_doc(member['person_id'], member['organization_id'],
                                                                   member['membership'], member['role'], member['url'])
            if not member['role']:
                del committee_membership_json['role']
            memberships.append(committee_membership_json)
        print "\n\tScraping completed! \n\tScraped " + str(len(memberships)) + " members"
        return memberships

    def scrape_parliamentary_groups(self):
        print "\n\tScraping parliamentary groups from Ukraine's parliament...\n"
        parties = parser.parliamentary_groups()
        parties_list = []
        for party in parties:
            party_json = self.build_organization_doc("parliamentary group", party['name'],
                                                     party['identifier'], party['start_date'],
                                                     party['end_date'], party['url'], "",
                                                     party['parent_id'])

            del party_json['contact_details']

            if party['start_date']:
                del party_json['founding_date']

            if party['end_date']:
                del party_json['dissolution_date']
            parties_list.append(party_json)
        print "\n\tScraping completed! \n\tScraped " + str(len(parties_list)) + " members"
        return parties_list

    def scrape_chamber(self):
        print "\n\tScraping chambers from Ukraine's parliament...\n"
        chambers = parser.chambers()
        chambers_list = []
        widgets = ['        Progress: ', Percentage(), ' ', Bar(marker='#', left='[', right=']'),
                   ' ', ETA(), " - Processed: ", Counter(), ' chambers             ']
        pbar = ProgressBar(widgets=widgets)
        for chamber in pbar(chambers):
            chamber_json = self.build_organization_doc("chamber", chambers[chamber]['name'], chamber,
                                                       chambers[chamber]['start_date'], chambers[chamber]['end_date'],
                                                       chambers[chamber]['url'], "", "")

            if chambers[chamber]['end_date'] == "":
                del chamber_json['dissolution_date']

            del chamber_json['contact_details']
            del chamber_json['parent_id']

            chambers_list.append(chamber_json)
        print "\n\tScraping completed! \n\tScraped " + str(len(chambers_list)) + " chambers"
        return chambers_list

    def build_organization_doc(self, classification, name, identifier, founding_date,
                               dissolution_date, url, email, parent_id):
        return {
            "classification": classification,
            "name": name,
            "identifiers": [{
                "identifier": identifier,
                "scheme": "rada.ua"
            }],
            "founding_date": founding_date,
            "contact_details": [{
                "label": "Ел. пошта",
                "type": "email",
                "value": email
            }],
            "dissolution_date": dissolution_date,
            "sources": [{
                "note": "веб-сторінка",
                "url": url
            }],
            "parent_id": parent_id
        }

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