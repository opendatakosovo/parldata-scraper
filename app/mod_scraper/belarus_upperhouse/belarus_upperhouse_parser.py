# -*- coding: utf-8 -*-
from app.mod_scraper import scraper
import re
import vpapi
from progressbar import ProgressBar, Percentage, ETA, Counter, Bar

scrape = scraper.Scraper()


class BelarusUpperhouseParser():
    months_correction = {
        "января": "01",
        "февраля": "02",
        "марта": "03",
        "апреля": "04",
        "мая": "05",
        "июня": "06",
        "июля": "07",
        "августа": "08",
        "сентября": "09",
        "октября": "10",
        "ноября": "11",
        "декабря": "12"
    }

    terms = {
        "1": {
            "start_date": "1997-01-13",
            "end_date": "2000-12-19",
            "url": "http://www.sovrep.gov.by/ru/sozyvy-ru/view/pervij-sozyv-ru-1/"
        },
        "2": {
            "start_date": "2000-12-19",
            "end_date": "2004-11-15",
            "url": "http://www.sovrep.gov.by/ru/sozyvy-ru/view/vtoroy-sozyv-ru-2/"
        },
        "3": {
            "start_date": "2004-11-15",
            "end_date": "2008-10-31",
            "url": "http://www.sovrep.gov.by/ru/sozyvy-ru/view/tretij-sozyv-ru-3/"
        },
        "4": {
            "start_date": "2008-10-31",
            "end_date": "2012-10-19",
            "url": "http://www.sovrep.gov.by/ru/sozyvy-ru/view/chetverty-sozyv-ru-4/"
        },
        "5": {
            "start_date": "2012-10-19",
            "end_date": "",
            "url": "http://www.sovrep.gov.by/ru/sozyvy-ru/view/pyatyj-sozyv-ru-5/"
        }
    }

    def chambers_list(self):
        # Returns chambers list with the basic information data for Belarus Upper house parliament.
        url = "http://www.sovrep.gov.by/ru/sozyvy-ru/"
        soup = scrape.download_html_file(url)
        chambers = {}
        for each_li in soup.find('ul', {"class": "inner_menu"}).findAll("li"):
            url = each_li.find("a").get('href')
            term = url[-2:].replace("/", "")
            name = each_li.find('a').get_text().replace('\n', '').replace("   ", "")
            chambers[term] = {
                "name": name,
                "url": url,
                "start_date": self.terms[term]['start_date'],
                "end_date": self.terms[term]['end_date']
            }
        return chambers

    def membership_correction(self):
        # Returns the json document which can translate the belarus language membership labels to english..
        return {
            "Председатель комиссии": "chairman",
            "Заместитель председателя комиссии": "vice-chairman",
            "Председатель Совета Республики Национального собрания Республики Беларусь": "chairman",
            "Заместитель Председателя Совета Республики Национального собрания Республики Беларусь": "vice-chairman",
            "Член": "member"

        }

    def members_list(self):
        # Returns MP list with the basic information data for each member for Belarus Upper house parliament.
        terms = self.chambers_list()
        mps_list = []
        roles = self.membership_correction()
        for term in list(reversed(sorted(terms.keys()))):
            presidium = {}
            url = terms[term]['url']
            soup = scrape.download_html_file(url)
            for each_div in soup.find("div", {"id": "rukovodstvo_bm_info"}).findAll("div", {'class': "news_item news_item_second"}):
                name = each_div.find('div', {'class': "news_title"}).find('a').get_text().strip()
                names_array = name.split(" ")
                first_name_deputy = names_array[1]
                middle_name_deputy = names_array[2]
                last_name_deputy = names_array[0]
                name_ordered_deputy = first_name_deputy + " " + middle_name_deputy + " " + last_name_deputy
                name_ordered_deputy_final = name_ordered_deputy.replace("\n", "")
                membership_label = each_div.find("div", {'class': "news_text"}).get_text().encode('utf-8')
                if "Председатель Совета Республики Национального собрания Республики Беларусь" in membership_label:
                    presidium[name_ordered_deputy_final] = \
                        "Председатель Совета Республики Национального собрания Республики Беларусь"
                elif "Заместитель Председателя Совета Республики Национального собрания Республики Беларусь" in membership_label:
                    presidium[name_ordered_deputy_final] = \
                        "Заместитель Председателя Совета Республики Национального собрания Республики Беларусь"

            for each_div in soup.find("div", {"id": "members_bm_info"}).findAll("div", {'class': "news_item news_item_second"}):
                name_unordered = each_div.find('div', {'class': "news_title"}).find('a').get_text()
                member_url = each_div.find('div', {'class': "news_title"}).find('a').get("href")
                identifier = re.findall(r'\d+', member_url)
                names = name_unordered.split(" ")
                first_name = names[1]
                middle_name = names[2]
                last_name = names[0]
                name_ordered = first_name + " " + middle_name + " " + last_name
                name_ordered_final = name_ordered.replace("\n", "")
                if name_ordered_final in presidium:
                    membership = presidium[name_ordered_final].decode('utf-8')
                else:
                    membership = "Член".decode('utf-8')

                role = roles[membership.encode('utf-8')]
                if each_div.find('img'):
                    image_url = each_div.find('img').get('src')
                else:
                    image_url = ""
                if len(identifier) > 1:
                    member_id = identifier[1]
                else:
                    member_id = identifier[0]

                gender = self.guess_gender(first_name)
                members_json = {
                    "gender": gender,
                    "image_url": image_url,
                    "term": str(term),
                    "membership": membership,
                    "member_id": member_id,
                    "role": role,
                    "url": member_url,
                    "name": name_ordered,
                    "given_name": first_name,
                    "family_name": last_name,
                    "sort_name": last_name + ", " + first_name,
                }
                mps_list.append(members_json)
        return mps_list

    def guess_gender(self, first_name):
        # Returns gender of a member based on his/her first name.
        females = ["Лидия", "Лилия", "Наталия", "Наталья", "Клавдия", "Евгения", "Мария", "Софья", "Любовь"]
        if first_name[-1] == "а".decode('utf-8') or first_name.encode('utf-8') in females:
            return "female"
        else:
            return "male"

    def committe_list(self):
        # Returns the list of committee groups with basic information for each
        committee_list = []
        chambers_list = {}
        chambers_api = vpapi.getall("organizations", where={"classification": "chamber"})
        for chamber in chambers_api:
            chambers_list[chamber['identifiers'][0]['identifier']] = chamber['id']

        chambers = self.chambers_list()
        for term in chambers:
            soup = scrape.download_html_file(chambers[term]['url'])
            for each_h2 in soup.find("div", {"id": "committee_bm_info"}).findAll("h2"):
                name = each_h2.find("a").get_text()
                url = each_h2.find("a").get("href")
                start_date = chambers[term]['start_date']
                if term != "5":
                    end_date = chambers[term]['end_date']
                else:
                    end_date = None
                identifiers = re.findall(r'\d+', url)
                if len(identifiers) > 2:
                    identifier = identifiers[1]
                else:
                    identifier = identifiers[0]
                chamber_id = chambers_list[term]
                committee_json = {
                    "identifier": identifier,
                    "parent_id": chamber_id,
                    "name": name,
                    "url": url,
                    "start_date": start_date,
                    "end_date": end_date
                }
                committee_list.append(committee_json)
        return committee_list

    def committee_membership(self):
        # Returns committee groups membership list with all needed information data
        # for each member of every committee group for Belarus Upper house parliament.
        roles = self.membership_correction()
        committee_list = self.committe_list()
        committee_membership_list = []
        counter = 0
        widgets_member = ['        Progress: ', Percentage(), ' ', Bar(marker='#', left='[', right=']'),
                          ' ', ETA(), " - Processed: ", Counter(), " committees             "]
        pbar_m = ProgressBar(widgets=widgets_member)
        for committee in pbar_m(committee_list):
            soup = scrape.download_html_file(committee['url'])
            for each_div in soup.find("div", {"id": "person_bm_info"}).findAll("div", {'class': "news_item news_item_second"}):
                counter += 1
                name = each_div.find('div', {'class': "news_title"}).get_text().replace("\n", "").strip()
                if "(" in name:
                    index_start = name.index("(")
                    membership_label = name[index_start + 1:len(name) - 1]
                    name = name[:index_start].strip()
                else:
                    membership_label = "Член".decode('utf-8')
                member_url = each_div.find('div', {'class': "news_title"}).find('a').get("href")
                identifier = re.findall(r'\d+', member_url)
                if len(identifier) > 1:
                    member_id = identifier[1]
                else:
                    member_id = identifier[0]
                names = name.split(" ")
                first_name = names[1]
                middle_name = names[2]
                last_name = names[0]
                name_ordered = first_name + " " + middle_name + " " + last_name
                role = roles[membership_label.encode('utf-8')]
                committee_membership_json = {
                    "name": name_ordered.strip(),
                    "identifier": member_id,
                    "membership": membership_label,
                    "role": role,
                    "committee_parent_id": committee['parent_id'],
                    "committee_name": committee['name'],
                    "url": committee['url']
                }
                committee_membership_list.append(committee_membership_json)
        return committee_membership_list

    def mps_list(self):
        # Returns MP list with all the information needed data for each member for Belarus Upper house parliament.
        members = self.members_list()
        members_list = []
        members_prevent_duplicates = []
        widgets = ['        Progress: ', Percentage(), ' ', Bar(marker='#', left='[', right=']'),
                                   ' ', ETA(), " - Processed: ", Counter(), ' items             ']
        pbar = ProgressBar(widgets=widgets)
        for member in pbar(members):
            if member['name'] not in members_prevent_duplicates:
                members_prevent_duplicates.append(member['name'])
                soup = scrape.download_html_file(member['url'])
                personal_info_divs = soup.findAll("div", {"class": "person_text"})
                if personal_info_divs:
                    if personal_info_divs[len(personal_info_divs) - 1].find('div'):
                        for each_div in personal_info_divs[len(personal_info_divs) - 1].findAll('div'):
                            if each_div.next[:2] == "8-":
                                if "(факс)" not in each_div.next.encode('utf-8'):
                                    phone = each_div.next.strip()
                                    if len(phone) > 1:
                                        member['phone_number'] = phone
                                    else:
                                        member['phone_number'] = None
                                else:
                                    fax = each_div.next.strip()
                                    if len(fax) > 1:
                                        member['fax'] = fax.encode('utf-8').replace("(факс)", "").strip()
                                    else:
                                        member['fax'] = None
                            else:
                                member['phone_number'] = None
                                member['fax'] = None
                    else:
                        member['phone_number'] = None
                        member['fax'] = ""
                else:
                    member['phone_number'] = None
                    member['fax'] = ""

                if len(soup.find("div", {"id": "biography_bm_info"}).findAll('p')) > 0:
                    biography = soup.find("div", {"id": "biography_bm_info"}).findAll("p")
                    birth_date_paragraph = biography[0].next.encode('utf-8')
                    if re.search(r'(\d+.\d+.\d+)', birth_date_paragraph):
                        birth_date_list = biography[0].get_text().split(" - ")
                        birth_date_extract = birth_date_list[0].split(".")
                        birth_date = birth_date_extract[2] + "-" + birth_date_extract[1] + "-" + birth_date_extract[0]
                        member['birth_date'] = birth_date
                    else:
                        if "года" in birth_date_paragraph:
                            index_end = birth_date_paragraph.index("года")
                        else:
                            index_end = len(birth_date_paragraph) - 3

                        extract_birth_date = birth_date_paragraph[:index_end].replace("Родилась ", "").replace("Родился", "").strip()
                        if len(extract_birth_date) > 2:
                            birth_date_array = extract_birth_date.split(" ")
                            year = birth_date_array[2]
                            month = self.months_correction[birth_date_array[1].strip()]
                            day = birth_date_array[0]
                            if len(day) == 1:
                                day = "0" + day
                            birth_date = year + "-" + month + "-" + day
                            member['birth_date'] = birth_date
                        else:
                            member['birth_date'] = None
                else:
                    biography = soup.find("div", {"id": "biography_bm_info"}).get_text()
                    if "-" in biography:
                        biography = soup.find("div", {"id": "biography_bm_info"}).get_text()
                        birth_date_list = biography.split(" - ")
                        birth_date_extract = birth_date_list[0].split(".")
                        birth_date = birth_date_extract[2] + "-" + birth_date_extract[1] + "-" + birth_date_extract[0]
                    else:
                        biography = soup.find("div", {"id": "biography_bm_info"}).get_text()
                        birth_date_extract = biography.split(".")
                        birth_date = birth_date_extract[2] + "-" + birth_date_extract[1] + "-" + birth_date_extract[0]
                    member['birth_date'] = birth_date.replace("\n", "").replace(" ", "")
                members_list.append(member)
        return members_list


