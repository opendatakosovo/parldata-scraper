# ParlData Scraper
Scraping parliament data that scrapes parliement websites and extracts data on MPs, their memberships, and votes. The scraped data is for the [Visegrad+ project](http://parldata.eu/) and made accessible from the Visegrad+ parliament API.

Data in scraped for the following countries:
- Armenia
- Belarus
  - Lower House
  - Upper House
- Georgia
- Moldova
- Ukraine

# Installation
- [Prerequisites](#prerequisites)
- [Download](#download)
- [Configuration](#configuration)
- [Running](#running)

# Prerequisites
- Made to run on a Unix distro. Development was done in Ubuntu.
- Install cURL. Required to download Python and/or virtualenv (in Ubuntu: sudo apt-get install curl).
- Install python-dev. Required to compile 3rd party python libraries.

# Download
>$ sudo mkdir --p /home/projects/scrapers
>
>$ cd /home/projects/scrapers
>
>$ sudo git clone https://github.com/opendatakosovo/parldata-scraper.git

# Configuration
TODO: write instructions for config.cfg file.

# Running
The scraper is executed by running the scrape.sh shell script. The script accepts the following parameters.

| Parameter    | Data Type              | Description                                                |
| -------------|------------------------|------------------------------------------------------------|
| countries    | Comma Separated String | List the countries from which we want to scrape data.      |
| people       | String                | Scrape MP data.                                            |
| votes        | String                | Scrape cast votes.                                       |
| loop         | Integer                | Loop scraper with given interval sleep time (in seconds).  |
| overwrite    | String                | Overwrite previously scraped data.                         |

To illustrate how the scraper's parameters are used, consider the following examples.

Scrape people and vote data for armenia and georgie. Run the scraper script every 3 minutes and overwrite all previously scraped data:
>bash scraper.sh --countries armenia,georgia --people --votes --loop 180 --overwrite

Run scraper once to retrieve people and votes data from Armenia parliament:
>bash scraper.sh --countries armenia --people --votes

Run scraper once to retrieve people data from Armenian parliament:
>bash scraper.sh --countries armenia --people

Run scraper every 3 minutes to retrieve votes data from Georgia parliament:
>bash scraper.sh --countries georgia --votes --loop 180
