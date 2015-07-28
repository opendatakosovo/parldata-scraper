from pymongo import MongoClient
import scraper
import pprint

client = MongoClient()
db = client.md

class MoldovaScraper():
    def scrape_mp_bio_data(self, people, votes):
        if people == "yes":
            db.mps_list.remove({})
            print "\nScraping members (people) of Moldova's parliament..."

            deputy_list_url = "http://www.parlament.md/StructuraParlamentului/Deputies/tabid/87/language/ro-RO/Default.aspx"
            scrape = scraper.Scraper()

            soup = scrape.download_html_file(deputy_list_url)

            counter = 0

            each = soup.findAll("table", {"cellspacing": "4"})[0].findAll('tr') #iterate over loop [above sections]
            for tr in each:
                link = ""
                if tr.find('a'):
                    for td in tr:
                        for td_element in td:
                            if str(td_element)[:2] == "<a":
                                if td_element.get('class')[0] == "FractionLink":
                                    print "link Fra: " + str(td_element.get('href'))
                                    print "party: " + td_element.get_text()
                                else:
                                    link = str(td_element.get('href'))
                                    print "full_name: " + td_element.get_text()
                                    print "link: " + str(td_element.get('href'))
                            elif str(td_element)[:2] == "<i":
                                print "image_url: http://www.parlament.md" + td_element.get('src')

                    soup_deputy = scrape.download_html_file(link)
                    #membership = soup_deputy.find("td", {"class": "ContentPane"})
                    #nameTags = membership.findAll('a', {"name": True})[0].get('name')
                    #print "personID: " + nameTags
                    print "----------------------------------------------------------"
                    counter += 1
                else:
                    continue

            print "Scraping compete!\nScraped %s members " % str(counter)
        if votes == "yes":
            print "scraping Moldova Votes data"