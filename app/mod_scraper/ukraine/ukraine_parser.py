# -*- coding: utf-8 -*-
from app.mod_scraper import scraper
from bs4 import BeautifulSoup
from progressbar import ProgressBar, Percentage, ETA, Counter, Bar
import dateutil.parser as dparser
from datetime import datetime
from operator import itemgetter
import requests
import pprint
import urlparse
import re
import vpapi
import dateutil.parser
from time import sleep
import sys

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
        try:
            while True:
                response = requests.get(url)
                if response.status_code == 200:
                    soup = self.get_response_from_url(response, encoding_type)
                    break
                elif response.status_code == 301:
                    response = requests.get(url)
                    soup = self.get_response_from_url(response, encoding_type)
                    break
                else:
                    print "Connection timeout"
        except Exception as ex:
            print ex.message

        return soup

    def get_response_from_url(self, response, encoding_type=None ):
        if encoding_type:
            response.encoding = "utf-8"
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')
        return soup

    def local_to_utc(self, dt_str):
        dt = dateutil.parser.parse(dt_str, dayfirst=True)
        if ':' in dt_str:
            return vpapi.local_to_utc(dt, to_string=True)
        else:
            return dt.strftime('%Y-%m-%d')

    def chambers(self):
        chambers = {
            "9": {
                "url": "http://w1.c1.rada.gov.ua/pls/site2/p_deputat_list?skl=9",
                "name": "VIII скликання (2014-)",
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

    def committee_list(self):
        chamber_ids = {}
        all_chambers = vpapi.getall("organizations", where={"classification": "chamber"})
        for term in all_chambers:
            chamber_ids[term['identifiers'][0]['identifier']] = term['id']
        committees = []
        chambers = self.chambers()
        for i in range(7, int(max(chambers.keys())) + 1):
            url = "http://w1.c1.rada.gov.ua/pls/site2/p_komitis?skl=%s" % str(i)
            soup = self.download_html_file(url)
            for each_tr in soup.find('table', {'class': "striped Centered"}).findAll("tr")[1:]:
                all_td_elements = each_tr.findAll("td")
                if len(all_td_elements) > 1:
                    url = "http://w1.c1.rada.gov.ua/pls/site2/" + all_td_elements[0].find("a").get('href')
                    name = all_td_elements[0].find("a").get_text()
                    if name.encode('utf-8') != "Народні депутати, які не входять до складу жодного комітету":
                        if "pidid=" in url:
                            index_start = url.index("pidid=") + 6
                        else:
                            index_start = None
                        if index_start:
                            identifier = url[index_start:]
                        else:
                            identifier = "0"
                        party_json = {
                            "term": str(i),
                            "name": name,
                            "url": url,
                            "identifier": identifier,
                            "parent_id": chamber_ids[str(i)]
                        }
                        committees.append(party_json)
                else:
                    continue
        return committees

    def committees(self):
        committee_list = self.committee_list()
        committees = []
        widgets = ['        Progress: ', Percentage(), ' ', Bar(marker='#', left='[', right=']'),
                   ' ', ETA(), " - Processed: ", Counter(), ' items             ']
        pbar = ProgressBar(widgets=widgets)
        for committee in pbar(committee_list):
            soup = self.download_html_file(committee['url'])
            info_tables = soup.findAll('table', {'class': "simple_info"})
            all_tr_tags = info_tables[0].findAll('tr')
            all_td_tags_start_date = all_tr_tags[0].findAll('td')
            start_date_text = all_td_tags_start_date[1].next
            start_date = start_date_text.encode('utf-8').strip()
            start_date_array = start_date.replace("р.", "").split(" ")
            start_date_str = start_date_array[2] + "-" + self.months[start_date_array[1]]\
                             + "-" + start_date_array[0]
            committee['start_date'] = start_date_str
            if committee['term'] != "9":
                all_td_tags_end_date = all_tr_tags[3].findAll('td')
                end_date_text = all_td_tags_end_date[1].next
                end_date = end_date_text.encode('utf-8').strip()
                end_date_array = end_date.replace("р.", "").split(" ")
                end_date_str = end_date_array[2] + "-" + self.months[end_date_array[1]]\
                                 + "-" + end_date_array[0]
                committee['end_date'] = end_date_str
            else:
                committee['end_date'] = None
            committees.append(committee)
        return committees

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
                        "term": str(i),
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
        parties = []
        widgets = ['        Progress: ', Percentage(), ' ', Bar(marker='#', left='[', right=']'),
                   ' ', ETA(), " - Processed: ", Counter(), ' items             ']
        pbar = ProgressBar(widgets=widgets)
        for party in pbar(parties_list):
            soup = self.download_html_file(party['url'])
            all_divs = soup.findAll('div', {"class": "information_block_ins"})
            all_p_tags = all_divs[1].findAll("p")
            if party['term'] != "9":
                if party['identifier'] != "0":
                    start_date_text = all_p_tags[0].get_text()
                    start_date = start_date_text.encode('utf-8').replace("Дата створення: ", "")[:len(start_date_text) - 2].strip()
                    start_date_array = start_date.replace("р.", "").split(" ")
                    start_date_str = start_date_array[2] + "-" + self.months[start_date_array[1]]\
                                     + "-" + start_date_array[0]
                    party['start_date'] = start_date_str

                    end_date_text = all_p_tags[1].get_text()
                    end_date = end_date_text.encode('utf-8').replace("Дата розпуску: ", "")[:len(end_date_text) - 2].strip()
                    end_date_array = end_date.replace("р.", "").split(" ")
                    end_date_str = end_date_array[2] + "-" + self.months[end_date_array[1]]\
                                     + "-" + end_date_array[0]

                    party['end_date'] = end_date_str
                else:
                    party['start_date'] = None
                    party['end_date'] = None
            else:
                if party['identifier'] != "0":
                    start_date_text = all_p_tags[0].get_text()
                    start_date = start_date_text.encode('utf-8').replace("Дата створення:", "")[:len(start_date_text) - 2].strip()
                    start_date_array = start_date.replace("р.", "").split(" ")
                    start_date_str = start_date_array[2] + "-" + self.months[start_date_array[1]]\
                                     + "-" + start_date_array[0]
                    party['start_date'] = start_date_str
                    party['end_date'] = None
                else:
                    party['start_date'] = None
                    party['end_date'] = None
            parties.append(party)
        return parties

    def build_ordered_name(self, name):
        names = name.split(" ")
        first_name = names[1]
        middle_name = names[2]
        last_name = names[0]
        name_ordered = first_name + " " + middle_name + " " + last_name
        return name_ordered

    def build_date_str(self, date_text):
        date_list = date_text.split(".")
        date_str = date_list[2] + "-" + date_list[1] + "-" + date_list[0]
        return date_str

    def scrape_parties_members(self, party, soup, all_p_tags, item_index, parties, member_ids, roles):
        membership_array = []
        if party['identifier'] != "0":
            members = {}
            for each_div in soup.findAll('div', {"class": "ker_list"}):
                membership = each_div.find('div', {"class": "ker_title"}).get_text()
                for each_li in each_div.find('ul').findAll("li"):
                    name = each_li.find('a').get_text()
                    name_ordered = self.build_ordered_name(name)
                    members[name_ordered] = membership[:len(membership) - 2]
            url = "http://w1.c1.rada.gov.ua/pls/site2/" + all_p_tags[item_index].find('a').get('href')
            soup_members = self.download_html_file(url)
            for each_tr in soup_members.find('table', {"class": "striped Centered"}).findAll('tr')[1:]:
                td_tags = each_tr.findAll('td')
                name = td_tags[0].find('a').get_text()
                start_date_text = td_tags[1].get_text().strip()
                end_date_text = td_tags[2].get_text().strip()
                if start_date_text != "-":
                    start_date = self.build_date_str(start_date_text)
                else:
                    start_date = None

                if end_date_text != "-":
                    end_date = self.build_date_str(end_date_text)
                else:
                    end_date = None

                name_ordered = self.build_ordered_name(name)
                if name_ordered in members:
                    membership_label = members[name_ordered]
                else:
                    membership_label = "член".decode('utf-8')

                if membership_label in roles:
                    role = roles[membership_label.encode('utf-8')]
                else:
                    role = None

                o_id = parties[party['identifier']]

                if name_ordered in member_ids:
                    p_id = member_ids[name_ordered]
                else:
                    p_id = None

                if o_id and p_id:
                    membership_json = {
                        "role": role,
                        "url": url,
                        "person_id": p_id,
                        "membership": membership_label,
                        "start_date": start_date,
                        "end_date": end_date,
                        "organization_id": o_id
                    }
                    membership_array.append(membership_json)
        else:
            for each_li in soup.find('ul', {"class": "level1"}).findAll('li'):
                name = each_li.find('a').get_text()
                membership_label = "член".decode('utf-8')
                if membership_label.encode('utf-8') in roles:
                    role = roles[membership_label.encode('utf-8')]
                else:
                    role = None

                name_ordered = self.build_ordered_name(name)
                if name_ordered in member_ids:
                    p_id = member_ids[name_ordered]
                else:
                    p_id = None

                o_id = "0_" + party['term']
                organization_id = parties[o_id]
                if o_id and p_id:
                    membership_json = {
                        "role": role,
                        "url": party['url'],
                        "person_id": p_id,
                        "membership": membership_label,
                        "start_date": None,
                        "end_date": None,
                        "organization_id": organization_id
                    }
                    membership_array.append(membership_json)
        return membership_array

    def committee_members(self, url, member_ids, committee_ids, roles, identifier):
        committee_members = []
        soup = self.download_html_file(url)
        for each_tr in soup.find('table', {"class": "striped Centered"}).findAll('tr'):
            all_td_tags = each_tr.findAll('td')
            name = all_td_tags[0].find('a').get_text()
            ordered_name = self.build_ordered_name(name)
            membership_label = all_td_tags[1].get_text()
            if ordered_name in member_ids:
                p_id = member_ids[ordered_name]
            else:
                p_id = None

            if membership_label in roles:
                role = roles[membership_label.encode('utf-8')]
            else:
                role = None
            o_id = committee_ids[identifier]
            if p_id and o_id:
                committee_membership_json = {
                    "person_id": p_id,
                    "organization_id": o_id,
                    "url": url,
                    "membership": membership_label,
                    "role": role,
                }
                committee_members.append(committee_membership_json)
        return committee_members

    def committee_membership(self):
        member_ids = {}
        roles = self.membership_correction()
        all_members = vpapi.getall("people")
        for member in all_members:
            member_ids[member['name']] = member['id']

        committees_ids = {}
        all_committees = vpapi.getall("organizations", where={'classification': "committe"})
        for committe in all_committees:
            committees_ids[committe['identifiers'][0]['identifier']] = committe['id']

        committee_membership_list = []
        committee_list = self.committee_list()
        widgets = ['        Progress: ', Percentage(), ' ', Bar(marker='#', left='[', right=']'),
                   ' ', ETA(), " - Processed members from: ", Counter(), ' committees             ']
        pbar = ProgressBar(widgets=widgets)
        for committee in pbar(committee_list):
            soup = self.download_html_file(committee['url'])
            info_tables = soup.findAll('table', {"class": "simple_info"})
            if committee['term'] != "9":
                all_tr_tags = info_tables[0].findAll('tr')
                members_url = "http://w1.c1.rada.gov.ua/pls/site2/" + all_tr_tags[4].find('a').get('href')
                members = self.committee_members(members_url, member_ids, committees_ids,
                                                 roles, committee['identifier'])
                committee_membership_list += members
            else:
                all_tr_tags = info_tables[0].findAll('tr')
                members_url = "http://w1.c1.rada.gov.ua/pls/site2/" + all_tr_tags[3].find('a').get('href')
                members = self.committee_members(members_url, member_ids, committees_ids,
                                                 roles, committee['identifier'])
                committee_membership_list += members
        return committee_membership_list

    def parliamentary_group_membership(self):
        member_ids = {}
        roles = self.membership_correction()
        all_members = vpapi.getall("people")
        for member in all_members:
            member_ids[member['name']] = member['id']

        chambers = {}
        all_chambers = vpapi.getall("organizations", where={'classification': "chamber"})
        for chamber in all_chambers:
            chambers[chamber['id']] = chamber['identifiers'][0]['identifier']

        parties_ids = {}
        all_parties = vpapi.getall("organizations", where={'classification': 'parliamentary group'})
        for parti in all_parties:
            if parti['identifiers'][0]['identifier'] == "0":
                parties_ids[parti['identifiers'][0]['identifier'] + "_" + chambers[parti['parent_id']]] = parti['id']
            else:
                parties_ids[parti['identifiers'][0]['identifier']] = parti['id']
        parties = self.parliamentary_group_list()
        parties_membership = []
        widgets = ['        Progress: ', Percentage(), ' ', Bar(marker='#', left='[', right=']'),
                   ' ', ETA(), " - Processed members from: ", Counter(), ' parties             ']
        pbar = ProgressBar(widgets=widgets)
        for party in pbar(parties):
            soup = self.download_html_file(party['url'])
            all_divs = soup.findAll('div', {"class": "information_block_ins"})
            all_p_tags = all_divs[1].findAll("p")
            if party['term'] != "9":
                membership_array = self.scrape_parties_members(party, soup, all_p_tags, 4,
                                                               parties_ids, member_ids, roles)
                parties_membership += membership_array
            else:
                membership_array = self.scrape_parties_members(party, soup, all_p_tags, 3,
                                                               parties_ids, member_ids, roles)
                parties_membership += membership_array
        return parties_membership

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

    def find_start_end_time(self, all_b_tags, date, index_start):
        max_min_json = {}
        timestamps_array = []
        for b_tag in all_b_tags[index_start:]:
            time_text = b_tag.get_text().replace('\n', "")
            if "-" in time_text:
                time_list = time_text.split("-")
                if len(time_list) > 1 and len(time_list[1]) > 0:
                    if time_list[0] != "00:00:00" and time_list[1] != "00:00:00" and time_list[1] != "...":
                        time1 = datetime.strptime(date + " " + time_list[0], "%Y-%m-%d %H:%M:%S")
                        time2 = datetime.strptime(date + " " + time_list[1], "%Y-%m-%d %H:%M:%S")
                        timestamps_array.append(time1)
                        timestamps_array.append(time2)
                else:
                    if time_list[0] != "00:00:00" and time_list[0] != "...":
                        time1 = datetime.strptime(date + " " + time_list[0], "%Y-%m-%d %H:%M:%S")
                        timestamps_array.append(time1)
            else:
                if time_text != "00:00:00" and time_text != "...":
                    time1 = datetime.strptime(date + " " + time_text, "%Y-%m-%d %H:%M:%S")
                    timestamps_array.append(time1)
        if len(timestamps_array) == 0:
            time1 = datetime.strptime(date + " 00:00:00", "%Y-%m-%d %H:%M:%S")
            timestamps_array.append(time1)
        max_min_json['max'] = str(max(timestamps_array))
        max_min_json['min'] = str(min(timestamps_array))
        return max_min_json

    def split_vote_count(self, separator, vote_text):
        vote_list = vote_text.split(separator)
        return vote_list[1]

    def build_date_time_str(self, date_text):
        date_time_list = date_text.split(" ")
        date = date_time_list[0]
        time = date_time_list[1]
        date_list = date.split('.')
        date_str = date_list[2] + "-" + date_list[1] + "-" + date_list[0]
        date_time_str = date_str + "T" + time.strip()
        if len(date_time_str) < 20:
            date_time_str += ":00"
        return str(date_time_str)

    def build_json_motion(self, date_text, url, motion_id, event_id, organization_id, name, result, yes_counts,
                          no_counts, abstain_counts, absent_counts):
        json_doc = {
            "date": self.build_date_time_str(date_text),
            "start_date": self.build_date_time_str(date_text),
            "sources": [{
                "url": url,
                "note": "веб-сайт"
            }],
            "id": motion_id,
            "identifier": motion_id,
            "legislative_session_id": event_id,
            "motion_id": motion_id,
            "organization_id": organization_id,
            "text": name,
            "result": result,
            "counts": [
                {
                    "option": "yes",
                    "value": yes_counts
                },
                {
                    "option": "no",
                    "value": no_counts
                },
                {
                    "option": "abstain",
                    "value": abstain_counts
                },
                {
                    "option": "absent",
                    "value": absent_counts
                }
            ]
        }
        return json_doc

    def scrape_vote_event(self, event_id, law_id, skl, organization_id):
        events = []
        passed_status_correction = {
            "Рішення прийняте": "pass",
            "Рішення не прийняте": "fail"
        }
        if skl:
            url = "http://w1.c1.rada.gov.ua/pls/radan_gs09/ns_arh_zakon_gol_dep_WOHF?zn=%s&n_skl=%s" % (law_id, skl)
        else:
            url = "http://w1.c1.rada.gov.ua/pls/radan_gs09/ns_zakon_gol_dep_wohf?zn=%s" % law_id
        soup_vote_event = self.download_html_file(url)
        if soup_vote_event.find('ul', {"id": "gol_v"}):
            if len(soup_vote_event.find('ul', {"id": "gol_v"}).findAll('li')) > 1:
                for each_li_vote_event in soup_vote_event.find('ul', {"id": "gol_v"}).findAll('li')[1:]:
                    if each_li_vote_event.find('div', {"class": "fr_data"}):
                        date_text = each_li_vote_event.find('div', {"class": "fr_data"}).get_text()
                        name = each_li_vote_event.find('div', {"class": "fr_nazva"}).find('a').get_text()
                        url = each_li_vote_event.find('div', {"class": "fr_nazva"}).find('a').get("href")
                        if "http://w1.c1.rada.gov.ua" not in url:
                            url = "http://w1.c1.rada.gov.ua" + url
                        parsed_url = urlparse.urlparse(url)
                        motion_id = urlparse.parse_qs(parsed_url.query)['g_id'][0]
                        passed_status = each_li_vote_event.find('div', {"class": "fr_nazva"}).find('center').find('font').get_text().strip()
                        counts_text = each_li_vote_event.find('div', {"class": "fr_nazva"}).find('center').get_text().replace(passed_status, "").strip()
                        counts_list = counts_text.split(" ")
                        yes_votes = counts_list[0]
                        no_votes = counts_list[1]
                        abstain_votes = counts_list[2]
                        absent_votes = counts_list[4]
                        separator = "-"
                        yes_counts = self.split_vote_count(separator, yes_votes)
                        abstain_counts = self.split_vote_count(separator, abstain_votes)
                        no_counts = self.split_vote_count(separator, no_votes)
                        absent_counts = self.split_vote_count(separator, absent_votes)
                        result = passed_status_correction[passed_status.encode('utf-8')]
                        json_motion = self.build_json_motion(date_text, url, motion_id, event_id, organization_id, name,
                                                             result, yes_counts, no_counts, abstain_counts, absent_counts)
                        events.append(json_motion)
        return events

    def scrape_5th_chamber_vote_event(self, all_a_tags, event_id, organization_id):
        chamber_motions = []
        passed_status_correction = {
            "Рішення прийняте": "pass",
            "Рішення прийнято": "pass",
            "Рішення не прийнято": "fail",
            "Рішення не прийняте": "fail"
        }
        for a_tag in all_a_tags[1:]:
            text = a_tag.get_text().encode('utf-8')
            if "Реєстрація в залі." in text:
                continue
            else:
                url = "http://w1.c1.rada.gov.ua" + a_tag.get('href')
                soup_motion = self.download_html_file(url)
                motion_text = soup_motion.find("div", {"class": "head_gol"}).get_text().strip()
                parsed_url = urlparse.urlparse(url)
                motion_id = urlparse.parse_qs(parsed_url.query)['g_id'][0]
                motion_text_list = motion_text.split("\n")
                date_text = motion_text_list[1]
                passed_status = motion_text_list[3]
                result = passed_status_correction[passed_status.encode('utf-8')]
                counts_text = motion_text_list[2]
                counts_list = counts_text.split("  ")
                yes_votes = counts_list[0]
                no_votes = counts_list[1]
                abstain_votes = counts_list[2]
                absent_votes = counts_list[4]
                separator = ":"
                yes_counts = self.split_vote_count(separator, yes_votes)
                abstain_counts = self.split_vote_count(separator, abstain_votes)
                no_counts = self.split_vote_count(separator, no_votes)
                absent_counts = self.split_vote_count(separator, absent_votes)
                json_motion = self.build_json_motion(date_text, url, motion_id, event_id, organization_id, text,
                                                     result, yes_counts, no_counts, abstain_counts, absent_counts)
                chamber_motions.append(json_motion)
        return chamber_motions

    def vote_events_list(self):
        vote_event_list = []
        chambers = {}
        all_chambers = vpapi.getall("organizations", where={'classification': 'chamber'})
        for chamber in all_chambers:
            chambers[chamber['identifiers'][0]['identifier']] = chamber['id']
        widgets = ['        Progress: ', Percentage(), ' ', Bar(marker='#', left='[', right=']'),
                   ' ', ETA(), " - Processed: ", Counter(), ' events             ']
        pbar = ProgressBar(widgets=widgets)
        events_list = self.events_list()
        last_event_motion = vpapi.getfirst("motions", sort="-date")
        if last_event_motion:
            index_motion = next(index for (index, d) in enumerate(events_list) if d["identifier"] == last_event_motion['legislative_session_id'])
        else:
            index_motion = 0
        last_event = vpapi.getfirst("vote-events", sort="-start_date")
        if last_event:
            index_event = next(index for (index, d) in enumerate(events_list) if d["identifier"] == last_event['legislative_session_id'])
        else:
            index_event = 0

        index = min(index_motion, index_event)
        if len(events_list[index:]) > 0:
            for event in pbar(events_list[index:]):
                if event['term'] != "9":
                    url_plenary_session = event['url']
                    parsed_url = urlparse.urlparse(url_plenary_session)
                    skl = urlparse.parse_qs(parsed_url.query)['nom_skl'][0]
                else:
                    skl = None
                soup = self.download_html_file(event['url'])
                if soup.find('ul', {"class": "pd"}):
                    for each_li in soup.find('ul', {"class": "pd"}).findAll('li'):
                        if each_li.find("div", {'class': "block_pd"}) or each_li.find("div", {'class': "block_tab"}):
                            block_pd = each_li.find("div", {'class': "block_pd"})
                            block_tab = each_li.find("div", {'class': "block_tab"})
                            if block_pd:
                                law_id = block_pd.find('div', {'class': "nomer"}).find('a').get_text().strip()
                                if law_id != "":
                                    motions = self.scrape_vote_event(event['identifier'], law_id, skl, chambers[event['term']])
                                    vote_event_list += motions
                            elif block_tab:
                                law_id = block_tab.find('td', {'class': "exnomer"}).find('a').get_text().strip()
                                if law_id != "":
                                    motions = self.scrape_vote_event(event['identifier'], law_id, skl, chambers[event['term']])
                                    vote_event_list += motions
                else:
                    all_a_tags = soup.find('ul', {"class": "npd"}).findAll('a')
                    motions = self.scrape_5th_chamber_vote_event(all_a_tags, event['identifier'], chambers[event['term']])
                    vote_event_list += motions
        else:
            print "\n\tThere are no new items."
        sorted_vote_events = sorted(vote_event_list, key=itemgetter('date'))
        return sorted_vote_events

    def events(self):
        events = []
        events_list = self.events_list()
        last_event = vpapi.getfirst("events", sort='-start_date')
        if last_event:
            index = next(index for (index, d) in enumerate(events_list) if d["url"] == last_event['sources'][0]['url']) + 1
        else:
            index = 0
        widgets = ['        Progress: ', Percentage(), ' ', Bar(marker='#', left='[', right=']'),
                   ' ', ETA(), " - Processed: ", Counter(), ' events             ']
        pbar = ProgressBar(widgets=widgets)
        if len(events_list[index:]) > 0:
            for event in pbar(events_list[index:]):
                soup_event = self.download_html_file(event['url'])
                date = event['date']
                if soup_event.find('ul', {"class": "pd"}):
                    all_b_tags = soup_event.find('ul', {"class": "pd"}).findAll('b')
                    start_end_time = self.find_start_end_time(all_b_tags, date, 1)
                    start_date = start_end_time['min']
                    end_date = start_end_time['max']
                else:
                    all_b_tags = soup_event.find('ul', {"class": "npd"}).findAll('b')
                    start_end_time = self.find_start_end_time(all_b_tags, date, 0)
                    start_date = start_end_time['min']
                    end_date = start_end_time['max']
                event['start_date'] = start_date.replace(" ", "T")
                event['end_date'] = end_date.replace(" ", "T")
                events.append(event)
        else:
            print "\n\tThere are no new events to scrape"
        return events

    def scrape_events(self, url, chamber_id, term):
        plenary_session = "пленарні засідання".decode('utf-8')
        events_list = []
        soup = self.download_html_file(url)
        for each_li in soup.find('ul', {"class": "m_ses"}).findAll('li'):
            url_sessions = "http://w1.c1.rada.gov.ua" + each_li.get('onclick').replace("load_out_html('", "").replace("','Data_fr')", "")
            soup_events = self.download_html_file(url_sessions)
            for each_tr in soup_events.find('table', {"border": "0"}).findAll('tr'):
                for each_td in each_tr.findAll("td"):
                    for each_li_event in each_td.find("ul").findAll('li', {"style": "background-color:#FFFFAE;"}):
                        if each_li_event.find('a'):
                            url_plenary_session = each_li_event.find('a').get('href')
                            parsed_url = urlparse.urlparse(url_plenary_session)
                            day = urlparse.parse_qs(parsed_url.query)['day_'][0]
                            month = urlparse.parse_qs(parsed_url.query)['month_'][0]
                            year = urlparse.parse_qs(parsed_url.query)['year'][0]
                            date_str = year + "-" + month + "-" + day
                            name = plenary_session + " " + date_str
                            identifier = "event_" + str(year) + str(month) + str(day)
                            date = datetime.strptime(date_str, "%Y-%m-%d")
                            event_json = {
                                "term": term,
                                "date_obj": date,
                                "identifier": identifier,
                                "url": url_plenary_session,
                                "name": name,
                                'date': date_str,
                                'organization_id': chamber_id
                            }
                            events_list.append(event_json)
        return events_list

    def events_list(self):
        all_events = []
        chamber_ids = {}
        all_chambers = vpapi.getall("organizations", where={'classification': "chamber"})
        for chamber in all_chambers:
            chamber_ids[chamber['identifiers'][0]['identifier']] = chamber['id']
        chambers = self.chambers()
        for i in range(3, int(max(chambers.keys())) - 1):
            if i == 3:
                url_3 = "http://w1.c1.rada.gov.ua/pls/radan_gs09/ns_arh_h1?nom_skl=3"
                chamber_events = self.scrape_events(url_3, chamber_ids['3'], "3")
                all_events += chamber_events
            else:
                url = "http://w1.c1.rada.gov.ua/pls/radan_gs09/ns_arh_h1?nom_skl=%s" % str(i+1)
                chamber_events = self.scrape_events(url, chamber_ids[str(i+2)], str(i+2))
                all_events += chamber_events

        last_chamber_url = "http://w1.c1.rada.gov.ua/pls/radan_gs09/ns_pd1"
        last_chamber_events = self.scrape_events(last_chamber_url, chamber_ids['9'], "9")
        all_events += last_chamber_events
        sorted_events = sorted(all_events, key=itemgetter('date_obj'))
        return sorted_events

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
            "Голова Комітету": "chairman",
            "Співголова депутатської групи": "chairman",
            "Заступник голови депутатської групи": "chairman",
            "Голова Верховної Ради України": "chairman",
            "Голова депутатської фракції": "chairman",
            "Заступник голови Комітету": "vice-chairman",
            "Заступники голови депутатської фракції": "vice-chairman",
            "Заступник голови депутатської фракції": "vice-chairman",
            "Перший заступник голови Комітету": "first-vice-chairman",
            "Перший заступник Голови Верховної Ради України": "first-vice-chairman",
            "Заступник Голови Верховної Ради України": "vice-chairman",
            "Член депутатської фракції": "member",
            "член": "member",
            "Член Комітету": "member",
            "Голова підкомітету": "subcommittee-chairman"
        }

    def get_last_page(self):
        last_motion = vpapi.get("votes", page='1')
        if len(last_motion['_items']) > 0:
            last_motion_page_text = last_motion['_links']['last']['href']
            index = last_motion_page_text.index("page=") + 5
            last_motion_page = last_motion_page_text[index:]
        else:
            last_motion_page = None
        return last_motion_page

    def vote_correction(self):
        return {
            "За": "yes",
            "Проти": "no",
            "Відсутня": "absent",
            "Утримався": "abstain",
            "Утрималась": "abstain",
            "Не голосував": "not voting",
            "Не голосувала": "not voting",
            "Не голосував*": "not voting",
            "Відсутній": "absent"
        }

    def scrape_voting_records(self):
        sys.setrecursionlimit(100000000)
        chambers = {}
        all_chambers = vpapi.getall("organizations", where={"classification": "chamber"})
        for chamber in all_chambers:
            chambers[chamber['id']] = chamber['identifiers'][0]['identifier']
        motions = []
        all_motions = vpapi.getall("motions", sort="date")
        print "\n\tScraping vote events from Ukraine's parliament..."
        print "\tPlease wait. This may take a few moments...\n"
        for motion in all_motions:
            json_motion = {
                "start_date": motion['date'],
                "url": motion['sources'][0]['url'],
                "identifier": motion['identifier'],
                "term": chambers[motion['organization_id']],
                "organization_id": motion['organization_id']
            }
            motions.append(json_motion)
        sorted_motions = sorted(motions, key=itemgetter('start_date'))
        parliamentary_groups = {}
        for chamber in chambers:
            parliamentary_groups[chambers[chamber]] = {}
            all_parties = vpapi.getall("organizations", where={"classification": "parliamentary group", "parent_id": chamber})
            for party in all_parties:
                members_of_party = vpapi.getall("memberships", where={'organization_id': party['id']})
                for person in members_of_party:
                    parliamentary_groups[chambers[chamber]][person['person_id']] = party['id']

        members = {}
        all_members = vpapi.getall("people")
        for member in all_members:
            name = member['name']
            name_list = name.split(" ")
            name_ordered = name_list[2] + " " + name_list[0][:1] + "." + name_list[1][:1] + "."
            members[name_ordered] = member['id']
        counter_all = 0
        vote_correction = self.vote_correction()
        votes = []

        last_motion_page = self.get_last_page()
        if last_motion_page:
            last_page_motions = vpapi.get("votes", page=last_motion_page)
            last_page_motions_list = []
            for motion in last_page_motions["_items"]:
                last_page_motions_list.append(motion['vote_event_id'])
            index_start = next(index for (index, d) in enumerate(sorted_motions) if d["identifier"] == last_page_motions_list[-1]) + 1

        else:
            index_start = 0
        print index_start
        print "\n\tScraping votes from Ukraine's parliament...\n"
        widgets = ['        Progress: ', Percentage(), ' ', Bar(marker='#', left='[', right=']'),
                   ' ', ETA(), " - Processed: ", Counter(), ' vote events             ']
        pbar = ProgressBar(widgets=widgets)
        for motion in pbar(sorted_motions[index_start:5600]):
            url = motion['url']
            chamber = motion['term']
            vote_event_id = motion['identifier']
            soup = self.download_html_file(url)
            counter = 0
            for each_li in soup.findAll('div', {"class": "dep"}):
                counter_all += 1
                all_votes = soup.findAll('div', {"class": "golos"})
                option_text = all_votes[counter].get_text().strip()
                option = vote_correction[option_text.encode('utf-8')]
                name = each_li.get_text().strip()
                if name in members:
                    p_id = members[name]
                else:
                    p_id = None
                if p_id:
                    json_vote = {
                        "vote_event_id": vote_event_id,
                        "option": option,
                        "voter_id": p_id
                    }
                    if p_id in parliamentary_groups[chamber]:
                        o_id = parliamentary_groups[chamber][p_id]
                        print o_id
                    else:
                        o_id = None
                    if o_id:
                        json_vote['group_id'] = o_id
                    votes.append(json_vote)
                counter += 1
        return votes

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
                        ids_from_url = re.findall(r'\d+', member_url)
                        identifier = ids_from_url[0]
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
                        if identifier != "11102":
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