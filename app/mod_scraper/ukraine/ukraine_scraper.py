# -*- coding: utf-8 -*-
from progressbar import ProgressBar, Percentage, ETA, Counter, Bar
import vpapi
import ukraine_parser
from operator import itemgetter

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

    def test_date_sort(self):
        date_list = [
            {
                "date": "1998-09-19T17:55:00",
                "name": "DATA E PARE"
            },
            {
                "date": "1998-01-19T17:55:00",
                "name": "DATA E PARE"
            },
            {
                "date": "1998-06-19T17:55:00",
                "name": "DATA E PARE"
            }
        ]
        sorted_vote_events = sorted(date_list, key=itemgetter('date'))
        print sorted_vote_events
        return sorted_vote_events

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
        for member in pbar(mps_list[900:]):
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

    def get_index(self, collection, sort, vote_events):
        last_event = vpapi.getfirst(collection, sort=sort)
        if last_event:
            index = next(index for (index, d) in enumerate(vote_events) if d["identifier"] == last_event['identifier']) + 1
        else:
            index = 0
        return index

    def vote_events(self):
        print "\n\n\tScraping Motions and Vote Events data from Ukraine's parliament..."
        vote_events = parser.vote_events_list("vote-events", '-start_date')
        index_vote_events = self.get_index("vote-events", "-start_date", vote_events)
        voting_events = []
        for vote_event in vote_events[index_vote_events:]:
            vote_event_json = vote_event
            del vote_event_json['text']
            del vote_event_json['sources']
            del vote_event_json['date']
            voting_events.append(vote_event_json)

        motions = []
        for motion in vote_events[index_vote_events:]:
            json_motion = motion
            del json_motion['counts']
            del json_motion['motion_id']
            del json_motion['start_date']
            motions.append(json_motion)
        if len(voting_events) > 0 and len(motions) > 0:
            print "\n\tScraping completed! \n\tScraped " + str(len(voting_events)) + "motions and vote events"
        else:
            print "\n\tThere are no new motions or vote events."
        return (motions, voting_events)

    def scrape_votes(self):
        parser.scrape_voting_records()

    def motions(self):
        print "\n\n\tScraping Motions data from Ukraine's parliament..."
        vote_events = parser.vote_events_list("motions", '-date')
        last_event = vpapi.getfirst("motions", sort='-date')
        if last_event:
            index = next(index for (index, d) in enumerate(vote_events) if d["identifier"] == last_event['identifier']) + 1
        else:
            index = 0
        print index
        motions = []
        for motion in vote_events[index:]:
            json_motion = motion
            del json_motion['counts']
            del json_motion['motion_id']
            del json_motion['start_date']
            motions.append(json_motion)
            vpapi.post("vote-events", json_motion)
        if len(motions) > 0:
            print "\n\tScraping completed! \n\tScraped " + str(len(motions)) + " motions"
        else:
            print "\n\tThere are no new motions."
        return motions

    def scrape_events(self):
        print "\n\tScraping events from Ukraine's parliament..."
        print "\tPlease wait. This may take a few moments...\n"
        events = parser.events()
        events_list = []
        if len(events) > 0:
            for event in events:
                event_json = {
                    'id': event['identifier'],
                    "name": event['name'],
                    'end_date': event['end_date'],
                    'identifier': event['identifier'],
                    'organization_id': event['organization_id'],
                    'start_date': event['start_date'],
                    'sources': [{
                        'url': event['url'],
                        "note": "веб-сайт"
                    }]
                }
                events_list.append(event_json)
        print "\n\tScraping completed! \n\tScraped " + str(len(events_list)) + " members"
        return events_list

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
        for member in committee_membership[740:]:
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