# -*- coding: utf-8 -*-
from app.mod_scraper import scraper
from datetime import date
import vpapi

scrape = scraper.Scraper()

class ArmeniaScraper():
    terms = {
        "1": {
            "start_date": "1995-07-27",
            "end_date": "1999-06-09"
        },
        "2": {
            "start_date": "1999-06-10",
            "end_date": "2003-05-14"
        },
        "3": {
            "start_date": "2003-06-10",
            "end_date": "2007-04-09"
        },
        "4": {
            "start_date": "2007-06-07",
            "end_date": "2012-05-31"
        },
        "5": {
            "start_date": "2012-05-31",
            "end_date": ""
        }
    }

    def mps_list(self):
        mps_list = []
        names_deputies = []
        for term in list(reversed(sorted(self.terms.keys()))):
            url = "http://www.parliament.am/deputies.php?lang=arm&sel=full&ord=alpha&show_session=" + term
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
                    mps_list.append(members_json)
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
            "identifiers": [{
                "identifier": identifier,
                "scheme": "parliament.am"
            }],
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
        print "\tThis may take a few minutes..."
        for member in mps_list:
            birth_date = ""
            email = ""
            soup = scrape.download_html_file(member['url'])
            each_tr = soup.find("div", {'class': "dep_description"}).find('table', {"width": "480"}).findAll('tr')
            if each_tr[0].find('td', {'rowspan': "8"}).find('img'):
                image_url = "http://www.parliament.am/" + each_tr[0].find('td', {'rowspan': "8"}).find('img').get('src')
                image_url.replace("big", "small")
            else:
                image_url = None

            if each_tr[1].find('td'):
                birth_date = each_tr[1].find('div', {'class': "description_2"}).get_text()

            if each_tr[len(each_tr) - 1].find('a'):
                email = each_tr[len(each_tr) - 1].find('a').get_text()
                if email[-2:] != "am":
                    email = None
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

            if not image_url:
                del member_json['image']

            members_list.append(member_json)
        print "\n\tScraping completed! \n\tScraped " + str(len(members_list)) + " members"
        return members_list

    def build_organization_doc(self, classification, name, identifier, founding_date,
                               dissolution_date, url, email, parent_id):
        return {
            "classification": classification,
            "name": name,
            "identifiers": [{
                "identifier": identifier,
                "scheme": "parliament.am"
            }],
            "founding_date": founding_date,
            "contact_details": [{
                "label": "Էլ. փոստ",
                "type": "email",
                "value": email
            }],
            "dissolution_date": dissolution_date,
            "sources": [{
                "note": "վեբ էջ",
                "url": url
            }],
            "parent_id": parent_id
        }

    def scrape_parliamentary_groups(self):
        parties_list = []
        terms_ids = {}

        all_terms = vpapi.getall("organizations", where={"classification": "chamber"})

        print "\n\tScraping parliamentary groups from Armenia's parliament..."
        for term in all_terms:
            terms_ids[term['identifiers'][0]['identifier']] = term['id']

        for term in list(reversed(sorted(self.terms.keys()))):
            url = "http://www.parliament.am/deputies.php?lang=arm&sel=factions&SubscribeEmail=&show_session=" + term
            soup = scrape.download_html_file(url)
            parties_doc = {}
            for each_a in soup.find("div", {"class": "level3menu"}).findAll("a"):
                url = "http://www.parliament.am" + each_a.get('href')
                party_name = each_a.get_text().encode('utf-8')
                party_name_ordered = party_name.replace(" խմբակցություն", "").strip()
                index_start = url.index("ID=")
                index_end = url.index("&lang")
                identifier = url[index_start + 3:index_end]
                if identifier != "0":
                    parties_doc[party_name_ordered.decode('utf-8')] = {
                        "url": url,
                        "identifier": identifier,
                    }

            for each_div in soup.findAll('div', {"class": "content"}):
                name = each_div.find("center").find("b").get_text()
                name_ordered = name.replace("  ", " ")
                if name in parties_doc:
                    identifier = parties_doc[name]['identifier']
                else:
                    identifier = None
                founding_date = self.terms[term]["start_date"]
                parent_id = terms_ids[term]

                if each_div.find("center").find("a"):
                    email = each_div.find("center").find("a").get_text()

                if term != "5":
                    dissolution_date = self.terms[term]["end_date"]
                else:
                    dissolution_date = None

                party_json = self.build_organization_doc("parliamentary group", name_ordered, identifier, founding_date,
                                                         dissolution_date, url, email, parent_id)

                if not dissolution_date:
                    del party_json['dissolution_date']

                if email or email != None:
                    del party_json['contact_details']

                if identifier or identifier == None:
                    del party_json['identifiers']

                parties_list.append(party_json)
        print "\n\tScraping completed! \n\tScraped " + str(len(parties_list)) + " parliametary groups"
        return parties_list


    def effective_date(self):
        return date.today().isoformat()

    def scrape_chamber(self):
        url = "http://www.parliament.am/deputies.php?sel=ful&ord=photo&show_session=5&lang=arm&enc=utf8"
        soup = scrape.download_html_file(url)
        chambers_list = []
        print "\n\tScraping chambers from Armenia's parliament..."
        for each_option in soup.find("select", {"name": "show_session"}).findAll("option"):
            identifier = each_option.get('value')
            name = each_option.get_text()
            url = "http://www.parliament.am/deputies.php?lang=arm&sel=&ord=&show_session=" + identifier
            if "100" not in identifier:
                founding_date = self.terms[identifier]["start_date"]
                dissolution_date = self.terms[identifier]["end_date"]
                chamber_json = self.build_organization_doc("chamber", name, identifier, founding_date,
                                                           dissolution_date, url, "", "")

                del chamber_json['contact_details']
                del chamber_json['parent_id']
                if identifier == "5":
                    del chamber_json['dissolution_date']

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

    def scrape_organization(self):
        print "scraping Armenia Votes data"