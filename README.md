# ParlData Scraper
Data scraper that scans parliement websites and extracts data on MPs, their memberships, and votes. The scraped data is for the [Visegrad+ project](http://parldata.eu/) and is made accessible from the Visegrad+ parliament API.

Data is scraped for the following countries:
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
- [Install](#install)
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

Get VPAPI client and SSH certificate of the server:

> $ sudo wget https://raw.githubusercontent.com/KohoVolit/api.parldata.eu/master/client/vpapi.py
>
> $ sudo wget https://raw.githubusercontent.com/KohoVolit/api.parldata.eu/master/client/server_cert.p

# Install
- Install the required libraries for running the scraper.
> bash install.sh

# Running
The scraper is executed by running the scrape.sh shell script. The script accepts the following parameters.

| Parameter    | Data Type              | Description                                                |
| -------------|------------------------|------------------------------------------------------------|
| countries    | Comma Separated String | List the countries from which we want to scrape data.      |
| people       | String                | Scrape MP data.                                            |
| votes        | String                | Scrape cast votes.                                       |
| loop         | String                | Loop scraper with given interval sleep time (in seconds) or (ex. 2d - 'd' means days).  |

To illustrate how the scraper's parameters are used, consider the following examples.

Scrape people and vote data for Armenia and Georgia. Run the scraper script every 3 minutes:
>bash run.sh --countries armenia,georgia --people yes --votes yes --loop 180

Run scraper every 2 days to retrieve people and votes data from Armenia parliament:
>bash run.sh --countries armenia --people yes --votes yes --loop 2d
