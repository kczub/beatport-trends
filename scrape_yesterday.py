import os
import time
import datetime
import re
import pandas as pd
import requests
from bs4 import BeautifulSoup
from requests_html import HTML


yesterday = datetime.date.today() - datetime.timedelta(days=1)
base_url = 'https://www.beatport.com'
url = f'{base_url}/charts/all?start-date={str(yesterday)}&end-date={str(yesterday)}'

BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, 'Data')
TEMP_DIR = os.path.join(BASE_DIR, 'Temp')
TEMP_FILE_PATH = os.path.join(TEMP_DIR, f'{yesterday}-temp.csv')
CLEAN_FILE_PATH = os.path.join(DATA_DIR, f'{yesterday}.csv')


def get_next_page(html=None):
    if html is not None:
        next_page = html.find('a.pag-next', first=True).attrs['href']

    if next_page:
        next_url = f'{base_url}{next_page}'
        return next_url


def get_links(url, chart_links=None):
    """Return a list of links."""
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
    else:
        print("No more pages")

    return chart_links


def parse_chart(url):
    """
    Get genre of every track in a chart, return pandas series
    """
    r = requests.get(url)
    soup = BeautifulSoup(r.content, 'html.parser')

    date = soup.find('span', class_='value').string
    if str(date) != str(yesterday):
        print("wrong date")
        return None

    chart = []
    for genre in soup.find_all('p', class_='buk-track-genre')[1:]:
        chart.append(genre.find('a').string)

    series = pd.Series(chart, name=date)
    return series
        

def scrape(url):
    """
    Main scraping function
    """
    all_links = get_links(url)
    print("Scraping...")
    all_charts = []
    for url in all_links:
        all_charts.append(parse_chart(url))
        time.sleep(1)

    data = pd.concat(all_charts)

    os.makedirs(TEMP_DIR, exist_ok=True)
    data.to_csv(TEMP_FILE_PATH)
    return data


def clean_data(df):
    data = pd.read_csv(df, index_col=0)
    print("Cleaning")
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
    return clean_data



if __name__ == '__main__':
    scrape(url=url)
    clean_data(TEMP_FILE_PATH)