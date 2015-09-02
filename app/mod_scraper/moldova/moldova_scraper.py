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
            name = tr.find("td").find("img").get("alt")
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