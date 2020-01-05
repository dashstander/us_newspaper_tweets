import argparse
from bs4 import BeautifulSoup
import requests
import re
import pandas as pd
from io import StringIO, BytesIO

parser = argparse.ArgumentParser()
parser.add_argument('--fp', action='store', default='~')

base_url = 'https://www.thepaperboy.com'

def get_state_name(tag):
    if tag.text:
        return tag.contents[0]


def get_state_link(tag):
    if tag.text:
        return base_url + tag['href']

def make_soup(url):
    page = BytesIO(requests.get(url).content)
    return BeautifulSoup(page, 'lxml')

def get_states():
    url = base_url + '/usa-newspapers-by-state.cfm'
    soup = make_soup(url)
    attrs = {'class': 'mediumlink', 'href': re.compile('newspapers')}

    return {
        get_state_name(tag): get_state_link(tag) 
        for tag 
        in soup.find_all('a', attrs=attrs)
    }


def state_papers_iter(soup, state):
    papers = []
    pattern = re.compile('newspaper|twitter')

    for row in soup.find_all('tr'):
        elements = [el.text for el in row.find_all('a', href=pattern)]
        if len(elements) > 1:
            paper_name = elements[0]
            if paper_name in ['World Newspapers', 'Newspapers by Country']:
                continue
            if len(elements) == 3:
                papers.append({'paper_name': paper_name, 'city': elements[2], 'state': state, 'twitter': elements[1]})
            else:
                papers.append({'paper_name': paper_name, 'city': elements[1], 'state': state, 'twitter': ''})
            
    
    return pd.DataFrame(papers)


def get_all_papers():
    states = get_states()
    all_papers = []
    for state_name, url in states.items():
        print(f'{state_name}: {url}')
        if url:
            state_papers = state_papers_iter(make_soup(url), state_name)
            print(f'\tAdded {state_papers.shape[0]} papers.')
            all_papers.append(state_papers)
        
    return all_papers


if __name__ == '__main__':
    args, _ = parser.parse_known_args()
    papers = pd.concat(get_all_papers())
    papers.to_csv(args.fp, index=False)


