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
    with open(os.path.join(BASE_DIR, 'access.json')) as f:
        creds = json.load(f)
    vpapi.parliament('ge/parliament')
    vpapi.timezone('Asia/Tbilisi')
    vpapi.authorize(creds['georgia']['api_user'], creds['georgia']['password'])
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

    for item in countries_array:
        if people == "yes":
            print "\n\tPosting and updating data from %s parliament" % item
            print "\tThis may take a few minutes..."
            members = references[item.lower()].scrape_mp_bio_data()
            chamber = references[item.lower()].scrape_chamber()
            parliamentary_groups = references[item.lower()].scrape_parliamentary_groups()
            committee = references[item.lower()].scrape_committe()
            data_collections = {
                "a-people": members,
                "b-chamber": chamber,
                "c-parliamentary_groups": parliamentary_groups,
                "d-committe": committee
            }
            # inserts data for each data collection in Visegrad+ Api
            for collection in sorted(set(data_collections)):
                print "\n\tPosting and updating data from %s data collection" % collection[2:]
                for json_doc in data_collections[collection]:
                    if collection == "a-people":
                        where_condition = {'identifiers': {'$elemMatch': json_doc['identifiers'][0]}}
                        collection_of_data = "people"
                    elif collection == "c-parliamentary_groups" or collection == "d-committe":
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
                print "\n\tFinished Posting and updating data from %s data collection" % collection[2:]

            membership = references[item.lower()].scrape_membership()
            for json_doc in membership:
                existing = vpapi.getfirst(collection_of_data, where={'organization_id': json_doc['organization_id'], "person_id": json_doc['person_id']})
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
            print "\n\tFinished Posting and updating data from memberships data collection"
        if votes == "yes":
            references[item.lower()].scrape_events()

    # Download bio images and render thumbnails.
    #download_bio_images()


# Funtction which will scrape MP's bio data
# Define the arguments.

if __name__ == "__main__":
    parser = argparse.ArgumentParser("\nArguments should be written like this: \n\t$1-countries $2-people $3-votes")
    parser.add_argument("--countries", help="Import countries data..", default="all")
    parser.add_argument("--people", help="Import the persons data..", default="yes")
    parser.add_argument("--votes", help="Import the votes data..", default="yes")
    parser.add_argument("--time_out", help="TimeOut..", default="yes")
    parser.add_argument("--time_out_seconds", help="TimeOut seconds..", default="86400")

    # Parse arguemnts and run the app.
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