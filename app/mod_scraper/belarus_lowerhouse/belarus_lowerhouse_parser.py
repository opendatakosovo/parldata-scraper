# -*- coding: utf-8 -*-
from app.mod_scraper import scraper
import vpapi


scrape = scraper.Scraper()


class BelarusLowerhouseParser():
    months_correction = {
        "студзеня": "01",
        "лютага": "02",
        "сакавіка": "03",
        "Красавік": "04",
        "красавіка": "04",
        "мая": "05",
        "чэрвеня": "06",
        "ліпеня": "07",
        "жніўня": "08",
        "верасня": "09",
        "кастрычніка": "10",
        "лістапада": "11",
        "снежня": "12"
    }

    def guess_gender(self, name):
        females = ["Наталля"]
        if name[-1] == "а".decode('utf-8') or name.encode('utf-8') in females:
            return "female"
        else:
            return "male"

    def mps_list(self):
        members_list = []
        url = "http://house.gov.by/index.php/,17041,,,,2,,,0.html"
        soup = scrape.download_html_file(url)
        # print soup.findAll('a', {'class': 'd_list'})
        counter = 0
        for each_tr in soup.findAll('a', {'class': 'd_list'}):
            counter += 1
            name_unordered = each_tr.get_text()
            names = name_unordered.split(" ")
            first_name = names[1]
            middle_name = names[2]
            last_name = names[0]
            name_ordered = first_name + " " + middle_name + " " + last_name
            url_member = each_tr.get('href')
            index_start = url_member.index('041,') + 4
            index_end = url_member.index(',,,2')
            identifier = url_member[index_start:index_end]
            gender = self.guess_gender(first_name)
            member_json = {
                "name": name_ordered,
                "given_name": first_name,
                "family_name": last_name,
                "sort_name": last_name + ", " + first_name,
                "identifier": identifier,
                "url": url_member,
                "gender": gender
            }
            members_list.append(member_json)
        return members_list

    def mp(self):
        print "\n\tScraping people data from Belarus Lower House parliament..."
        print "\tPlease wait. This may take a few minutes..."
        mps_list = self.mps_list()
        members = []
        for member in mps_list:
            soup = scrape.download_html_file(member['url'])
            image_url = "http://house.gov.by/" + soup.find("table", {"cellspacing": "1"}).find('img').get('src')
            member['image_url'] = image_url
            for each_p in soup.find("td", {"style": "padding: 20px;"}).findAll("p"):
                encoded_p_tag = each_p.get_text().encode('utf-8')
                if "E-mail" in encoded_p_tag:
                    email = encoded_p_tag.replace("E-mail:", "").strip()
                    email_fixed_1 = email.replace("\xc2\xa0", "")
                    email_length = len(email_fixed_1)
                    if 2 < email_length < 36:
                        member['email'] = email_fixed_1
                    else:
                        member['email'] = None
                if "Нарадзіўся" in encoded_p_tag:
                    birth_date_text = encoded_p_tag.replace("Нарадзіўся ", "").strip()
                    index_end = birth_date_text.index('года') - 1
                    extract_birth_date = birth_date_text[:index_end]
                    if len(extract_birth_date) > 0:
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
                elif "Нарадзілася" in encoded_p_tag:
                    birth_date_text = encoded_p_tag.replace("Нарадзілася ", "").strip()
                    index_end = birth_date_text.index('года') - 1
                    extract_birth_date = birth_date_text[:index_end]
                    if len(extract_birth_date) > 0:
                        birth_date_array = extract_birth_date.split(" ")
                        year = birth_date_array[2]
                        month = self.months_correction[birth_date_array[1].strip()]
                        day = birth_date_array[0]
                        if len(day) == 1:
                            day = "0" + day
                        birth_date = year + "-" + month + "-" + day
                        member['birth_date'] = birth_date
                    else:
                        mps_list[member]['birth_date'] = None
            members.append(member)
        print "\n\tScraping completed! \n\tScraped " + str(len(members)) + " members"
        return members

    def chambers(self):
        return {
            "1": {
                "start_date": "1919",
                "end_date": "1990",
                "name": "I этап — савецкі (1919 год — канец 80-х — пачатак 90-х гадоў)"
            },
            "2": {
                "start_date": "1991",
                "end_date": "",
                "name": "II этап — постсавецкі (1991 год — цяперашні час)"
            }
        }

    def committee_list(self):
        url = "http://house.gov.by/index.php/,17052,,,,2,,,0.html"
        soup = scrape.download_html_file(url)
        committees = []
        chamber = vpapi.getfirst("organizations", where={'identifiers': {'$elemMatch': {"identifier": "2", "scheme": "house.by"}}})
        for each_div in soup.findAll('div', {"style": "margin-left:0px; padding-bottom: 1px;"}):
            name = each_div.find('a').get_text().strip()
            url = each_div.find('a').get('href')
            index_start = url.index("/,") + 2
            index_end = url.index(",,,,2")
            identifier = url[index_start:index_end]
            committee_json = {
                "name": name,
                "url": url,
                "identifier": identifier,
                "parent_id": chamber['id']
            }
            committees.append(committee_json)
        return committees

    def committees(self):
        committee_list = self.committee_list()
        committees = []
        for committee in committee_list:
            identifier = int(committee['identifier']) + 2
            url = committee['url'].replace(committee['identifier'], str(identifier))
            soup = scrape.download_html_file(url)
            all_tr = soup.find("table", {"cellpadding": "2"}).findAll('tr')
            phone_number_tr = all_tr[len(all_tr) - 1].findAll('td')
            phone_number = phone_number_tr[1].get_text().encode('utf-8')
            phone_number_fixed_1 = phone_number.replace("тэл./факс", "").replace("тэл.            222-63-98", "").strip()
            phone_number_fixed_2 = phone_number_fixed_1.replace("\xc2\xa0", "")
            phone_number_final = phone_number_fixed_2.replace(" ", "")
            committee['phone_number'] = phone_number_final
            committee['members_url'] = url
            committees.append(committee)
        return committees

    def parliamentary_groups(self):
        url = "http://house.gov.by/index.php/,17543,,,,2,,,0.html"
        index_start = url.index("/,") + 2
        index_end = url.index(",,,,2")
        identifier = url[index_start:index_end]
        chamber = vpapi.getfirst("organizations", where={'identifiers': {'$elemMatch': {"identifier": "2", "scheme": "house.by"}}})
        soup = scrape.download_html_file(url)
        party_name = soup.find('h1').get_text()
        party_json = {
            "name": party_name,
            "url": url,
            "identifier": identifier,
            "parent_id": chamber['id']
        }
        return party_json