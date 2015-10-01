# -*- coding: utf-8 -*-
import argparse
from time import sleep
from datetime import date
import os
import urllib2
import json
import vpapi
import dateutil.parser
from app.mod_scraper.ukraine import ukraine_scraper
from app.mod_scraper.moldova import moldova_scraper
from app.mod_scraper.armenia import armenia_scraper
from app.mod_scraper.georgia import georgia_scraper
from app.mod_scraper.belarus_lowerhouse import belarus_lowerhouse_scraper
from app.mod_scraper.belarus_upperhouse import belarus_upperhouse_scraper
from progressbar import ProgressBar, Percentage, ETA, Counter, Bar

BASE_DIR = os.path.dirname(os.path.realpath(__file__))


def internet_on():
    try:
        response = urllib2.urlopen("https://www.google.com/?gws_rd=ssl", timeout=1)
        if response:
            return True
    except urllib2.URLError as err: pass
    return False


def local_to_utc(dt_str):
    dt = dateutil.parser.parse(dt_str, dayfirst=True)
    if ':' in dt_str:
        return vpapi.local_to_utc(dt, to_string=True)
    else:
        return dt.strftime('%Y-%m-%d')


def scrape(countries, people, votes):
    global effective_date
    effective_date = date.today().isoformat()

    # execute MP's bio data.
    georgia = georgia_scraper.GeorgiaScraper()
    armenia = armenia_scraper.ArmeniaScraper()
    ukraine = ukraine_scraper.UkraineScraper()
    belarus_lowerhouse = belarus_lowerhouse_scraper.BelarusLowerhouseScraper()
    belarus_upperhouse = belarus_upperhouse_scraper.BelarusUpperhouseScraper()
    moldova = moldova_scraper.MoldovaScraper()
    references = {"georgia": georgia, "armenia": armenia, "ukraine": ukraine,
                  "belarus-lowerhouse": belarus_lowerhouse, "moldova": moldova,
                  "belarus-upperhouse": belarus_upperhouse}
    countries_array = []
    if countries == "all":
        for key in references:
            countries_array.append(key)
    else:
        countries_array = countries.split(',')
        indexes = []
        for country in countries_array:
            if country.lower() not in references:
                indexes.append(countries_array.index(country))
        if len(indexes) > 0:
            countries_array.pop(indexes)
    with open(os.path.join(BASE_DIR, 'access.json')) as f:
        creds = json.load(f)
    if len(countries_array) > 0:
        for item in countries_array:
            if internet_on():
                print "\n\tPosting and updating data from %s parliament" % item
                print "\tThis may take a few minutes..."
                vpapi.parliament(creds[item.lower()]['parliament'])
                vpapi.timezone(creds[item.lower()]['timezone'])
                vpapi.authorize(creds[item.lower()]['api_user'], creds[item.lower()]['password'])
                if people == "yes":
                    members = references[item.lower()].scrape_mp_bio_data()
                    chamber = references[item.lower()].scrape_chamber()
                    parliamentary_groups = references[item.lower()].scrape_parliamentary_groups()
                    committee = references[item.lower()].scrape_committee()
                    data_collections = {
                        "a-people": members,
                        "b-chamber": chamber,
                        "c-parliamentary_groups": parliamentary_groups,
                        "d-committe": committee
                    }
                    # inserts data for each data collection in Visegrad+ Api
                    for collection in sorted(set(data_collections)):
                        widgets = ['        Progress: ', Percentage(), ' ', Bar(marker='#', left='[', right=']'),
                                   ' ', ETA(), " - Processed: ", Counter(), ' items             ']
                        pbar = ProgressBar(widgets=widgets)
                        print "\n\tPosting and updating data to the Visegrad+ from %s data collection\n\n" % \
                              collection[2:]
                        if len(data_collections[collection]) > 0:
                            for json_doc in pbar(data_collections[collection]):
                                if collection == "a-people":
                                    where_condition = {'identifiers': {'$elemMatch': json_doc['identifiers'][0]}}
                                    collection_of_data = "people"
                                elif collection == "c-parliamentary_groups" or collection == "d-committe":
                                    if item.lower() == "armenia" or item.lower() == "belarus-upperhouse"\
                                            or item.lower() == "ukraine":
                                        where_condition = {'name': json_doc['name'], "parent_id": json_doc['parent_id']}
                                    else:
                                        where_condition = {'name': json_doc['name']}
                                    collection_of_data = "organizations"
                                elif collection == "b-chamber":
                                    where_condition = {'identifiers': {'$elemMatch': json_doc['identifiers'][0]}}
                                    collection_of_data = "organizations"

                                existing = vpapi.getfirst(collection_of_data, where=where_condition)
                                if not existing:
                                    resp = vpapi.post(collection_of_data, json_doc)
                                else:
                                    json_obj_id = existing['id']
                                    items_to_delete = ["created_at", "updated_at", "_links", "id"]
                                    for item_delete in items_to_delete:
                                        del existing[item_delete]
                                    if json.loads(json.dumps(json_doc)) == existing:
                                        continue
                                    else:
                                        resp = vpapi.put(collection_of_data, json_obj_id, json_doc, effective_date=effective_date)

                                    # update by PUT is preferred over PATCH to correctly remove properties that no longer exist now
                                if resp["_status"] != "OK":
                                    raise Exception("Invalid status code")

                            print "\n\tFinished Posting and updating data from %s data collection\n" % collection[2:]
                    if item.lower() != "georgia":
                        memberships = {
                            "chambers": references[item.lower()].scrape_membership(),
                            "parliamentary_groups": references[item.lower()].scrape_parliamentary_group_membership(),
                            "committees": references[item.lower()].scrape_committee_members()
                        }
                    elif item.lower() == "georgia":
                        memberships = {
                            "chambers": references[item.lower()].scrape_membership()
                        }

                    for data_collection in memberships:
                        widgets_stat = ['        Progress: ', Percentage(), ' ', Bar(marker='#', left='[', right=']'),
                                        ' ', ETA(), " - Processed: ", Counter(), ' items             ']
                        prog_bar = ProgressBar(widgets=widgets_stat)
                        if len(memberships[data_collection]) > 0:
                            print "\n\tPosting and updating data from %s membership data collection\n" % data_collection
                            for json_doc in prog_bar(memberships[data_collection]):
                                existing = vpapi.getfirst("memberships", where={'organization_id': json_doc['organization_id'],
                                                                                "person_id": json_doc['person_id']})
                                if not existing:
                                    resp = vpapi.post("memberships", json_doc)
                                else:
                                    json_obj_id = existing['id']
                                    items_to_delete = ["created_at", "updated_at", "_links", "id"]
                                    for item_delete in items_to_delete:
                                        del existing[item_delete]
                                    if json.loads(json.dumps(json_doc)) == existing:
                                        continue
                                    else:
                                        resp = vpapi.put("memberships", json_obj_id, json_doc, effective_date=effective_date)
                                if resp["_status"] != "OK":
                                    raise Exception("Invalid status code")
                            print "\n\tFinished Posted and updated data from %s membership data collection\n" % data_collection
                        else:
                            print "\n\tThere is no data from %s membership data collection\n" % data_collection
                            continue
                if votes == "yes":
                    events = references[item.lower()].scrape_events()
                    if len(events) > 0:
                        post_data("events", events)
                    else:
                        print "\tThere's not any event to post from %s parliament" % item
                    motions = references[item.lower()].motions()
                    if len(motions) > 0:
                        post_data("motions", motions)
                    else:
                        print "\tThere's not any motion to post from %s parliament" % item
                    vote_events = references[item.lower()].vote_events()
                    if len(vote_events) > 0:
                        post_data("vote-events", vote_events)
                    else:
                        print "\tThere's not any event to post from %s parliament" % item

                    # votes = references[item.lower()].scrape_votes()
                    # try:
                    #     if len(votes) > 0:
                    #         vpapi.post("votes", votes)
                    # except BaseException as ex:
                    #     print ex.message
                vpapi.deauthorize()
            else:
                print "\n\tInternet connection problems for %s official parliament web page" % item
                continue
    else:
        print "\n\tInvalid country/ies added"


def post_data(collection_str, data_collection):
    try:
        if len(data_collection) > 0:
            resp = vpapi.post(collection_str, data_collection)
            if resp["_status"] != "OK":
                raise Exception("Invalid status code")
            print "\n\tFinished Posting and updating data from %s data collection" % collection_str
    except BaseException as ex:
        print ex.message

# Define the arguments.
if __name__ == "__main__":
    parser = argparse.ArgumentParser("\nArguments should be written like this: \n\t$1-countries $2-people $3-votes")
    parser.add_argument("--countries", help="Import countries data..", default="all")
    parser.add_argument("--people", help="Import the persons data..", default="yes")
    parser.add_argument("--votes", help="Import the votes data..", default="yes")
    parser.add_argument("--time_out", help="TimeOut..", default="yes")
    parser.add_argument("--time_out_seconds", help="TimeOut seconds..", default="86400")

    # Parse arguments and run the app.
    args = parser.parse_args()
    countries = args.countries
    people = args.people
    votes = args.votes
    time_out = args.time_out
    time_out_seconds = args.time_out_seconds
    if time_out_seconds != "":
        while True:
            try:
                scrape(countries, people.lower(), votes.lower())
            except BaseException as e:
                print e.message

            # Wait for a bit before checking if there are any new edits.
            # But not too much that we would risk missing an edits (because we only look at the latest edit for now)
            if time_out == "yes":
                sleep(float(time_out_seconds))
            else:
                print "You are out of loop"
                break