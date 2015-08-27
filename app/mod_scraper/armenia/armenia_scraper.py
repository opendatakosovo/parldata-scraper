# -*- coding: utf-8 -*-
from app.mod_scraper import scraper
import re
from collections import OrderedDict

scrape = scraper.Scraper()

class ArmeniaScraper():
    def mps_list(self):
        mps_list = []
        terms = {
            "5": "ԱԺ հինգերորդ գումարում",
            "4": "ԱԺ չորրորդ գումարում",
            "3": "ԱԺ երրորդ գումարում",
            "2": "ԱԺ երկրորդ գումարում",
            "1": "ԱԺ առաջին գումարում",
        }
        names_deputies = []
        for term in list(reversed(sorted(terms.keys()))):
            print term
            url = "http://www.parliament.am/deputies.php?lang=arm&sel=full&ord=alpha&show_session=" + term
            print url
            soup = scrape.download_html_file(url)
            for each_div in soup.findAll('div', {'class': 'dep_name_list'}):
                url_deputy = each_div.findAll("a")
                if term != "5" and term != "4":
                    url_deputy_final = "http://www.parliament.am" + url_deputy[0].get('href')
                else:
                    url_deputy_final = "http://www.parliament.am" + url_deputy[1].get('href')
                index_of_start_id_url = url_deputy_final.index('ID=')
                index_of_end_id_url = url_deputy_final.index('&lang')
                member_id = url_deputy_final[index_of_start_id_url + 3:index_of_end_id_url]
                full_text = each_div.get_text().strip()
                if "(" in full_text:
                    index = full_text.index("(")
                    membership = full_text[index + 1: len(full_text) - 1]
                # print "This is FULL TEXT: " + full_text
                else:
                    membership = "member"
                distinct_id = full_text[:3]
                name_unordered = full_text.replace(distinct_id, "").strip()
                names = name_unordered.split(' ')
                first_name = names[1]
                last_name = names[0]
                middle_name = names[2]
                name_ordered = "%s %s %s" % (first_name, middle_name, last_name)

                if name_ordered not in names_deputies:
                    names_deputies.append(name_ordered)
                    # print "name: %s " % name_ordered
                    members_json = {
                        "membership": membership,
                        "member_id": member_id,
                        "url": url_deputy_final,
                        "name": name_ordered,
                        "given_name": first_name,
                        "family_name": last_name,
                        "sort_name": last_name + ", " + first_name,
                        "distinct_id": distinct_id,
                    }
                    # soup_deputy = scrape.download_html_file(url_deputy)
                    # for each_row in soup_deputy.find('div', {'class': 'dep_description'}).find('tbody').findAll("tr"):
                    #     print each_row
                    # print "\n\nname: %s \nId: %s" % (name.strip(), distinct_id)
                    # print "url: http://www.parliament.am" + url[1].get('href')
                    mps_list.append(members_json)
                    print members_json
                    print "-------------------------------------------"
        print "\tScraped %s members" % str(len(mps_list))
        return mps_list
        # print array

    def guess_gender(self, first_name):
        females = ["Հերմինե", "Հեղինե", "Մարգարիտ", "Նաիրա", "Արփինե", "Մարինե", "Ռուզաննա", "Շուշան",
                   "Կարինե", "Զարուհի", "Էլինար", "Լյուդմիլա", "Լարիսա", "Անահիտ", "Լիլիթ", "Գոհար",
                   "Ալվարդ", "Հռիփսիմե", "Հրանուշ", "Արմենուհի", "Էմմա"]

        if first_name.encode('utf-8') in females:
            return "female"
        else:
            return "male"

    def build_json_doc(self, identifier, full_name, first_name, last_name, url, image_url,
                       email, date_of_birth, gender, biography):
        json_doc = {
            "identifiers": [identifier],
            "gender": gender,
            "name": full_name,
            "given_name": first_name,
            "family_name": last_name,
            "sources": [{
                "note": "վեբ էջ",
                "url": url
            }],
            "image": image_url,
            "contact_details": [{
                "label": "Էլ. փոստ",
                "type": "email",
                "value": email
            }],
            "sort_name": last_name + ", " + first_name,
            "birth_date": date_of_birth,
            "biography": biography
        }
        return json_doc

    def scrape_mp_bio_data(self):
        mps_list = self.mps_list()
        members_list = []
        print "\n\tScraping people data from Armenia's parliament..."
        for member in mps_list:
            birth_date = ""
            email = ""
            soup = scrape.download_html_file(member['url'])
            each_tr = soup.find("div", {'class': "dep_description"}).find('table', {"width": "480"}).findAll('tr')
            if each_tr[0].find('td', {'rowspan': "8"}).find('img'):
                image_url = "url: http://www.parliament.am/" + each_tr[0].find('td', {'rowspan': "8"}).find('img').get('src')
            else:
                image_url = "http://snapparcel.com/wp-content/uploads/2014/10/url-150x150.png"

            if each_tr[1].find('td'):
                birth_date = each_tr[1].find('div', {'class': "description_2"}).get_text()

            if each_tr[len(each_tr) - 1].find('a'):
                email = each_tr[len(each_tr) - 1].find('a').get_text()
            else:
                email = None

            birth_date_array = birth_date.split(".")
            birth_date_ordered = "%s-%s-%s" % (birth_date_array[2], birth_date_array[1], birth_date_array[0])
            biography = soup.find('div', {"class": "content"}).get_text().strip()
            mp_biography = biography.replace('\n', ' ').replace('\r', '').strip()
            gender = self.guess_gender(member['given_name'])
            member_json = self.build_json_doc(member['member_id'], member['name'], member['given_name'], member['family_name'],
                                              member['url'], image_url, email, birth_date_ordered, gender, mp_biography)

            if not email:
                del member_json['contact_details']
            members_list.append(member_json)
        print "\n\tScraping completed! \n\tScraped " + str(len(members_list)) + " members"
        return members_list

    def scrape_organization(self):
            print "scraping Armenia Votes data"