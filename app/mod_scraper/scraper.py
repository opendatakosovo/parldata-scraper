import mechanize
from bs4 import BeautifulSoup

class Scraper():
    def download_html_file(self, url):
        br = mechanize.Browser()
        br.set_handle_robots(False)  # ignore robots
        br.set_handle_refresh(False)  # can sometimes hang without this
        br.addheaders = [('User-Agent', "Firefox"), ('Accept', '*/*')]  # User-Agent
        response = br.open(url)

        html_content = response.read()
        soup = BeautifulSoup(html_content, 'html.parser')

        return soup
