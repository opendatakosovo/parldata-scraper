# -*- coding: utf-8 -*-
from app.mod_scraper import scraper
import belarus_lowerhouse_parser
from datetime import date
import vpapi
from progressbar import ProgressBar, Percentage, ETA, Counter, Bar

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

    def motions(self):
        return []

    def events(self):
        return []

    def vote_events(self):
        return []

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

    def build_memberships_doc(self, person_id, organization_id, label, role, url):
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

    def scrape_committee_members(self):
        print "\n\tScraping committee groups membership from Belarus Lowerhouse parliament..."
        committee_membership_list = []
        committee_list = parser.committee_membership()
        groups = {}
        all_groups = vpapi.getall("organizations", where={"classification": "committe"})
        for group in all_groups:
            groups[group['identifiers'][0]['identifier']] = group['id']
        roles = parser.membership_correction()
        for committee in committee_list:
            identifier = int(committee) + 2
            url = "http://house.gov.by/index.php/,17230,,,,2,,,0.html".replace("17230", str(identifier))
            for membership in committee_list[committee]:
                for members in committee_list[committee][membership]:
                    role = roles[membership]
                    membership_json = self.build_memberships_doc(members, groups[committee], membership, role, url)
                    committee_membership_list.append(membership_json)
        print "\n\tScraping completed! \n\tScraped " + str(len(committee_membership_list)) + " members of committee groups"
        return committee_membership_list

    def scrape_parliamentary_group_membership(self):
        print "\n\tScraping parliamentary groups membership from Belarus Lowerhouse's parliament..."
        party_membership = parser.parliamentary_group_membership()
        parties_membership_list = []
        for member in party_membership:
            party_membership_json = self.build_memberships_doc(member['person_id'], member['organization_id'],
                                                               member['membership'], member['role'], member['url'])
            parties_membership_list.append(party_membership_json)
        print "\n\tScraping completed! \n\tScraped " + str(len(parties_membership_list)) + " members of parliamentary groups"
        return parties_membership_list

    def scrape_membership(self):
        print "\n\tScraping membership's data from Belarus Lowerhouese parliament..."
        mp_list = parser.mps_list()
        chamber_membership_list = []
        members = {}
        url = "http://house.gov.by/index.php/,17041,,,,2,,,0.html"
        all_members = vpapi.getall("people")
        for person in all_members:
            members[person['identifiers'][0]['identifier']] = person['id']
        chamber = vpapi.getfirst("organizations", where={"identifiers": {"$elemMatch": {"identifier": "2", "scheme": "house.by"}}})
        for member in mp_list:
            p_id = members[member['identifier']]
            o_id = chamber['id']
            chamber_membership_json = self.build_memberships_doc(p_id, o_id, member['membership'], member['role'], url)
            chamber_membership_list.append(chamber_membership_json)
        print "\n\tScraping completed! \n\tScraped " + str(len(chamber_membership_list)) + " members"
        return chamber_membership_list

    def effective_date(self):
        return date.today().isoformat()

    def scrape_committee(self):
        print "\n\tScraping committee groups from Belarus Lowerhouse parliament..."
        committee_list = []
        committees = parser.committees()
        for committee in committees:
            committee_json = self.build_organization_doc("committe", committee['name'], committee['identifier'],
                                                         "", "", committee['url'], '', committee['parent_id'])
            del committee_json['contact_details']
            del committee_json['founding_date']
            del committee_json['dissolution_date']
            committee_json["contact_details"] = []
            committee_json["contact_details"].append({
                "type": "fax",
                "label": "факс",
                "value": committee['phone_number']
            })
            committee_json["contact_details"].append({
                "type": "tel",
                "label": "тэл",
                "value": committee['phone_number']
            })
            committee_list.append(committee_json)
        print "\n\tScraping completed! \n\tScraped " + str(len(committee_list)) + " committee groups"
        return committee_list


    def scrape_parliamentary_groups(self):
        print "\n\tScraping parliamentary groups from Belarus Lowerhouse parliament..."
        party_list = []
        parties = parser.parliamentary_groups()
        party_json = self.build_organization_doc("parliamentary group", parties['name'], parties['identifier'],
                                                 "", "", parties['url'], "", parties['parent_id'])
        del party_json['contact_details']
        del party_json['founding_date']
        del party_json['dissolution_date']
        party_list.append(party_json)
        print "\n\tScraping completed! \n\tScraped " + str(len(party_list)) + " parliamentary groups"
        return party_list

    def scrape_chamber(self):
        print "\n\tScraping chambers from Belarus Lowerhouse parliament..."
        chambers = parser.chambers()
        chambers_list = []
        url = "http://house.gov.by/index.php/,10087,,,,2,,,0.html"
        for chamber in chambers:
            chamber_json = self.build_organization_doc("chamber", chambers[chamber]['name'], chamber,
                                                       chambers[chamber]['start_date'], chambers[chamber]['end_date'],
                                                       url, "", "")
            if chamber == "2":
                del chamber_json['dissolution_date']
            del chamber_json['contact_details']
            del chamber_json['parent_id']

            existing = vpapi.getfirst("organizations", where={'identifiers': {'$elemMatch': chamber_json['identifiers'][0]}})
            if not existing:
                resp = vpapi.post("organizations", chamber_json)
            else:
                # update by PUT is preferred over PATCH to correctly remove properties that no longer exist now
                resp = vpapi.put("organizations", existing['id'], chamber_json, effective_date=self.effective_date())
            if resp["_status"] != "OK":
                raise Exception("Invalid status code")
            chambers_list.append(chamber_json)
        print "\n\tScraping completed! \n\tScraped " + str(len(chambers_list)) + " chambers"
        return chambers_list