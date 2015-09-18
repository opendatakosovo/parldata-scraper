# -*- coding: utf-8 -*-
from app.mod_scraper import scraper
from datetime import date
import vpapi
import re
from progressbar import ProgressBar, Percentage, ETA, Bar, FileTransferSpeed, Counter
import json

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

    def members_list(self):
        mps_list = []
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
                    membership = "անդամ".decode('utf-8')
                distinct_id = full_text[:3]
                name_unordered = full_text.replace(distinct_id, "").strip()
                names = name_unordered.split(' ')
                first_name = names[1]
                last_name = names[0]
                middle_name = names[2]
                name_ordered = "%s %s %s" % (first_name, middle_name, last_name)

                # print "name: %s " % name_ordered
                members_json = {
                    "term": str(term),
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

    def mps_list(self):
        members_list = []
        names_deputies = []
        mps = self.members_list()
        for member in mps:
            if member['name'] not in names_deputies:
                names_deputies.append(member['name'])
                members_list.append(member)
        return members_list

    def guess_gender(self, first_name):
        females = ["Հերմինե", "Հեղինե", "Մարգարիտ", "Նաիրա", "Արփինե", "Մարինե", "Ռուզաննա", "Շուշան",
                   "Կարինե", "Զարուհի", "Էլինար", "Լյուդմիլա", "Լարիսա", "Անահիտ", "Լիլիթ", "Գոհար",
                   "Ալվարդ", "Հռիփսիմե", "Հրանուշ", "Արմենուհի", "Էմմա"]

        if first_name.encode('utf-8') in females:
            return "female"
        else:
            return "male"

    def membership_correction(self):
        return {
            "Ազգային ժողովի նախագահ": "chairman",
            "Ազգային ժողովի նախագահի տեղակալ": "vice-chairman",
            "հանձնաժողովի նախագահ": "chairman",
            "ղեկավար": "chairman",
            "քարտուղար": "secretary",
            "անդամ": "member",
            "հանձնաժողովի նախագահի տեղակալ": "vice-chairman",
        }

    def scrape_committee_membership(self):
        print "\n\tScraping committee groups membership from Armenia's parliament...\n"
        committees = self.committee_list()
        committee_membership = []
        chambers = {}
        groups = {}
        members = {}
        memberships = self.membership_correction()
        all_chambers = vpapi.getall("organizations", where={"classification": "chamber"})
        for chamber in all_chambers:
            chambers[chamber['identifiers'][0]["identifier"]] = chamber['id']

        all_groups = vpapi.getall('organizations', where={"classification": "committe"})
        for group in all_groups:
            groups[group['sources'][0]['url']] = group['id']

        all_members = vpapi.getall("people")
        for member in all_members:
            members[member['name']] = member['id']
        widgets = ['        Progress: ', Percentage(), ' ', Bar(marker='#', left='[', right=']'),
                   ' ', ETA(), " - Processed: ", Counter(), ' items             ']
        pbar = ProgressBar(widgets=widgets)
        for committee in pbar(committees):
            url = committee['url'].replace('show', "members")
            soup = scrape.download_html_file(url)
            for each_tr in soup.find('table', {"style": "margin-top:10px; margin-bottom:10px;"}).findAll('tr'):
                if each_tr.has_attr('bgcolor'):
                    continue
                else:
                    td_array = each_tr.findAll('td')
                    if td_array:
                        names = td_array[0].find('a').get_text().split(' ')
                        first_name = names[1]
                        last_name = names[0]
                        middle_name = names[2]
                        name_ordered = "%s %s %s" % (first_name, middle_name, last_name)
                        membership = each_tr.find('span', {'class': "news_date"}).get_text()

                        if url in groups:
                            o_id = groups[url]

                        if membership == "":
                            membership = "անդամ".decode('utf-8')
                        else:
                            membership = membership[1:len(membership)-1]

                        role = memberships[membership.encode('utf-8')]
                        if name_ordered in members:
                            p_id = members[name_ordered]
                        party_membership_json = self.build_memberships_doc(p_id, o_id, membership, role, url)
                        committee_membership.append(party_membership_json)
        print "\n\tScraping completed! \n\tScraped " + str(len(committee_membership)) + " members of committee groups"
        return committee_membership

    def scrape_parliamentary_group_membership(self):
        print "\n\tScraping parliamentary groups membership from Armenia's parliament...\n"
        chambers = {}
        groups = {}
        members = {}
        memberships = self.membership_correction()

        all_chambers = vpapi.getall("organizations", where={"classification": "chamber"})
        for chamber in all_chambers:
            chambers[chamber['identifiers'][0]["identifier"]] = chamber['id']

        all_groups = vpapi.getall('organizations', where={"classification": "parliamentary group"})
        for group in all_groups:
            groups[group['sources'][0]['url']] = group['id']

        all_members = vpapi.getall("people")
        for member in all_members:
            members[member['name']] = member['id']

        parties_membership = []

        widgets = ['        Progress: ', Percentage(), ' ', Bar(marker='#', left='[', right=']'),
                   ' ', ETA(), " - Processed: ", Counter(), ' items             ']
        pbar = ProgressBar(widgets=widgets)
        for term in pbar(list(reversed(sorted(self.terms.keys())))):
            url = "http://www.parliament.am/deputies.php?lang=arm&sel=factions&SubscribeEmail=&show_session=" + str(term)
            soup = scrape.download_html_file(url)
            for each_div in soup.findAll('div', {"class": "content"}):
                party_name = each_div.find("center").find("b").get_text()
                party_name_ordered = party_name.replace("  ", " ")
                exist = vpapi.getfirst("organizations", where={'name': party_name_ordered,
                                                               "parent_id": chambers[str(term)]})
                if exist:
                    o_id = exist['id']
                for each_tr in each_div.find('table', {"style": "margin-top:10px; margin-bottom:10px;"}).findAll('tr'):
                    if each_tr.has_attr('bgcolor'):
                        continue
                    else:
                        td_array = each_tr.findAll('td')
                        names = td_array[0].find('a').get_text().split(' ')
                        first_name = names[1]
                        last_name = names[0]
                        middle_name = names[2]
                        name_ordered = "%s %s %s" % (first_name, middle_name, last_name)
                        membership = each_tr.find('span', {'class': "news_date"}).get_text()

                        if membership == "":
                            membership = "անդամ".decode('utf-8')
                        else:
                            membership = membership[1:len(membership)-1]

                        role = memberships[membership.encode('utf-8')]
                        if name_ordered in members:
                            p_id = members[name_ordered]
                        party_membership_json = self.build_memberships_doc(p_id, o_id, membership, role, url)
                        parties_membership.append(party_membership_json)
        print "\n\tScraping completed! \n\tScraped " + str(len(parties_membership)) + " members of parliamentary groups"
        return parties_membership
        # print counter

    def scrape_membership(self):
        print "\n\tScraping membership's data from Armenia's parliament...\n"
        mps = self.members_list()
        memberships = []
        roles = self.membership_correction()
        chambers = {}
        all_chambers = vpapi.getall("organizations", where={"classification": "chamber"})
        for chamber in all_chambers:
            chambers[chamber['identifiers'][0]["identifier"]] = chamber['id']

        members = {}
        all_members = vpapi.getall("people")
        for member in all_members:
            members[member['name']] = member['id']

        widgets = ['        Progress: ', Percentage(), ' ', Bar(marker='#', left='[', right=']'),
                   ' ', ETA(), " - Processed: ", Counter(), ' items             ']
        pbar = ProgressBar(widgets=widgets)
        for member in pbar(mps):
            p_id = members[member['name']]
            o_id = chambers[member['term']]
            role = ""
            membership_label = member['membership']
            if member['membership'].encode('utf-8') in roles:
                role = roles["անդամ"]
            url = "http://www.parliament.am/deputies.php?lang=arm&sel=full&ord=alpha&show_session=" + member['term']
            membership_json = self.build_memberships_doc(p_id, o_id, membership_label, role, url)
            memberships.append(membership_json)

        print "\n\tScraping completed! \n\tScraped " + str(len(memberships)) + " members"
        return memberships

    def build_memberships_doc(self, person_id, organization_id, label, role, url):
        json_doc = {
            "person_id": person_id,
            "organization_id": organization_id,
            "label": label,
            "role": role,
            "sources": [{
                "url": url,
                "note": "վեբ էջ"
            }]
        }
        return json_doc

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
        print "\n\tScraping people data from Armenia's parliament..."
        print "\tThis may take a few minutes...\n"
        mps_list = self.mps_list()
        members_list = []
        widgets = ['        Progress: ', Percentage(), ' ', Bar(marker='#', left='[', right=']'),
                                   ' ', ETA(), " - Processed: ", Counter(), ' items             ']
        pbar = ProgressBar(widgets=widgets)
        for member in pbar(mps_list):
            birth_date = ""
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

    def parliamentary_groups(self):
        parties_doc = {}
        parties_correction = {
            "«ԺՈՂՈՎՐԴԱԿԱՆ ՊԱՏԳԱՄԱՎՈՐ» պատգամավորական խումբ": "«ԺՈՂՈՎՐԴԱԿԱՆ ՊԱՏԳԱՄԱՎՈՐ»",
            "«ՀԱՅԱՍՏԱՆ» պատգամավորական խումբ": "«ՀԱՅԱՍՏԱՆ»",
            "«ԱԳՐՈԱՐԴՅՈՒՆԱԲԵՐԱԿԱՆ ԺՈՂՈՎՐԴԱԿԱՆ ՄԻԱՎՈՐՈՒՄ» պատգամավորական խումբ": "«ԱԳՐՈԱՐԴՅՈՒՆԱԲԵՐԱԿԱՆ ԺՈՂՈՎՐԴԱԿԱՆ ՄԻԱՎՈՐՈՒՄ»",
            "«ԺՈՂՈՎՐԴԻ ՁԱՅՆ» պատգամավորական խումբ": "«ԺՈՂՈՎՐԴԻ ՁԱՅՆ»",
            "«Օրինաց  երկիր»": "«Օրինաց երկիր»",
            "«Ժողովրդական պատգամավոր» պատգամավորական խումբ": "«Ժողովրդական պատգամավոր»",
            "«Գործարար» պատգամավորական խումբ": "«Գործարար»",
            "«Բարեփոխումներ» պատգամավորական խումբ": "«Բարեփոխումներ»"
        }
        for term in list(reversed(sorted(self.terms.keys()))):
            url = "http://www.parliament.am/deputies.php?lang=arm&sel=factions&SubscribeEmail=&show_session=" + term
            soup = scrape.download_html_file(url)
            parties_doc[str(term)] = {}
            for each_a in soup.find("div", {"class": "level3menu"}).findAll("a"):
                url = "http://www.parliament.am" + each_a.get('href')
                party_name = each_a.get_text().encode('utf-8')
                party_name_ordered = party_name.replace(" խմբակցություն", "").strip()
                if party_name_ordered in parties_correction:
                    party_name_ordered = parties_correction[party_name_ordered]
                index_start = url.index("ID=")
                index_end = url.index("&lang")
                identifier = url[index_start + 3:index_end]
                parties_doc[str(term)][party_name_ordered.decode('utf-8')] = {
                    "url": url,
                    "identifier": identifier,
                }
        return parties_doc

    def scrape_parliamentary_groups(self):
        parties_list = []
        terms_ids = {}

        all_terms = vpapi.getall("organizations", where={"classification": "chamber"})

        for term in all_terms:
            terms_ids[term['identifiers'][0]['identifier']] = term['id']

        parties_doc = self.parliamentary_groups()

        print "\n\tScraping parliamentary groups from Armenia's parliament...\n"
        widgets = ['        Progress: ', Percentage(), ' ', Bar(marker='#', left='[', right=']'),
                   ' ', ETA(), " - Processed: ", Counter(), ' items             ']
        pbar = ProgressBar(widgets=widgets)
        for term in pbar(parties_doc):
            url = "http://www.parliament.am/deputies.php?lang=arm&sel=factions&SubscribeEmail=&show_session=" + term
            soup = scrape.download_html_file(url)
            all_divs = soup.findAll('div', {"class": "content"})
            for each_div in all_divs:
                name = each_div.find("center").find("b").get_text()
                name_ordered = name.replace("  ", " ")
                if name_ordered in parties_doc[term]:
                    identifier = parties_doc[term][name_ordered]['identifier']
                    url_faction = parties_doc[term][name_ordered]['url']
                    founding_date = self.terms[term]["start_date"]
                    parent_id = terms_ids[str(term)]

                    if each_div.find("center").find("a"):
                        email = each_div.find("center").find("a").get_text()

                    if term != "5":
                        dissolution_date = self.terms[term]["end_date"]
                    else:
                        dissolution_date = None

                    party_json = self.build_organization_doc("parliamentary group", name_ordered, identifier,
                                                             founding_date, dissolution_date, url_faction, email, parent_id)

                    if not dissolution_date:
                        del party_json['dissolution_date']

                    if not email or email == None:
                        del party_json['contact_details']

                    if not identifier:
                        del party_json['identifiers']

                    parties_list.append(party_json)
                else:
                    print "term: %s \nname: %s" % (term, name_ordered)
        print "\n\tScraping completed! \n\tScraped " + str(len(parties_list)) + " parliametary groups"
        return parties_list

    def committee_list(self):
        committee_list = []
        chambers = {}
        all_chambers = vpapi.getall("organizations", where={"classification": "chamber"})
        for chamber in all_chambers:
            chambers[chamber['identifiers'][0]['identifier']] = chamber['id']
        for i in range(3, 6):
            url = "http://www.parliament.am/committees.php?lang=arm&show_session=" + str(i)
            soup = scrape.download_html_file(url)
            for each_tr in soup.find("table", {"class": "com-table"}).findAll('tr', {"valign": "top"}):
                for each_td in each_tr.findAll('td'):
                    name = each_td.find('a', {"class": "blue_mid_b"}).get_text()
                    url = "http://www.parliament.am" + each_td.find('a', {"class": "blue_mid_b"}).get("href")
                    identifier = re.findall(r'\d+', url)
                    committee_json = {
                        "name": name,
                        "url": url,
                        "identifier": identifier[0],
                        "parent_id": chambers[str(i)]
                    }
                    committee_list.append(committee_json)
        return committee_list

    def scrape_committee(self):
        print "\n\tScraping committee groups from Armenia's parliament..."
        committees = self.committee_list()
        committees_list = []
        widgets = ['        Progress: ', Percentage(), ' ', Bar(marker='#', left='[', right=']'),
                   ' ', ETA(), " - Processed: ", Counter(), ' items             ']
        pbar = ProgressBar(widgets=widgets)
        for committee in pbar(committees):
            url = committee['url'].replace('show', "members")
            soup = scrape.download_html_file(url)
            if soup.find("div", {"style": "border-bottom:1px solid #E2E2E2;"}).find('a').get_text() != "":
                email = soup.find("div", {"style": "border-bottom:1px solid #E2E2E2;"}).find('a').get_text()
            else:
                email = None

            committee_json = self.build_organization_doc("committe", committee['name'], committee['identifier'],
                                                         "", "", url, email, committee['parent_id'])

            if not email:
                del committee_json['contact_details']
            del committee_json['dissolution_date']
            del committee_json['founding_date']

            committees_list.append(committee_json)
            # email = soup.find("div", {"style": "border-bottom:1px solid #E2E2E2;"}).find('a').get('href')
        print "\n\tScraping completed! \n\tScraped " + str(len(committees_list)) + " committee groups"
        return committees_list

    def effective_date(self):
        return date.today().isoformat()

    def scrape_chamber(self):
        url = "http://www.parliament.am/deputies.php?sel=ful&ord=photo&show_session=5&lang=arm&enc=utf8"
        soup = scrape.download_html_file(url)
        chambers_list = []
        print "\n\tScraping chambers from Armenia's parliament...\n"
        widgets = ['        Progress: ', Percentage(), ' ', Bar(marker='#', left='[', right=']'),
                   ' ', ETA(), " - Processed: ", Counter(), ' items             ']
        pbar = ProgressBar(widgets=widgets)
        all_options = soup.find("select", {"name": "show_session"}).findAll("option")
        for each_option in pbar(all_options):
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
                    resp = vpapi.put("organizations", existing['id'], chamber_json, effective_date=self.effective_date())
                if resp["_status"] != "OK":
                    raise Exception("Invalid status code")
                chambers_list.append(chamber_json)
        print "\n\tScraping completed! \n\tScraped " + str(len(chambers_list)) + " chambers"
        return chambers_list