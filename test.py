import requests
from bs4 import BeautifulSoup
import pandas as pd




class scrapy(object):
    def __init__(self,
                 url='http://tik8.com/category/',
                 elems_class='card_banner card'
                 ):
        self.url = url
        self.elems_class = elems_class
        page = requests.get(self.url)

        soup = BeautifulSoup(page.content, 'html.parser')

        self.elems = soup.find_all('div', class_=elems_class)

    def get_data(self):
        server_url = self.url
        api_url = self.url
        api_list = ['theater', 'concert', 'cinema', 'kid', 'conference',
                    'entertainment', 'Cultural-Heritage', 'escape-room']
        data = []
        for url in api_list:
            event_type = url
            url = api_url + url
            print(event_type, url)
            page = requests.get(url)
            soup = BeautifulSoup(page.content, 'html.parser')
            elems = soup.find_all('div', class_='card_banner card')
            #################################################################
            headers = ['event_type', 'details_api', 'title', 'location', 'image']
            for elem in elems:
                details_api = elem.find('a', class_='card_banner-box-hover__link-main')
                title = elem.find('img', class_='card_poster2')
                location = elem.find('span')

                if None in details_api:
                    continue
                details_api = server_url + str(details_api['href'])
                image = title['src']
                title = title['alt']
                location = location.text.strip()
                data.append([event_type, details_api, title, location, image])

        return pd.DataFrame(data, columns=headers)
    def run(self):
        self.get_data()

s= scrapy()
data = s.get_data()
        