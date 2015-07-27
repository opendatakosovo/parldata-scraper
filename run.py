from pymongo import MongoClient
import argparse
from time import sleep
from app.mod_scraper import georgia_scraper, armenia_scraper, ukraine_scraper

client = MongoClient()
db = client.ge


def scrape(countries, people, votes):
    # execute MP's bio data.
    georgia = georgia_scraper.GeorgiaScraper()
    armenia = armenia_scraper.ArmeniaScraper()
    ukraine = ukraine_scraper.UkraineScraper()

    references = {"georgia": georgia, "armenia": armenia, "ukraine": ukraine}
    if countries == "all":
        armenia.scrape_mp_bio_data(people, votes)
        georgia.scrape_mp_bio_data(people, votes)
    else:
        countries_array = countries.split(',')
        print countries_array
        for item in countries_array:
            references[item].scrape_mp_bio_data(people, votes)




    # Download bio images and render thumbnails.
    #download_bio_images()


# Funtction which will scrape MP's bio data
# Define the arguments.

if __name__ == "__main__":
    parser = argparse.ArgumentParser("\nArguments should be written like this: \n\t$1-countries $2-people $3-votes")
    parser.add_argument("--countries", help="Import countries data..")
    parser.add_argument("--people", help="Import the persons data..")
    parser.add_argument("--votes", help="Import the votes data..")
    parser.add_argument("--time_out", help="TimeOut..")
    parser.add_argument("--time_out_seconds", help="TimeOut seconds..")

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
                scrape(countries, people, votes)
            except:
                print "An error occured wile polling for changes."

            # Wait for a bit before checking if there are any new edits.
            # But not too much that we would risk missing an edits (because we only look at the latest edit for now)
            sleep(float(time_out_seconds))