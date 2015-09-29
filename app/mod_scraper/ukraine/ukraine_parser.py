# -*- coding: utf-8 -*-
from app.mod_scraper import scraper
from bs4 import BeautifulSoup
from progressbar import ProgressBar, Percentage, ETA, Counter, Bar
import dateutil.parser as dparser
from datetime import datetime
import requests
import pprint
import urlparse
import re
import vpapi
import dateutil.parser

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
                if len(time_list) > 1:
                    if time_list[0] != "00:00:00" and time_list[1] != "00:00:00":
                        time1 = datetime.strptime(date + " " + time_list[0], "%Y-%m-%d %H:%M:%S")
                        time2 = datetime.strptime(date + " " + time_list[1], "%Y-%m-%d %H:%M:%S")
                        timestamps_array.append(time1)
                        timestamps_array.append(time2)
                else:
                    if time_list[0] != "00:00:00":
                        time1 = datetime.strptime(date + " " + time_list[0], "%Y-%m-%d %H:%M:%S")
                        timestamps_array.append(dparser.parse(time1))
            else:
                if time_text != "00:00:00":
                    time1 = datetime.atetime.strptime(date + " " + time_text, "%Y-%m-%d %H:%M:%S")
                    timestamps_array.append(time1)
        max_min_json['min'] = str(min(timestamps_array))
        max_min_json['max'] = str(max(timestamps_array))
        return max_min_json

    def events(self):
        events = []
        events_list = self.events_list()
        widgets = ['        Progress: ', Percentage(), ' ', Bar(marker='#', left='[', right=']'),
                   ' ', ETA(), " - Processed: ", Counter(), ' events             ']
        pbar = ProgressBar(widgets=widgets)
        for event in pbar(events_list[:10]):
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
        return events

    def scrape_events(self, url, chamber_id):
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
                            date = year + "-" + month + "-" + day
                            name = plenary_session + " " + date
                            # soup_event = self.download_html_file(url_plenary_session)
                            # if soup_event.find('ul', {"class": "pd"}):
                            #     all_b_tags = soup_event.find('ul', {"class": "pd"}).findAll('b')
                            #     start_end_time = self.find_start_end_time(all_b_tags, timestamps_array, date, 1)
                            #     start_date = start_end_time['min']
                            #     end_date = start_end_time['max']
                            # else:
                            #     all_b_tags = soup_event.find('ul', {"class": "npd"}).findAll('b')
                            #     start_end_time = self.find_start_end_time(all_b_tags, timestamps_array, date, 0)
                            #     start_date = start_end_time['min']
                            #     end_date = start_end_time['max']
                            #
                            # print start_date
                            # print end_date
                            identifier = "event_" + str(year) + str(day) + str(month)
                            event_json = {
                                "identifier": identifier,
                                "url": url_plenary_session,
                                "name": name,
                                'date': date,
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
        last_chamber_url = "http://w1.c1.rada.gov.ua/pls/radan_gs09/ns_pd1"
        last_chamber_events = self.scrape_events(last_chamber_url, chamber_ids['9'])
        all_events += last_chamber_events
        for i in range(3, int(max(chambers.keys())) - 1):
            if i == 3:
                print "\n3\n"
                url_3 = "http://w1.c1.rada.gov.ua/pls/radan_gs09/ns_arh_h1?nom_skl=3"
                chamber_events = self.scrape_events(url_3, chamber_ids['3'])
                all_events += chamber_events
            else:
                print "\n%s\n" % str(i+1)
                url = "http://w1.c1.rada.gov.ua/pls/radan_gs09/ns_arh_h1?nom_skl=%s" % str(i+1)
                chamber_events = self.scrape_events(url, chamber_ids[str(i+2)])
                all_events += chamber_events
        return all_events

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