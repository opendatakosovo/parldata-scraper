# -*- coding: utf-8 -*-
from pymongo import MongoClient
from app.mod_scraper import scraper
from datetime import date
import vpapi
import re

client = MongoClient()
db = client.parlament_md
scrape = scraper.Scraper()


class MoldovaScraper():
    terms = {
        "12": {
            "start_date": "1990",
            "end_date": "1994"
        },
        "13": {
            "start_date": "1994",
            "end_date": "1998"
        },
        "14": {
            "start_date": "1999",
            "end_date": "2001"
        },
        "15": {
            "start_date": "2001",
            "end_date": "2005"
        },
        "16": {
            "start_date": "2005",
            "end_date": "2009"
        },
        "17": {
            "start_date": "2009-04",
            "end_date": "2009-07"
        },
        "18": {
            "start_date": "2009-07",
            "end_date": "2010-09"
        },
        "19": {
            "start_date": "2010-12-28",
            "end_date": "2014-07"
        },
        "20": {
            "start_date": "2014-12-29",
            "end_date": ""
        }
    }
    # def sk_to_utc(self, dt_str):
    #     """Converts Slovak date(-time) string into ISO format in UTC time."""
    #     match = re.search(SK_MONTHS_REGEX, dt_str, re.IGNORECASE)
    #     if match:
    #         month = match.group(0)
    #         dt_str = dt_str.replace(month, '%s.' % SK_MONTHS[month[:3].lower()])
    #     dt = dateutil.parser.parse(dt_str, dayfirst=True)
    #     if ':' in dt_str:
    #         return vpapi.local_to_utc(dt, to_string=True)
    #     else:
    #         return dt.strftime('%Y-%m-%d')

    def guess_gender(self, first_name):
        if first_name[-1:] == "a":
            return "female"
        else:
            return "male"

    def build_json_doc(self, identifier, full_name, first_name, last_name, url, image_url, gender):
        json_doc = {
            "identifiers": [{
                "identifier": identifier,
                "scheme": "parlament.md"
            }],
            "gender": gender,
            "name": full_name,
            "given_name": first_name,
            "family_name": last_name,
            "sources": [{
                "note": "pagină web",
                "url": url
            }],
            "image": image_url,
            "sort_name": last_name + ", " + first_name
        }
        return json_doc

    def mps_list(self):
        deputy_list = []
        deputy_list_url = "http://www.parlament.md/StructuraParlamentului/Deputies/tabid/87/language/ro-RO/Default.aspx"
        soup = scrape.download_html_file(deputy_list_url)
        each = soup.find("div", {"class": "allTitle"}).find("table", {"cellspacing": "4"}).findAll('tr')

        for tr in each:
            name = tr.find("td").find("img").get("alt").replace("  ", " ")
            link = tr.find("td", {"valign": "top"}).find("a").get("href")
            # fraction_link = tr.find("td", {"valign": "top"}).find("a", {"class": "FractionLink"}).get("href")
            # fraction = tr.find("td", {"valign": "top"}).find("a", {"class": "FractionLink"}).next
            image_url = "http://www.parlament.md" + tr.find("td").find("img").get("src")
            names = name.split(' ')
            first_name = names[1]
            last_name = names[0]
            sort_name = names[0] + ", " + names[1]
            name_ordered = first_name + " " + last_name
            gender = self.guess_gender(first_name)
            index_start = link.index('Id/')
            index_end = link.index('/la')
            member_id = link[index_start + 3:index_end]
            soup_deputy = scrape.download_html_file(link)
            membership = soup_deputy.find("span", {"id": "dnn_ctr476_ViewDeputat_lblPosition"})
            deputy_json = {
                "membership": membership.get_text(),
                "identifier": member_id,
                "name": name_ordered,
                "sort_name": sort_name,
                "gender": gender,
                "url": link,
                "image_url": image_url,
                "given_name": first_name,
                "family_name": last_name,
            }
            deputy_list.append(deputy_json)
        return deputy_list

    def membership_correction(self):
        return {
            "Preşedinte": "chairman",
            "Preşedintele Parlamentului": "chairman",
            "Vicepreşedinte": "vice-chairman",
            "Vicepreşedintele Parlamentului": "vice-chairman",
            "Membru": "member",
            "Deputat": "member",
            "Secretar": "secretary"
        }

    def scrape_membership(self):
        chamber_membership = []
        mps_list = self.mps_list()
        members = {}
        membership_correction = self.membership_correction()
        all_members = vpapi.getall("people")
        for member in all_members:
            members[member['identifiers'][0]['identifier']] = member['id']
        chamber_id = vpapi.getfirst("organizations",
                                    where={"identifiers": {
                                        "$elemMatch": {
                                            "identifier": "20", "scheme": "parlament.md"
                                        }
                                    }})
        deputy_list_url = "http://www.parlament.md/StructuraParlamentului/" \
                          "Deputies/tabid/87/language/ro-RO/Default.aspx"
        for member in mps_list:
            p_id = members[member['identifier']]
            role = membership_correction[member['membership'].encode('utf-8')]
            chamber_membership_json = self.build_memberships_doc(p_id, chamber_id['id'], member['membership'],
                                                                 role, deputy_list_url)
            chamber_membership.append(chamber_membership_json)
        return chamber_membership

    def scrape_parliamentary_group_membership(self):
        print "\n\tScraping parliamentary groups membership from Moldova's parliament..."
        parties_list = self.parliamentary_group_list()
        membership_correction = self.membership_correction()
        parties = {}
        all_parties = vpapi.getall("organizations", where={'classification': "parliamentary group"})
        for party in all_parties:
            parties[party['identifiers'][0]['identifier']] = party['id']

        members = {}
        all_members = vpapi.getall("people")
        for member in all_members:
            members[member['identifiers'][0]['identifier']] = member['id']

        parties_membership = []
        for party in parties_list:
            party_identifier = party['identifier']
            soup_party = scrape.download_html_file(party['url'])
            for each_tr in soup_party.find("fieldset", {"id": "dnn_ctr482_ViewFraction_fsMembers"}).findAll('tr'):
                td_array = each_tr.findAll('td')
                link = td_array[1].find('a').get('href')
                index_start = link.index('/Id/') + 4
                index_end = link.index('/la')
                member_identifier = link[index_start:index_end]
                membership = td_array[2].get_text().strip()
                member_id = members[member_identifier]
                o_id = parties[party_identifier]
                if membership == "":
                    membership = "Membru"
                role = membership_correction[membership.encode('utf-8')]
                party_membership_json = self.build_memberships_doc(member_id, o_id, membership, role, party['url'])
                parties_membership.append(party_membership_json)
        print "\n\tScraping completed! \n\tScraped " + str(len(parties_membership)) + " members of parties \n"
        return parties_membership

    def build_memberships_doc(self, person_id, organization_id, label, role, url):
        json_doc = {
            "person_id": person_id,
            "organization_id": organization_id,
            "label": label,
            "role": role,
            "sources": [{
                "url": url,
                "note": "Pagină web"
            }]
        }
        return json_doc


    def scrape_mp_bio_data(self):
        mps_list = self.mps_list()
        members = []
        print "\n\tScraping people data from Moldova's parliament..."
        print "\tThis may take a few minutes..."
        for member in mps_list:
            # identifier, full_name, first_name, last_name, url, image_url, gender
            member_json = self.build_json_doc(member['identifier'], member['name'], member['given_name'],
                                              member['family_name'], member['url'], member['image_url'],
                                              member['gender'])
            members.append(member_json)
        print "\n\tScraping completed! \n\tScraped " + str(len(members)) + " members"
        return members
        # print "Scraped %s members" % str(counter)

    def committee_list(self):
        committee_list = []
        url = "http://www.parlament.md/StructuraParlamentului/Comisiipermanente/tabid/84/language/ro-RO/Default.aspx"
        soup = scrape.download_html_file(url)
        for each_tr in soup.find("table", {"id": "dnn_ctr486_ViewCommissionPermanent_ctrlViewCommissionType_dlCommissions"}).findAll('tr'):
            name = each_tr.find("a").get_text()
            committee_url = each_tr.find("a").get('href')

            index_start = committee_url.index("nId/") + 4
            index_end = committee_url.index("/language")
            identifier = committee_url[index_start:index_end]
            committee_json = {
                "name": name,
                "url": committee_url,
                "identifier": identifier
            }
            committee_list.append(committee_json)
        return committee_list

    def scrape_committee(self):
        committees = self.committee_list()
        chamber_id = vpapi.getfirst("organizations",
                                    where={"identifiers": {
                                        "$elemMatch": {
                                            "identifier": "20", "scheme": "parlament.md"
                                        }
                                    }})
        committees_list = []
        print "\n\tScraping parliamentary committees from Moldova's parliament..."
        for committee in committees:
            soup = scrape.download_html_file(committee['url'])
            email_tag = soup.find("span", {"id": "dnn_ctr486_ViewCommissionPermanent_ctrlViewCommissionType_lblCommissionContacts"}).find('a')
            phone = soup.find("span", {"id": "dnn_ctr486_ViewCommissionPermanent_ctrlViewCommissionType_lblCommissionContacts"}).find('p')
            if phone.get_text().strip() != "":
                phone_number = phone.get_text()[6:].strip()
            else:
                phone_number = None
            if email_tag:
                email = email_tag.get_text()
            else:
                email = None

            committee_json = self.build_organization_doc("committe", committee['name'], committee['identifier'],
                                                         "", "", committee['url'], email, chamber_id['id'], )

            del committee_json['founding_date']
            del committee_json['dissolution_date']
            if not email:
                del committee_json['contact_details']
            elif not phone_number:
                del committee_json['contact_details']
            else:
                committee_json['contact_details'].append({
                    "label": "Tel.",
                    "type": "tel",
                    "value": phone_number
                })
            committees_list.append(committee_json)
        print "\n\tScraping completed! \n\tScraped " + str(len(committees_list)) + " committees"
        return committees_list

    def parliamentary_group_list(self):
        url = "http://www.parlament.md/StructuraParlamentului/Fractiuniparlamentare/" \
              "tabid/83/language/ro-RO/Default.aspx"
        soup = scrape.download_html_file(url)
        parties_list = []
        for each_tr in soup.find('table', {"id": "dnn_ctr482_ViewFraction_grdView"}).findAll("tr"):
            if each_tr.find('th'):
                continue
            else:
                all_a_tags = each_tr.findAll('a', {"class": "fractionTitle"})
                for a_tag in all_a_tags:
                    name = a_tag.get_text()
                    url = a_tag.get('href')
                    index_start = url.index("/Id/") + 4
                    index_end = url.index("/language")
                    identifier = url[index_start:index_end]
                    parties_json = {
                        "name": name,
                        "url": url,
                        "identifier": identifier
                    }
                    parties_list.append(parties_json)
        return parties_list

    def scrape_parliamentary_groups(self):
        chamber_id = vpapi.getfirst("organizations",
                                    where={"identifiers": {
                                        "$elemMatch": {
                                            "identifier": "20", "scheme": "parlament.md"
                                        }
                                    }})
        parties_list = self.parliamentary_group_list()
        parties = []
        print "\n\tScraping parliamentary groups from Moldova's parliament..."
        for party in parties_list:
            founding_date = self.terms["20"]["start_date"]
            party_json = self.build_organization_doc("parliamentary group", party['name'],
                                                     party['identifier'], founding_date, "",
                                                     party['url'], "", chamber_id['id'])
            del party_json['contact_details']
            del party_json['dissolution_date']
            parties.append(party_json)
        return parties

    def scrape_chamber(self):
        url = "http://www.parlament.md/Parlamentarismul%C3%AEnRepublicaMoldova/" \
              "Istorie%C8%99ievolu%C8%9Bie/tabid/96/language/ro-RO/Default.aspx"
        chambers_to_fix = {"XII": "12", "XIII": "13", "XIV": "14", "XV": "15", "XVI": "16", "XVII": "17",
                           "XVIII": "18", "XIX": "19", "XX": "20"}
        chambers = []
        soup = scrape.download_html_file(url)
        print "\n\tScraping chambers from Armenia's parliament..."
        for each_a in soup.find('div', {"class": "LocalizedContent"}).findAll('a'):
            name = each_a.get_text().strip()
            if name != "":
                url = "http://www.parlament.md" + each_a.get('href')
                if "(" in name:
                    chamber_roman = name[name.index('X'):name.index('(')].replace('-a', "").strip()
                    chamber_identifier = chambers_to_fix[chamber_roman]
                    founding_date = self.terms[chamber_identifier]['start_date']
                    dissolution_date = self.terms[chamber_identifier]['end_date']
                else:
                    chamber_roman = name[-6:len(name)-3].strip()
                    chamber_identifier = chambers_to_fix[chamber_roman]
                    founding_date = self.terms[chamber_identifier]['start_date']
                    dissolution_date = self.terms[chamber_identifier]['end_date']

                chamber_json = self.build_organization_doc("chamber", name, chamber_identifier, founding_date,
                                                           dissolution_date, url, "", "")

                del chamber_json['contact_details']
                del chamber_json['parent_id']
                if chamber_identifier == "20":
                    del chamber_json['dissolution_date']

                existing = vpapi.getfirst("organizations", where={'identifiers': {'$elemMatch': chamber_json['identifiers'][0]}})
                if not existing:
                    resp = vpapi.post("organizations", chamber_json)
                else:
                    # update by PUT is preferred over PATCH to correctly remove properties that no longer exist now
                    resp = vpapi.put("organizations", existing['id'], chamber_json, effective_date=self.effective_date())
                if resp["_status"] != "OK":
                    raise Exception("Invalid status code")
                chambers.append(chamber_json)
        print "\n\tScraping completed! \n\tScraped " + str(len(chambers)) + " chambers"
        return chambers

    def effective_date(self):
        return date.today().isoformat()

    def build_organization_doc(self, classification, name, identifier, founding_date,
                               dissolution_date, url, email, parent_id):
        return {
            "classification": classification,
            "name": name,
            "identifiers": [{
                "identifier": identifier,
                "scheme": "parlament.md"
            }],
            "founding_date": founding_date,
            "contact_details": [{
                "label": "e-mail",
                "type": "email",
                "value": email
            }],
            "dissolution_date": dissolution_date,
            "sources": [{
                "note": "Pagină web",
                "url": url
            }],
            "parent_id": parent_id
        }