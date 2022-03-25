import os
import time
import datetime
import re
import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests_html import HTML


# other_date = '2022-03-12'
yesterday = datetime.date.today() - datetime.timedelta(days=1)
base_url = 'https://www.beatport.com'
url = f'{base_url}/charts/all?start-date={str(yesterday)}&end-date={str(yesterday)}'
# url2 = f'{base_url}/charts/all?start-date={other_date}&end-date={other_date}'

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, 'Data')
CLEAN_FILE_PATH = os.path.join(DATA_DIR, f'{yesterday}.csv')
# CLEAN_FILE_PATH_2 = os.path.join(DATA_DIR, f'{other_date}.csv')


def get_next_page(html=None):
    if html is not None:
        next_page = html.find('a.pag-next', first=True).attrs['href']

    if next_page:
        next_url = f'{base_url}{next_page}'
        return next_url


def get_links(url, chart_links=None):
    r = requests.get(url)
    print(url, requests.codes.ok)
    html_string = HTML(html=r.content)

    if r.status_code != requests.codes.ok:
        return False

    links = list(html_string.links)
    regex = re.compile(r'^/chart/\w+')

    if chart_links is None:
        chart_links = []
    else:
        chart_links = chart_links

    for url in links:
        match = regex.search(url)
        if match is not None:
            chart_links.append(f'{base_url}{match.string}')

    next_url = get_next_page(html=html_string)
    if next_url:
        try:
            get_links(next_url, chart_links=chart_links)
        except AttributeError:
            print("No more pages")

    return chart_links


def parse_chart(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html.parser')

    date = soup.find('span', class_='value').string
    if str(date) != str(yesterday):
        return None

    chart = []
    for genre in soup.find_all('p', class_='buk-track-genre')[1:]:
        chart.append(genre.find('a').string)

    series = pd.Series(chart, name=date)
    return series
        

def scrape(url):
    all_links = get_links(url)
    print("Scraping...")
    all_charts = []
    for url in all_links:
        all_charts.append(parse_chart(url))
        time.sleep(1)

    data = pd.concat(all_charts)
    return data


def clean_data(raw_data):
    data = pd.DataFrame(raw_data)
    col = data.columns[0]
    data.rename({col: 'genre'}, axis=1, inplace=True)

    genres = data.genre.unique().tolist()
    values = [data.loc[data.genre == genre].shape[0] for genre in genres]

    temp = []
    for genre, val in zip(genres, values):
        data = {
            'genre': genre,
            'appearances': val
        }
        temp.append(data)
    
    clean_data = pd.DataFrame(temp)

    clean_data.to_csv(CLEAN_FILE_PATH, index=False)
    print("Done")
    return clean_data



if __name__ == '__main__':
    data = scrape(url=url)
    clean_data(raw_data=data)