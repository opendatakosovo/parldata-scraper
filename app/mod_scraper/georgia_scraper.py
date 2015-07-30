from pymongo import MongoClient
import scraper
import pprint

client = MongoClient()
db = client.ge

class GeorgiaScraper():
    def scrape_mp_bio_data(self, people, votes):
        '''
        Scraping members data of the Georgian Parliament.
        '''
        if people == "yes":
            db.mps_list.remove({})
            print "\nScraping members (people) of Georgia's parliament..."

            deputy_list_url = "http://www.parliament.ge/en/parlamentarebi/deputatebis-sia"
            scrape = scraper.Scraper()

            soup = scrape.download_html_file(deputy_list_url)

            counter = 0
            #iterate through each deputy in the deputy list.
            for each in soup.find("div", {"class": "mps_list"}): #iterate over loop [above sections]
                if each.find('a'):
                    continue
                else:
                    counter += 1
                    full_name = each.find('h4').next
                    position = each.find('p').next
                    url = each.get('href')
                    image_url = each.find('img').get('src')
                    person_id = url[-4:]

                    soup_deputy = scrape.download_html_file(url)

                    phone = ""
                    date_of_birth = ""
                    educational_institutions = ""
                    qualification = ""
                    election_form = ""
                    election_block = ""
                    specialities = {
                        "specialities": []
                    }

                    #iterate through each element of deputy information in the page and store data to the database.
                    for div_elements in soup_deputy.findAll("div", {"class": "info_group"}):
                        for li_element in div_elements.findAll('ul'):
                            if li_element.get_text(strip=True)[:4] == "phon":
                                phone = li_element.get_text(strip=True)
                                phone = phone.replace('phone', '')
                            if li_element.get_text(strip=True)[:4] == "date":
                                date_of_birth = li_element.get_text(strip=True)
                                date_of_birth = date_of_birth.replace('date of birth', '')
                            if li_element.get_text(strip=True)[:4] == "educ":
                                educational_institutions = li_element.get_text(strip=True)
                                educational_institutions = educational_institutions.replace('educational institutions', '')
                            if li_element.get_text(strip=True)[:4] == "qual":
                                qualification = li_element.get_text(strip=True)
                                qualification = qualification.replace('qualification', '')
                            if li_element.get_text(strip=True)[:4] == "spec":
                                speciality = li_element.get_text(strip=True)
                                speciality = speciality.replace('speciality', '')
                                specialities['specialities'].append(speciality)
                            if li_element.get_text(strip=True)[:10] == "election f":
                                election_form = li_element.get_text(strip=True)
                                election_form = election_form.replace('election form', '')
                            if li_element.get_text(strip=True)[:10] == "election b":
                                election_block = li_element.get_text(strip=True)
                                election_block = election_block.replace('election block', '')

                    json_doc = self.build_json_doc(person_id, full_name, position, url, image_url, phone, date_of_birth, educational_institutions,
                                           qualification, election_form, election_block, specialities['specialities'])
                    pp = pprint.PrettyPrinter()
                    pp.pprint(json_doc)
                    print "---------------------------------------------------------------------------------"
                    db.mps_list.insert(json_doc)

            #print "\n\tScraping completed! \n\tScraped " + str(counter) + " deputies"

    def build_json_doc(self, person_id, full_name, position, url, image_url, phone_number, date_of_birth, educational_institution, qualification,
                       election_form, election_block, specialities):
        json_doc = {
            "identifiers": {
              "identifier": person_id,
              "scheme": "parliament.ge"
            },
            "id": person_id,
            "full_name": full_name,
            "position": position,
            "source_url": url,
            "image_url": image_url,
            "phone_number": phone_number,
            "date_of_birth": date_of_birth,
            "educational_institutions": educational_institution,
            "qualification": qualification,
            "election_form": election_form,
            "election_block": election_block,
            "specialities": specialities
        }
        return json_doc

    '''
    sample_identifier = {
        'identifier': '046454286',
        'scheme': 'SIN'
    }
    sample_link = {
        'url': 'http://en.wikipedia.org/wiki/John_Q._Public',
        'note': 'Wikipedia page'
    }
    sample_image_url = 'http://www.google.com/images/srpr/logo11w.png'
    sample_person = {
        'name': 'Mr. John Q. Public, Esq.',
        'identifiers': [
            sample_identifier
        ],
        'email': 'jqpublic@xyz.example.com',
        'gender': 'male',
        'birth_date': '1920-01',
        'death_date': '2010-01-01',
        'image': sample_image_url,
        'summary': 'A hypothetical member of society deemed a "common man"',
        'biography': 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. ...',
        'national_identity': 'Scottish',
        'contact_details': [
            {
                'label': 'Mobile number',
                'type': 'tel',
                'value': '+1-555-555-0100',
                'note': 'Free evenings and weekends'
            }
        ],
        'links': [
            sample_link
        ]
    }
    person_with_id = {
        'id': 'bilbo-baggins',
        'name': 'Bilbo Baggins',
    }
    sample_organization = {
        "name": "ABC, Inc.",
        "founding_date": "1950-01-01",
        "dissolution_date": "2000-01-01",
    }
    sample_membership = {
        "label": "Kitchen assistant at ABC, Inc.",
        "role": "Kitchen assistant",
        "start_date": "1970-01",
        "end_date": "1971-12-31",
    }
    '''