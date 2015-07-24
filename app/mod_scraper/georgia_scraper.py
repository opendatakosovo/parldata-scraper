from pymongo import MongoClient
import scraper

client = MongoClient()
db = client.ge

class GeorgiaScraper():
    def scrape_mp_bio_data(self):

        db.mps_list.remove({})
        print "\nScraping members of parliament bio..."

        deputy_list_url = "http://www.parliament.ge/en/parlamentarebi/deputatebis-sia"
        scrape = scraper.Scraper()

        soup = scrape.download_html_file(deputy_list_url)

        counter = 0
        for each in soup.find("div", {"class": "mps_list"}): #iterate over loop [above sections]
            if each.find('a'):
                continue
            else:
                counter += 1
                full_name = each.find('h4').next
                position = each.find('p').next
                url = each.get('href')
                image_url = each.find('img').get('src')

                print "{\n\tlink: " + each.get('href') + ","
                print "\tname: " + each.find('h4').next + ","
                print "\tposition: " + each.find('p').next + ","
                print "\tpicture url: " + each.find('img').get('src') + ","

                deputy_url = url

                soup_deputy = scrape.download_html_file(deputy_url)

                phone = ""
                date_of_birth = ""
                educational_institutions = ""
                qualification = ""
                election_form = ""
                election_block = ""

                for div_elements in soup_deputy.findAll("div", {"class": "info_group"}): #iterate over loop [above sections]
                    for li_element in div_elements.findAll('ul'):
                        if li_element.get_text(strip=True)[:4] == "phon":
                            phone = li_element.get_text(strip=True)
                            phone = phone.replace('phone', '')
                            print "\tphone number: " + phone + ","
                        if li_element.get_text(strip=True)[:4] == "date":
                            date_of_birth = li_element.get_text(strip=True)
                            date_of_birth = date_of_birth.replace('date of birth', '')
                            print "\tdate of birth: " + date_of_birth + ","
                        if li_element.get_text(strip=True)[:4] == "educ":
                            educational_institutions = li_element.get_text(strip=True)
                            educational_institutions = educational_institutions.replace('educational institutions', '')
                            print "\teducational institutions: " + educational_institutions + ","
                            #deputy_personal_info.append(li_element.get_text(strip=True))
                        if li_element.get_text(strip=True)[:4] == "qual":
                            qualification = li_element.get_text(strip=True)
                            qualification = qualification.replace('qualification', '')
                            print "\tqualification: " + qualification + ","
                            #deputy_personal_info.append(li_element.get_text(strip=True))
                        if li_element.get_text(strip=True)[:10] == "election f":
                            election_form = li_element.get_text(strip=True)
                            election_form = election_form.replace('election form', '')
                            print "\telection form: " + election_form + ","
                        if li_element.get_text(strip=True)[:10] == "election b":
                            election_block = li_element.get_text(strip=True)
                            election_block = election_block.replace('election block', '')
                            print "\telection block: " + election_block + "\n},"
                            #deputy_personal_info.append(li_element.get_text(strip=True))

                json_doc = self.build_json_doc(full_name, position, url, image_url, phone, date_of_birth, educational_institutions,
                                       qualification, election_form, election_block)
                db.mps_list.insert(json_doc)

        print "\n\tScraping completed! \n\tScraped " + str(counter) + " deputies"

    def build_json_doc(self, full_name, position, url, image_url, phone_number, date_of_birth, educational_institution, qualification,
                       election_form, election_block):
        json_doc = {
            "full_name": full_name,
            "position": position,
            "source_url": url,
            "image_url": image_url,
            "phone_number": phone_number,
            "date_of_birth": date_of_birth,
            "educational_institutions": educational_institution,
            "qualification": qualification,
            "election_form": election_form,
            "election_block": election_block
        }
        return json_doc