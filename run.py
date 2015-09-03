from pymongo import MongoClient
import argparse
from time import sleep
from datetime import date
import os
import json
import vpapi
from app.mod_scraper.ukraine import ukraine_scraper
from app.mod_scraper.moldova import moldova_scraper
from app.mod_scraper.armenia import armenia_scraper
from app.mod_scraper.georgia import georgia_scraper
from app.mod_scraper.belarus_lowerhouse import belarus_scraper

client = MongoClient()
db = client.ge
BASE_DIR = os.path.dirname(os.path.realpath(__file__))


def scrape(countries, people, votes):
    global effective_date
    effective_date = date.today().isoformat()

    # execute MP's bio data.
    georgia = georgia_scraper.GeorgiaScraper()
    armenia = armenia_scraper.ArmeniaScraper()
    ukraine = ukraine_scraper.UkraineScraper()
    belarus = belarus_scraper.BelarusScraper()
    moldova = moldova_scraper.MoldovaScraper()
    references = {"georgia": georgia, "armenia": armenia, "ukraine": ukraine, "belarus": belarus, "moldova": moldova}
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
            print "\n\tPosting and updating data from %s parliament" % item
            print "\tThis may take a few minutes..."
            vpapi.parliament(creds[item.lower()]['parliament'])
            vpapi.timezone(creds[item.lower()]['timezone'])
            vpapi.authorize(creds[item.lower()]['api_user'], creds[item.lower()]['password'])
            if people == "yes":
                # references[item.lower()].scrape_committee_membership()
                # references[item.lower()].members_list()
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
                    print "\n\tPosting and updating data from %s data collection\n\n" % collection[2:]
                    for json_doc in data_collections[collection]:
                        if collection == "a-people":
                            where_condition = {'identifiers': {'$elemMatch': json_doc['identifiers'][0]}}
                            collection_of_data = "people"
                        elif collection == "c-parliamentary_groups" or collection == "d-committe":
                            if item.lower() == "armenia":
                                where_condition = {'name': json_doc['name'], "parent_id": json_doc['parent_id']}
                            else:
                                where_condition = {'name': json_doc['name']}
                            collection_of_data = "organizations"
                        elif collection == "b-chamber":
                            where_condition = {'identifiers': {'$elemMatch': json_doc['identifiers'][0]}}
                            collection_of_data = "organizations"

                        existing = vpapi.getfirst(collection_of_data, where=where_condition)
                        if not existing:
                            print "\t%s data collection item not found \n\tPosting new item to the API." % collection_of_data
                            resp = vpapi.post(collection_of_data, json_doc)
                        else:
                            print "\tUpdating %s data collection item" % collection_of_data
                            # update by PUT is preferred over PATCH to correctly remove properties that no longer exist now
                            resp = vpapi.put(collection_of_data, existing['id'], json_doc, effective_date=effective_date)
                        if resp["_status"] != "OK":
                            raise Exception("Invalid status code")

                        print "\t------------------------------------------------"
                    print "\n\tFinished Posting and updating data from %s data collection\n" % collection[2:]

                if item.lower() == "armenia" or item.lower() == "moldova":
                    memberships = {
                        "chambers": references[item.lower()].scrape_membership(),
                        "parliamentary_groups": references[item.lower()].scrape_parliamentary_group_membership(),
                        "committees": references[item.lower()].scrape_committee_membership()
                    }
                elif item.lower() == "georgia":
                    memberships = {
                        "chambers": references[item.lower()].scrape_parliamentary_group_membership(),
                    }

                for data_collection in memberships:
                    print "\n\tScraping and updating data from %s membership data collection\n" % data_collection
                    for json_doc in memberships[data_collection]:
                        existing = vpapi.getfirst("memberships", where={'organization_id': json_doc['organization_id'], "person_id": json_doc['person_id']})
                        if not existing:
                            print "\tMembership's data collection item not found \n\tPosting new item to the API."
                            resp = vpapi.post("memberships", json_doc)
                        else:
                            print "\tUpdating membership's data collection item"
                            # update by PUT is preferred over PATCH to correctly remove properties that no longer exist now
                            resp = vpapi.put("memberships", existing['id'], json_doc, effective_date=effective_date)
                        if resp["_status"] != "OK":
                            raise Exception("Invalid status code")

                        print "\t------------------------------------------------"
                    print "\n\tFinished Posted and updated data from %s membership data collection\n" % data_collection
            if votes == "yes":
                print "\n\tScraping and updating Vote Events, Motions and Votes"
                voting_data_collections = {
                    "motions": references[item.lower()].motions(),
                    "vote-events": references[item.lower()].vote_events(),
                }

                for collection in voting_data_collections:
                    try:
                        if len(voting_data_collections[collection]) > 0:
                            resp = vpapi.post(collection, voting_data_collections[collection])
                            if resp["_status"] != "OK":
                                raise Exception("Invalid status code")
                            print "\n\tFinished Posting and updating data from %s data collection" % collection
                        else:
                            print "\n\tThere are no new data for %s data collection" % collection
                    except BaseException as ex:
                        print ex.message

                votes = references[item.lower()].scrape_votes()
                try:
                    if len(votes) > 0:
                        vpapi.post("votes", votes)
                    else:
                        print "\n\tThere are no new data for votes data collection"
                except BaseException as ex:
                    print ex.message
                print "\n\tFinished Scraping and updating Vote Events, Motions and Votes"
                print "\t------------------------------------------------"
            vpapi.deauthorize()
    else:
        print "\n\tInvalid country/ies added"


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