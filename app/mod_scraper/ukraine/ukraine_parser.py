# -*- coding: utf-8 -*-
from app.mod_scraper import scraper
import sys
from bs4 import BeautifulSoup
import requests
import pprint
import re
import vpapi
from progressbar import ProgressBar, Percentage, ETA, Counter, Bar

scrape = scraper.Scraper()


class UkraineParser():
    months = {
        "січня": "01",
        "лютого": "02",
        "березня": "03",
        "квітня": "04",
        "травня": "05",
        "червня": "06",
        "липня": "07,",
        "серпня": "08",
        "вересня": "09",
        "жовтня": "10",
        "листопада": "11",
        "грудня": "12"
    }

    def download_html_file(self, url, encoding_type=None):
        response = requests.get(url)
        if encoding_type:
            response.encoding = "utf-8"
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup

    def chambers(self):
        chambers = {
            "9": {
                "url": "http://w1.c1.rada.gov.ua/pls/site2/p_deputat_list?skl=9",
                "name": "IX скликання (2014-)",
                "start_date": "2014",
                "end_date": ""
            }
        }
        url = "http://w1.c1.rada.gov.ua/pls/site2/p_deputat_list"
        soup = self.download_html_file(url)
        for each_li in soup.find("div", {"class": "col-half col-last"}).find('ul').findAll("li"):
            name = each_li.find('a').get_text()
            url = each_li.find('a').get("href")
            if ".htm" in url:
                identifier = url.replace(".htm", "")[-1:]
            else:
                identifier = url[-1:]

            index_start = name.index("(") + 1
            index_end = name.index(")")
            years = name[index_start:index_end].split("-")
            start_date = years[0]
            end_date = years[1]
            chambers[identifier] = {
                "url": url,
                "name": name,
                "start_date": start_date,
                "end_date": end_date
            }
        return chambers

    def build_ordered_name(self, name):
        encoded_name = name.encode('utf-8')
        names = encoded_name.split(" ")
        first_name = names[1]
        middle_name = names[2]
        last_name = names[0]
        return first_name + " " + middle_name + " " + last_name

    def chamber_mps_list(self, term):
        chamber_mps = []
        url = "http://w1.c1.rada.gov.ua/pls/radan_gs09/d_index_arh?skl=%s" % term
        soup = self.download_html_file(url)
        for each_td in soup.findAll('td'):
            if each_td.has_attr("width") or each_td.has_attr('colspan') or each_td.has_attr("valign"):
                continue
            else:
                name = each_td.get_text()
                member_url = "http://w1.c1.rada.gov.ua" + each_td.find('a').get('href')
                index_start = member_url.index("kod=") + 4
                identifier = member_url[index_start:]
                names = name.split(" ")
                first_name = names[1]
                middle_name = names[2]
                last_name = names[0]
                name_ordered = first_name + " " + middle_name + " " + last_name
                gender = self.guess_gender(first_name)
                membership = "член".decode('utf-8')
                role = "member"
                member_json = {
                    "member_id": identifier,
                    "membership": membership,
                    "role": role,
                    "term": term,
                    "name": name_ordered,
                    "given_name": first_name,
                    "family_name": last_name,
                    "sort_name": last_name + ", " + first_name,
                    "url": member_url,
                    "gender": gender
                }
                chamber_mps.append(member_json)
        return chamber_mps

    def first_chamber_mps_list(self):
        first_chamber_mps = []
        url = "http://static.rada.gov.ua/zakon/new/NEWSAIT/DEPUTAT1/spisok1.htm"
        soup = self.download_html_file(url, "utf-8")
        for each_div in soup.findAll('div', {"class": "topTitle"})[1:]:
            if each_div.find("table"):
                all_tr_elements = each_div.find("table").findAll('tr')
                for each_tr in all_tr_elements[1:len(all_tr_elements)-1]:
                    all_td_elements = each_tr.findAll('td')
                    name = all_td_elements[0].find("p").find('a').get_text().replace("\n", "").replace("                   ", " ")
                    names = name.split(" ")
                    first_name = names[1]
                    middle_name = names[2]
                    last_name = names[0]
                    name_ordered = first_name + " " + middle_name + " " + last_name
                    url_member = "http://static.rada.gov.ua/zakon/new/NEWSAIT/DEPUTAT1/" + \
                          all_td_elements[0].find("p").find('a').get("href")
                    index_start = url_member.index("TAT1/") + 5
                    index_end = url_member.index(".htm")
                    identifier = url_member[index_start:index_end]
                    gender = self.guess_gender(first_name)
                    membership = "член".decode('utf-8')
                    role = "member"
                    member_json = {
                        "member_id": identifier,
                        "membership": membership,
                        "role": role,
                        "term": "1",
                        "name": name_ordered,
                        "given_name": first_name,
                        "family_name": last_name,
                        "sort_name": last_name + ", " + first_name,
                        "url": url_member,
                        "gender": gender
                    }
                    first_chamber_mps.append(member_json)
        return first_chamber_mps

    def guess_gender(self, name):
        males = ["Микола"]
        if name[-1] == "а".decode('utf-8') and name.encode('utf-8') not in males:
            return "female"
        elif name[-1] == "я".decode('utf-8'):
            return "female"
        else:
            return "male"

    def parliamentary_group_list(self):
        chamber_ids = {}
        all_chambers = vpapi.getall("organizations", where={"classification": "chamber"})
        for term in all_chambers:
            chamber_ids[term['identifiers'][0]['identifier']] = term['id']
        parties = []
        chambers = self.chambers()
        for i in range(6, int(max(chambers.keys())) + 1):
            url = "http://w1.c1.rada.gov.ua/pls/site2/p_fractions?skl=%s" % str(i)
            soup = self.download_html_file(url)
            for each_tr in soup.find('table', {'class': "striped Centered"}).findAll("tr")[1:]:
                all_td_elements = each_tr.findAll("td")
                if len(all_td_elements) > 1:
                    url = "http://w1.c1.rada.gov.ua/pls/site2/" + all_td_elements[0].find("a").get('href')
                    name = all_td_elements[0].find("a").get_text()
                    if "pidid=" in url:
                        index_start = url.index("pidid=") + 6
                    else:
                        index_start = None
                    if index_start:
                        identifier = url[index_start:]
                    else:
                        identifier = "0"
                    party_json = {
                        "name": name,
                        "url": url,
                        "identifier": identifier,
                        "parent_id": chamber_ids[str(i)]
                    }
                    parties.append(party_json)
                else:
                    continue
        return parties

    def parliamentary_groups(self):
        parties_list = self.parliamentary_group_list()
        for party in parties_list:
            soup = self.download_html_file(party['url'])
            all_p_tags = soup.find('div', {"class": "information_block_ins"}).findAll("p")
            if int(party['identifier']) > 6:



    def members_list(self):
        mp_list = self.mps_list()
        members_prevent_duplicates = []
        members = []
        widgets = ['        Progress: ', Percentage(), ' ', Bar(marker='#', left='[', right=']'),
                   ' ', ETA(), " - Processed: ", Counter(), ' items             ']
        pbar = ProgressBar(widgets=widgets)
        for member in pbar(mp_list):
            if member['name'] not in members_prevent_duplicates:
                members_prevent_duplicates.append(member['name'])
                if int(member['term']) >= 5:
                    soup = self.download_html_file(member['url'])
                    table_infos = soup.findAll("table", {"class": "simple_info"})
                    birth_date_trs = table_infos[1].findAll('tr')
                    birth_date_tds = birth_date_trs[0].findAll('td')
                    if len(birth_date_tds) > 1:
                        birth_date_text = birth_date_tds[1].get_text()
                        extract_birth_date = birth_date_text[:len(birth_date_text) - 2]
                        birth_date_array = extract_birth_date.split(" ")
                        month = self.months[birth_date_array[1].strip().encode('utf-8')]
                        day = birth_date_array[0]
                        if len(day) == 1:
                            day = "0" + day
                        birth_date = birth_date_array[2] + "-" + month + "-" + day
                        member["birth_date"] = birth_date.replace(",", "")
                    else:
                        member['birth_date'] = None
                    email_divs = soup.findAll("div", {"class": "topTitle"})
                    if len(email_divs) > 1:
                        if email_divs[1].find("a"):
                            email = email_divs[1].find("a").get_text().strip()
                            member["email"] = email
                        else:
                            member['email'] = None
                    else:
                        member['email'] = None
                else:
                    soup = self.download_html_file(member['url'])
                    image_url = soup.find("img", {'width': "120"}).get("src")
                    if "http://static.rada.gov.ua" not in image_url:
                        image_url = "http://static.rada.gov.ua" + image_url
                    member["image_url"] = image_url
                    member["birth_date"] = None
                    member["email"] = None
                members.append(member)
        return members

    def chamber_membership(self):
        membership = {}
        chambers = self.chambers()
        for term in list(reversed(sorted(chambers)))[:5]:
            membership[str(term)] = {}
            url = "http://w1.c1.rada.gov.ua/pls/site2/p_ex_kerivnyky_vru?skl=%s" % term
            soup = self.download_html_file(url)
            for each_div in soup.findAll('div', {"class": "person"}):
                name = each_div.find('h2').find('a').get_text()
                membership_text = each_div.get_text().replace(name, "").replace('\n', "")
                index_start = membership_text.index("(")
                membership_label = membership_text[:index_start].strip()
                names = name.split(" ")
                first_name = names[1]
                middle_name = names[2]
                last_name = names[0]
                name_ordered = first_name + " " + middle_name + " " + last_name
                membership[str(term)][name_ordered] = ""
                membership[str(term)][name_ordered] = membership_label
        return membership

    def membership_correction(self):
        return {
            "Голова Верховної Ради України": "chairman",
            "Перший заступник Голови Верховної Ради України": "first-vice-chairman",
            "Заступник Голови Верховної Ради України": "vice-chairman",
            "член": "member"
        }

    def mps_list(self):
        roles = self.membership_correction()
        memberships = self.chamber_membership()
        chambers = self.chambers()
        guess_gender = {
            "1": "male",
            "2": "female"
        }
        mps_list = []
        counter = 0
        for term in list(reversed(sorted(chambers))):
            if int(term) >= 5:
                for i in range(1, 3):
                    url = "http://w1.c1.rada.gov.ua/pls/site2/fetch_mps?skl_id=%s&gender=%s" % (term, str(i))
                    soup = self.download_html_file(url)
                    for each_li in soup.find("ul", {"class": "search-filter-results search-filter-results-thumbnails"}).findAll("li"):
                        counter += 1
                        image_url = each_li.find("p", {"class": "thumbnail"}).find("img").get('src')
                        member_url = each_li.find("p", {"class": "title"}).find("a").get('href')
                        index_start = member_url.index("page/") + 5
                        identifier = member_url[index_start:]
                        name = each_li.find("p", {"class": "title"}).find("a").get_text()
                        names = name.split(" ")
                        first_name = names[1]
                        middle_name = names[2]
                        last_name = names[0]
                        name_ordered = first_name + " " + middle_name + " " + last_name
                        gender = guess_gender[str(i)]
                        if name_ordered in memberships[term]:
                            membership = memberships[term][name_ordered]
                        else:
                            membership = "член".decode('utf-8')

                        role = roles[membership.encode('utf-8')]
                        member_json = {
                            "member_id": identifier,
                            "membership": membership,
                            "role": role,
                            "term": str(term),
                            "name": name_ordered,
                            "given_name": first_name,
                            "family_name": last_name,
                            "sort_name": last_name + ", " + first_name,
                            "url": member_url,
                            "gender": gender,
                            "image_url": image_url
                        }
                        mps_list.append(member_json)
            elif int(term) <= 4:
                if int(term) > 1:
                    mp_list = self.chamber_mps_list(term)
                    mps_list += mp_list
                else:
                    first_chambers_mps = self.first_chamber_mps_list()
                    mps_list += first_chambers_mps
        return mps_list