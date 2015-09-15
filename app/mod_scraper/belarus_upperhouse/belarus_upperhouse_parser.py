# -*- coding: utf-8 -*-
from app.mod_scraper import scraper
import re
import vpapi


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

    def chambers_list(self):
        url = "http://www.sovrep.gov.by/ru/sozyvy-ru/"
        soup = scrape.download_html_file(url)
        chambers = {}
        for each_li in soup.find('ul', {"class": "inner_menu"}).findAll("li"):
            url = each_li.find("a").get('href')
            term = url[-2:].replace("/", "")
            name = each_li.find('a').get_text().replace('\n', '').replace("   ", "")
            chambers[term] = {
                "name": name,
                "url": url
            }
        return chambers

    def membership_correction(self):
        return {
            "Председатель Совета Республики Национального собрания Республики Беларусь": "chairman",
            "Заместитель Председателя Совета Республики Национального собрания Республики Беларусь": "vice-chairman",
            "Член": "member"

        }

    def members_list(self):
        terms = self.chambers_list()
        mps_list = []
        roles = self.membership_correction()
        counter = 0
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
                counter += 1
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

                gender = self.guess_gender(first_name)
                members_json = {
                    "gender": gender,
                    "image_url": image_url,
                    "term": str(term),
                    "membership": membership,
                    "member_id": identifier[0],
                    "role": role,
                    "url": member_url,
                    "name": name_ordered,
                    "given_name": first_name,
                    "family_name": last_name,
                    "sort_name": last_name + ", " + first_name,
                }
                mps_list.append(members_json)
        print "\t%s Members scraped" % str(counter)
        return mps_list

    def guess_gender(self, first_name):
        females = ["Лидия", "Лилия", "Наталия", "Наталья", "Клавдия", "Евгения", "Мария", "Софья", "Любовь"]
        if first_name[-1] == "а".decode('utf-8') or first_name.encode('utf-8') in females:
            return "female"
        else:
            return "male"

    def mps_list(self):
        members = self.members_list()
        members_list = []
        members_prevent_duplicates = []
        for member in members:
            if member['name'] not in members_prevent_duplicates:
                print member['member_id'] + '\n'
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
                                        member['phone_number'] = ""
                                else:
                                    fax = each_div.next.strip()
                                    if len(fax) > 1:
                                        member['fax'] = fax
                                    else:
                                        member['fax'] = ""
                    else:
                        member['phone_number'] = ""
                        member['fax'] = ""

                if len(soup.find("div", {"id": "biography_bm_info"}).findAll('p')) > 0:
                    biography = soup.find("div", {"id": "biography_bm_info"}).findAll("p")
                    birth_date_paragraph = biography[0].next.encode('utf-8')
                    if "73" in member['member_id']:
                        birth_date_list = birth_date_paragraph.split(" - ")
                        birth_date_extract = birth_date_list[0].split(".")
                        birth_date = birth_date_extract[2] + "-" + birth_date_extract[1] + "-" + birth_date_extract[0]
                        birth_date = birth_date.replace("\n", "").replace(" ", "")
                        member['birth_date'] = birth_date

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
                        member['birth_date'] = ""
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
                print member['given_name']
                print member['gender']
                print member['url']
                print "------------------------------------------"

                members_list.append(member)
        return members_list


