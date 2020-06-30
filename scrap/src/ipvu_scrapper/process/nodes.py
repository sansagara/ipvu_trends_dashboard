import re
from collections import Counter
from datetime import datetime

import pandas as pd
from kedro.pipeline.decorators import log_time
from nltk.corpus import stopwords
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.tokenize import word_tokenize, sent_tokenize

url_regex = 'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'


def join_articles(raw_elsevier: pd.DataFrame,
                  raw_ema: pd.DataFrame,
                  raw_lancet: pd.DataFrame,
                  raw_nejm: pd.DataFrame,
                  raw_pubmed: pd.DataFrame,
                  raw_uptodate: pd.DataFrame,
                  raw_nature: pd.DataFrame,
                  raw_acp: pd.DataFrame,
                  ) -> pd.DataFrame:
    """
    Join articles from different sources into a single dataset.
    Add the source and try to parse the PublishedDate string.
    :param raw_elsevier: raw elsevier dataset
    :param raw_ema: raw ema dataset
    :param raw_lancet: raw lancet dataset
    :param raw_nejm: raw nejm dataset
    :param raw_pubmed: raw pubmed dataset
    :param raw_uptodate: raw uptodate dataset
    :param raw_nature: raw nature dataset
    :param raw_acp: raw nature dataset
    :return: joined pandas dataset int_articles
    """
    raw_elsevier = raw_elsevier[['ID', 'DOI', 'Type', 'Title', 'Abstract', 'PublishedDate']] \
        .assign(Source='ELSEVIER')
    raw_elsevier['PublishedDate'] = pd.to_datetime(raw_elsevier['PublishedDate'],
                                                   infer_datetime_format=True,
                                                   errors='coerce')

    raw_ema = raw_ema[['ID', 'Title', 'Abstract', 'PublishedDate']] \
        .assign(Source='EMA') \
        .assign(DOI='N/A') \
        .assign(Type='Update')
    raw_ema['PublishedDate'] = pd.to_datetime(raw_ema['PublishedDate'] + " " + str(datetime.now().year),
                                              format="%d %B %Y",
                                              infer_datetime_format=True,
                                              errors='coerce')

    raw_lancet = raw_lancet[['ID', 'DOI', 'Type', 'Title', 'Abstract', 'PublishedDate']] \
        .assign(Source='LANCET')
    raw_lancet['PublishedDate'] = pd.to_datetime(raw_lancet['PublishedDate'],
                                                 infer_datetime_format=True,
                                                 errors='coerce')
    raw_lancet['PublishedDate'].fillna(method='ffill', inplace=True)

    raw_nejm = raw_nejm[['ID', 'DOI', 'Type', 'Title', 'Abstract', 'PublishedDate']] \
        .assign(Source='NEJM')
    raw_nejm['PublishedDate'] = pd.to_datetime(raw_nejm['PublishedDate'] + " " + str(datetime.now().year),
                                               format="%b %d %Y",
                                               infer_datetime_format=True,
                                               errors='coerce')
    raw_nejm['PublishedDate'].fillna(method='ffill', inplace=True)

    raw_pubmed = raw_pubmed[['ID', 'DOI', 'Type', 'Title', 'Abstract', 'PublishedDate']] \
        .assign(Source='PUBMED')
    raw_pubmed['PublishedDate'] = pd.to_datetime(raw_pubmed['PublishedDate'],
                                                 infer_datetime_format=True,
                                                 errors='coerce')

    raw_uptodate = raw_uptodate[['ID', 'Type', 'Title', 'Abstract', 'PublishedDate']] \
        .assign(Source='UPTODATE') \
        .assign(DOI='N/A')
    raw_uptodate['PublishedDate'] = pd.to_datetime(raw_uptodate['PublishedDate'],
                                                   infer_datetime_format=True,
                                                   errors='coerce')

    raw_nature = raw_nature[['ID', 'DOI', 'Type', 'Title', 'Abstract', 'PublishedDate']] \
        .assign(Source='NATURE')
    raw_nature['PublishedDate'] = pd.to_datetime(raw_nature['PublishedDate'],
                                                 infer_datetime_format=True,
                                                 errors='coerce')
    raw_nature['PublishedDate'].fillna(method='ffill', inplace=True)

    raw_acp = raw_acp[['ID', 'DOI', 'Type', 'Title', 'Abstract', 'PublishedDate']] \
        .assign(Source='ACP')
    raw_acp['PublishedDate'] = pd.to_datetime(raw_acp['PublishedDate'],
                                              infer_datetime_format=True,
                                              errors='coerce')

    return pd.concat([raw_elsevier, raw_ema, raw_lancet, raw_nejm, raw_pubmed, raw_uptodate, raw_nature, raw_acp],
                     ignore_index=True,
                     sort=False).dropna(subset=['ID']).assign(ScrapDate=pd.to_datetime('today'))


@log_time
def lemmatize(int_articles: pd.DataFrame, keywords: list, sw: list, stems: dict) -> pd.DataFrame:
    """
    Process text and add NLP features.
    :param int_articles: the joined int_articles.
    :param keywords: a list of keywords to search on corpus.
    :param sw: a list of stopwords (words to remove)
    :param stems: a dict of words with similar meaning for replacement
    :return: a dataset with new features calculated.
    """
    int_articles['title_words'] = int_articles.apply(lambda row: get_words(get_tokens(row.Title), sw, stems), axis=1)
    int_articles['abstract_sentences'] = int_articles.apply(lambda row: get_tokens(row.Abstract), axis=1)
    int_articles['abstract_words'] = int_articles.apply(lambda row: get_words(row.abstract_sentences, sw, stems),
                                                        axis=1)
    int_articles['abstract_length'] = int_articles['abstract_words'].str.len()
    int_articles['abstract_wc'] = int_articles.apply(lambda row: word_count(row.abstract_words), axis=1)
    int_articles['abstract_kw'] = int_articles.apply(lambda row: word_count(row.abstract_words, keywords), axis=1)
    int_articles['abstract_kw_sum'] = int_articles.apply(lambda row: sum(row.abstract_kw.values()), axis=1)
    int_articles['abstract_sentiment'] = int_articles.apply(lambda row: get_sentiment(row.abstract_sentences[:3]),
                                                            axis=1)

    return int_articles.drop(['Title', 'Abstract'], axis=1)


def drop_duplicates(prm_articles: pd.DataFrame, db_articles_in: pd.DataFrame) -> pd.DataFrame:
    """
    Join new articles with existing ones on DB and handle duplicates.
    :param prm_articles: New articles coming from this pipeline run.
    :param db_articles_in: Existing articles already stored in DB
    :return:
    """
    return pd.concat([prm_articles, db_articles_in],
                     ignore_index=True,
                     sort=False) \
        .drop_duplicates('ID') \
        .sort_values(by=['ScrapDate'])


def word_count(abstract_words: list, keywords: list = None) -> dict:
    # Get word count
    counts = Counter(abstract_words)
    if keywords:
        return dict((kw, counts[kw]) for kw in keywords if kw in counts)
    else:
        return dict(counts.most_common(20))


def get_tokens(text: str) -> list:
    # Stop processing if not string
    if not isinstance(text, str):
        return []

    # Check for URLS in corpus
    detected_urls = re.findall(url_regex, text)
    for url in detected_urls:
        text = text.replace(url, " urlplaceholder")

    # Tokenize into sentences (Can be unpacked into words later)
    tokens = sent_tokenize(text)
    sentences = []
    for sent in tokens:
        # Lemmatize nouns and verbs
        lem = [WordNetLemmatizer().lemmatize(word) for word in word_tokenize(sent) if
               word not in stopwords.words("english")]
        sentences.append(' '.join(WordNetLemmatizer().lemmatize(word, pos='v') for word in lem))
    return sentences


def get_words(sentences: list, custom_sw: list, stems: dict) -> list:
    # Remove punctuation and lowercase
    if not sentences:
        return []

    sw = list(stopwords.words("english")) + custom_sw
    words = [re.sub(r"[^a-zA-Z0-9\-]", "", word.lower()) for sent in sentences for word in sent.split()]
    words = [stems[word] if word in stems else word for word in words]
    return [word for word in words if word not in sw]


def get_sentiment(sentences: list):
    return round(SentimentIntensityAnalyzer().polarity_scores('. '.join(sentences))['compound'], 4)
