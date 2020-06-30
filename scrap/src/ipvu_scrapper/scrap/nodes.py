import logging
import time
from datetime import datetime
from typing import Tuple

import pandas as pd
import requests
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)


def scrap_lancet():
    r = requests.get("https://www.thelancet.com/coronavirus")
    soup = BeautifulSoup(r.text, "lxml")
    articles = soup.find_all("div", {"class": "articleCitation"})
    articles[0].select_one(".articleType").get_text().strip()
    data = list()
    for article in articles:
        link = article.select_one(".articleTitle").select_one("a")['href']
        abstract, date = get_abstract_lancet(link)
        data.append([
            "DOI:" + article.select_one(".doi").get_text().replace('DOI:', '').replace('https://doi.org/', '').strip(),
            article.select_one(".articleType").get_text().strip() if article.find_all("div", {
                "class": "articleType"}) else 'N/A',
            article.select_one(".articleTitle").get_text().strip(),
            link,
            article.select_one(".doi").get_text().replace('DOI:', '').strip(),
            article.select_one(".doi").get_text().replace('DOI:', '').replace('https://doi.org/', '').strip(),
            article.select_one(".authors").get_text() if article.find_all("div", {"class": "authors"}) else 'N/A',
            article.select_one(".citation").get_text().strip(),
            abstract,
            article.select_one(".published-online").get_text().split(':')[1] if article.select_one(
                ".published-online") else date,
            'Open' if article.find_all(".OALabel") else 'Closed'
        ])

    return pd.DataFrame(data,
                        columns=['ID', 'Type', 'Title', 'Link', 'DOI_link', 'DOI', 'Authors', 'Citation', 'Abstract',
                                 'PublishedDate', 'Availability'])


def scrap_elsevier() -> pd.DataFrame:
    r = requests.get(
        "https://api.elsevier.com/content/search/sciencedirect?query=covid&apiKey=7f59af901d2d86f78a1fd60c1bf9426a")
    articles = r.json()['search-results']['entry']
    data = list()
    for article in articles:
        data.append([
            article['dc:identifier'],
            article['load-date'].split("T")[0],
            article['dc:title'],
            get_abstract_elsevier(article['prism:url']),
            article['prism:publicationName'],
            article['dc:creator'],
            article['authors'],
            article['prism:url'],
            article['prism:doi'],
            'Open' if bool(article['openaccess']) else 'Private',
            article['pii']
        ])

    return pd.DataFrame(data,
                        columns=['ID', 'PublishedDate', 'Title', 'Abstract', 'Type', 'Creator', 'Authors',
                                 'Link', 'DOI', 'Availability', 'PII'])


def scrap_pubmed() -> pd.DataFrame:
    r = requests.get("https://www.ncbi.nlm.nih.gov/research/coronavirus-api/search/?filters=%7B%7D&sort=score%20desc")
    articles = r.json()['results']
    data = list()
    for article in articles:
        details, doi = get_details_pubmed(article['pmid'])
        data.append([
            ("DOI:" + doi) if doi else ("ID:" + str(article['pmid'])),
            article['pmid'],
            doi,
            article['title'],
            article['journal'],
            article['authors'] if 'authors' in article else '',
            details,
            article['date'].split("T")[0],
            article['topics'],
            article['text_hl']
        ])
    return pd.DataFrame(data,
                        columns=['ID', 'PubmedID', 'DOI', 'Title', 'Type', 'Authors', 'Abstract', 'PublishedDate',
                                 'Topics',
                                 'HighLights'])


def scrap_uptodate():
    r = requests.get(
        "https://www.uptodate.com/services/app/contents/search/2/json?index=0~20&language=en&max=20&search=covid+19")
    articles = r.json()['data']['searchResults']
    date = datetime.fromtimestamp(int(articles[0]['viewInLink']['lastMajorUpdateMs']) / 1000.0)
    data = list()
    for article in articles:
        data.append([
            "ID:" + article['id'],
            article['type'],
            article['subtype'],
            article['title'],
            article['url'],
            get_abstract_uptodate(article['url']),
            article['snippet'].replace('&hellip;', '').replace('<b>', '').replace('</b>', ''),
            date
        ])
    return pd.DataFrame(data, columns=['ID', 'Type', 'Subtype', 'Title', 'URL', 'Abstract', 'Snippet', 'PublishedDate'])


def scrap_nejm() -> pd.DataFrame:
    r = requests.get("https://www.nejm.org/coronavirus")
    soup = BeautifulSoup(r.text, "lxml")
    articles = soup.find_all("li", {"class": "m-article"})
    data = list()
    for article in articles:
        data.append([
            ("DOI:" + article.select_one(".m-article__link")['href'].replace('/doi/full/', '').split('?')[0]) if
            article.find_all("a", {"class": "m-article__link"}) else 'N/A',
            article.select_one(".m-article__type").get_text().strip() if article.select_one(
                ".m-article__type") else 'N/A',
            article.select_one(".m-article__title").get_text().strip(),
            article.select_one(".m-article__link")['href'] if article.find_all("a", {
                "class": "m-article__link"}) else 'N/A',
            article.select_one(".m-article__link")['href'].replace('/doi/full/', '').split('?')[0] if article.find_all(
                "a", {
                    "class": "m-article__link"}) else 'N/A',
            article.select_one(".m-article__author").get_text() if article.find_all("em", {
                "class": "m-article__author"}) else 'N/A',
            article.select_one(".m-article__blurb").get_text().replace('\n', '').strip(),
            article.select_one(".m-article__date").get_text() if article.find_all("em", {
                "class": "m-article__date"}) else 'N/A',
            article.select_one(".m-article__icons").find('svg').attrs['class'][0].split('--')[1] if article.find_all(
                "em", {"class": "m-article__icons"}) else 'N/A'
        ])
    return pd.DataFrame(data, columns=['ID', 'Type', 'Title', 'Link', 'DOI', 'Authors', 'Abstract', 'PublishedDate',
                                       'Availability'])


def scrap_ema() -> pd.DataFrame:
    r = requests.get(
        "https://www.ema.europa.eu/en/human-regulatory/overview/public-health-threats/coronavirus-disease-covid-19/covid-19-whats-new")
    soup = BeautifulSoup(r.text, "lxml")
    table = soup.find("table", {"class": "ecl-table"}).select_one("tbody")
    articles = list()
    for row in table.findAll("tr"):
        articles.append(row)
    data = list()

    for article in articles:
        data.append([
            "URL:" + article.find_all("td")[1].select_one("a")['href'].split('/')[-1],
            article.find_all("td")[1].get_text().strip(),
            article.find_all("td")[1].select_one("a")['href'],
            article.find_all("td")[2].get_text().strip(),
            article.find_all("td")[0].get_text().strip(),
            article.find_all("td")[3].get_text()
        ])
    return pd.DataFrame(data, columns=['ID', 'Title', 'Link', 'Abstract', 'PublishedDate', 'MoreInfoLink'])


def scrap_nature() -> pd.DataFrame:
    r = requests.get("https://www.nature.com/search?q=covid")
    soup = BeautifulSoup(r.text, "lxml")
    articles = soup.findAll("li", {"class": "mb20"})
    data = list()
    for article in articles:
        abstract, doi = get_details_nature(article.select_one("h2").select_one("a")['href'])
        if not abstract and not doi:
            continue
        data.append(
            ["DOI:" + doi or "",
             article.select_one("h2").get_text().strip(),
             doi or None,
             article.select_one("h2").select_one("a")['href'],
             article.find("li", {"itemprop": "creator"}).get_text().strip()
             if article.find("li", {"itemprop": "creator"}) else None,
             abstract or None,
             article.p.find(text=True, recursive=False).strip(),
             article.find("a", {"class": "emphasis"}).get_text().strip(),
             article.find("time", {"itemprop": "datePublished"})['datetime']
             ])
    return pd.DataFrame(data, columns=['ID', 'Title', 'DOI', 'Link', 'Author', 'Abstract', 'Type', 'Subject',
                                       'PublishedDate'])


def scrap_acp() -> pd.DataFrame:
    r = requests.get("https://www.acpjournals.org/topic/category/coronavirus")
    soup = BeautifulSoup(r.text, "lxml")
    articles = soup.findAll("li", {"class": "search__item"})
    data = list()
    for article in articles:
        link = article.select_one(".issue-item__title").select_one("a")["href"]
        doi = article.select_one(".issue-item__title").select_one("a")["href"].replace("/doi/", "")
        data.append(
            ["DOI:" + doi,
             article.select_one(".issue-item__title").select_one("a").get_text(),
             doi,
             article.select_one(".meta__heading").get_text(),
             article.select_one(".issue-item__title").select_one("span").get_text(),
             article.select_one(".meta__epubDate").get_text(),
             article.select_one(".issue-item__authors").get_text(),
             get_abstract_acp(link),
             link
             ])
    return pd.DataFrame(data, columns=['ID', 'Title', 'DOI', 'Type', 'Availability', 'PublishedDate', 'Authors',
                                       'Abstract', 'Link'])


def get_abstract_lancet(link: str) -> Tuple[any, any]:
    time.sleep(1)
    log.info("Abstract url: https://www.thelancet.com" + link)
    abstract = ""
    try:
        d = requests.get("https://www.thelancet.com" + link, timeout=20)
        content_soup = BeautifulSoup(d.text, "lxml")
    except:
        return None, None

    date = None
    if content_soup.select_one(".article-header__publish-date__value"):
        date = content_soup.select_one(".article-header__publish-date__value").get_text()
    sections = content_soup.find_all("div", {"class": "section-paragraph"})
    for section in sections:
        abstract += " " + section.get_text()

    return abstract.replace('\n', '').rstrip(), date


def get_abstract_elsevier(url: str) -> any:
    time.sleep(1)
    log.info("Abstract url: " + url)
    try:
        d = requests.get(str(url) + "?apiKey=7f59af901d2d86f78a1fd60c1bf9426a",
                         headers={'Accept': 'application/json'},
                         timeout=10)
    except:
        return None
    if d.status_code == 429:
        return "N/A (Too many requests)"
    if d.status_code < 200 or d.status_code > 299:
        return None
    if not d.json()["full-text-retrieval-response"]["coredata"]["dc:description"]:
        return None
    return d.json()["full-text-retrieval-response"]["coredata"]["dc:description"] \
        .replace('Abstract\n', '') \
        .replace('\n', ' ') \
        .rstrip()


def get_abstract_uptodate(url: str) -> any:
    time.sleep(1)
    url = url.split('/')[2].split('?')[0]
    log.info("Abstract url: https://www.uptodate.com/services/app/contents/topic/" + url)
    try:
        d = requests.get("https://www.uptodate.com/services/app/contents/topic/" + url + "/json",
                         headers={'Accept': 'application/json'},
                         timeout=10)
        content_soup = BeautifulSoup(d.json()["data"]['bodyHtml'], "html.parser")
    except:
        return None
    if d.status_code < 200 or d.status_code > 299:
        return None
    return content_soup.select_one("#topicText") \
        .get_text() \
        .replace('\n', ' ') \
        .strip()


def get_details_pubmed(docid: int) -> Tuple[any, any]:
    time.sleep(1)
    log.info("Abstract url: https://www.ncbi.nlm.nih.gov/research/coronavirus/publication/" + str(docid))
    try:
        d = requests.get("https://www.ncbi.nlm.nih.gov/research/coronavirus-api/publication/" + str(docid),
                         headers={'Accept': 'application/json'},
                         timeout=10)
    except:
        return None, None
    abstract = d.json()['text'][1].replace('\n', ' ').strip() if d.json()['text'] else None
    doi = d.json()['doi'].rstrip() if 'doi' in d.json() else None
    return abstract, doi


def get_details_nature(link: str) -> Tuple[any, any]:
    time.sleep(1)
    log.info("https://www.nature.com" + link)
    try:
        d = requests.get("https://www.nature.com" + link, timeout=10)
    except:
        return None, None
    content_soup = BeautifulSoup(d.text, "lxml")
    abstract = content_soup.select_one("#Abs1-content").get_text() if content_soup.select_one("#Abs1-content") else None
    doi = content_soup.select_one("#article-info-content") \
        .find("a", {"data-track-action": "view doi"}) \
        .get_text() \
        .replace("https://doi.org/", "") if content_soup.select_one("#article-info-content") else None
    return abstract, doi


def get_abstract_acp(link) -> any:
    time.sleep(1)
    log.info("https://www.nature.com" + link)
    try:
        d = requests.get("https://www.acpjournals.org" + link)
    except:
        return None
    content_soup = BeautifulSoup(d.text, "lxml")
    if not content_soup.select_one(".hlFld-Fulltext"):
        return None
    abstract = content_soup.select_one(".hlFld-Fulltext").find_all("p")[:5]
    return " ".join([parr.get_text() for parr in abstract])
