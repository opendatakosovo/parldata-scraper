from pymongo import MongoClient
import argparse
from time import sleep
from datetime import date
import os
import json
import vpapi
from app.mod_scraper import georgia_scraper, armenia_scraper, ukraine_scraper, belarus_scraper, moldova_scraper

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
    if countries == "all":
        armenia.scrape_mp_bio_data(people, votes, BASE_DIR)
        georgia.scrape_mp_bio_data(people, votes, BASE_DIR)
        belarus.scrape_mp_bio_data(people, votes, BASE_DIR)
    else:
        countries_array = countries.split(',')
        for item in countries_array:
            if people == "yes":
                mps_list = references[item.lower()].scrape_mp_bio_data(people, votes, BASE_DIR)
                for member in mps_list:
                    print member['identifiers'][0]
                    existing = vpapi.getfirst('people', where={'identifiers': {'$elemMatch': member['identifiers'][0]}})
                    if not existing:
                        resp = vpapi.post('people', member)
                    else:
                        # update by PUT is preferred over PATCH to correctly remove properties that no longer exist now
                        resp = vpapi.put('people', existing['id'], member, effective_date=effective_date)
                    if resp["_status"] != "OK":
                        raise Exception("Invalid status code")
            if votes == "yes":
                georgia.scrape_organization()




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
            except:
                print "An error occured wile polling for changes."

            # Wait for a bit before checking if there are any new edits.
            # But not too much that we would risk missing an edits (because we only look at the latest edit for now)
            if time_out == "yes":
                sleep(float(time_out_seconds))
            else:
                print "You are out of loop"
                break