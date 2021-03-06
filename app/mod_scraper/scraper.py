import mechanize
from bs4 import BeautifulSoup

class Scraper():
    def download_html_file(self, url):
        # downloads the html file from the url through Mechanize
        # and returns the beautifulsoup object of page.
        br = mechanize.Browser()
        br.set_handle_robots(False)  # ignore robots
        br.set_handle_refresh(False)  # can sometimes hang without this
        br.addheaders = [('User-Agent', "Firefox"), ('Accept', '*/*')]  # User-Agent
        try:
            response = br.open(url)
            html_content = response.read()
            soup = BeautifulSoup(html_content, 'html.parser')
            return soup
        except Exception as ex:
            print ex.message
