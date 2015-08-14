from app.mod_scraper import scraper
import re

class ArmeniaParser():
    def mps_list(self):
        mps_list = []
        url = "http://www.parliament.am/deputies.php?lang=arm&enc=utf80"
        scrape = scraper.Scraper()
        soup = scrape.download_html_file(url)
        array = []
        for each_div in soup.findAll('div', {'class': 'dep_name_list'}):
            url = each_div.findAll("a")
            full_text = each_div.get_text().strip()
            distinct_id = full_text[:3]
            name = full_text.replace(distinct_id, "")
            names = name.split(' ')
            print names
            members_json = {
                "name": name.strip(),
                "distinct_id": distinct_id,

            }
            # print "\n\nname: %s \nId: %s" % (name.strip(), distinct_id)
            # print "url: http://www.parliament.am" + url[1].get('href')
            array.append({"name": name, "id": distinct_id})
        # print array

    def scrape_organization(self):
            print "scraping Armenia Votes data"