from app.mod_scraper import scraper
import re

class ArmeniaScraper():
    def mps_list(self):
        mps_list = []
        url = "http://www.parliament.am/deputies.php?lang=arm&enc=utf80"
        scrape = scraper.Scraper()
        soup = scrape.download_html_file(url)
        array = []
        for each_div in soup.findAll('div', {'class': 'dep_name_list'}):
            url_deputy = each_div.findAll("a")
            full_text = each_div.get_text().strip()
            distinct_id = full_text[:3]
            name = full_text.replace(distinct_id, "").strip()
            names = name.split(' ')
            print "name1: %s \nname2: %s \nname3: %s\n\n" % (names[0], names[1], names[2])
            members_json = {
                "name": name.strip(),
                "distinct_id": distinct_id,
            }
            soup_deputy = scrape.download_html_file(url_deputy)
            for each_row in soup_deputy.find('div', {'class': 'dep_description'}).find('tbody').findAll("tr"):
                print each_row
            # print "\n\nname: %s \nId: %s" % (name.strip(), distinct_id)
            # print "url: http://www.parliament.am" + url[1].get('href')
            array.append({"name": name, "id": distinct_id})
        # print array

    def scrape_organization(self):
            print "scraping Armenia Votes data"