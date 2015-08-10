# -*- coding: utf-8 -*-
from pymongo import MongoClient
import scraper, re
import requests
import pprint

client = MongoClient()
db = client.parlament_md

class MoldovaScraper():

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

    def scrape_mp_bio_data(self):
        db.mps_list.remove({})

        print "\nScraping members (people) of Moldova's parliament..."

        deputy_list_url = "http://www.parlament.md/StructuraParlamentului/Deputies/tabid/87/language/ro-RO/Default.aspx"

        scrape = scraper.Scraper()

        soup = scrape.download_html_file(deputy_list_url)

        counter = 0

        each = soup.findAll("table", {"cellspacing": "4"})[0].findAll('tr')

        for tr in each:
            name = tr.find("td").find("img").get("alt")
            link = tr.find("td", {"valign": "top"}).find("a").get("href")
            fraction_link = tr.find("td", {"valign": "top"}).find("a", {"class": "FractionLink"}).get("href")
            fraction = tr.find("td", {"valign": "top"}).find("a", {"class": "FractionLink"}).next
            image_url = "http://www.parlament.md" + tr.find("td").find("img").get("src")

            print "<<<<<<<<<<<<<<<<<<<<<<<"
            print "name: " + name
            print "fraction: " + fraction
            print "fraction_link: " + fraction_link
            print "image_url: " + image_url
            print "link: " + link

            if "id/" in link:
                print link.index('Id/')
                print link.index('/la')
                person_id_url = link[:link.index('/la')]
                person_id = person_id_url[link.index('/Id/'):]
                print "PERSON_ID: " + person_id.replace('/Id/', '')
            print "identifier: " + person_id_url[:4].replace('/', "")
            soup_deputy = scrape.download_html_file(link)
            membership = soup_deputy.find("span", {"id": "dnn_ctr476_ViewDeputat_lblPosition"})
            birth_date = soup_deputy.find("fieldset", {"id": "dnn_ctr476_ViewDeputat_fsCurriculumVitae"}).find("span")
            print birth_date
            if membership.next[:1] != "P":
                labels = soup_deputy.findAll("td", {"class": "SubHead"})
                committe = soup_deputy.find("a", {"id": "dnn_ctr476_ViewDeputat_hlCommission"})
                party = soup_deputy.find("a", {"id": "dnn_ctr476_ViewDeputat_hlFraction"})
                label_committe = ""
                label_party = ""
                for label in labels:
                    if label.has_attr('style'):
                        label_committe = label.get_text()
                    else:
                        label_party = label.get_text()
                print "%s %s" % (label_party.strip().replace(' ', "_").lower(), party.next)
                print "%s %s" % (label_committe.strip().replace(' ', "_").lower(), committe.next)
                print ">>>>>>>>>>>>>>>>>>>>>>>"
            else:
                print "member: " + membership.next
                print ">>>>>>>>>>>>>>>>>>>>>>>"

            counter += 1

        print "Scraping compete!\nScraped %s members " % str(counter)

    def scrape_organization(self):
        print "scraping Moldova Votes data"