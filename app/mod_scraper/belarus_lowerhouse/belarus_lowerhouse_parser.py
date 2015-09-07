# -*- coding: utf-8 -*-
from app.mod_scraper import scraper


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
        if name[:-1] == "а":
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
            print first_name[-1]
            gender = self.guess_gender(first_name)
            print gender
            print "--------------------"
            member_json = {
                "name": name_ordered,
                "given_name": first_name,
                "family_name": last_name,
                "sort_name": last_name + ", " + first_name,
                "identifier": identifier,
                "url": url_member
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
                    email_fixed_1 = email.replace("  ", "").replace(" ", "")
                    email_length = len(email_fixed_1)
                    # print "email: " + email_fixed_1.strip()
                    if 2 < email_length < 36:
                        member['email'] = email_fixed_1.strip()
                    else:
                        member['email'] = ""
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
                        member['birth_date'] = ""
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
                        mps_list[member]['birth_date'] = ""
            members.append(member)
        print "\n\tScraping completed! \n\tScraped " + str(len(members)) + " members"
        return members