def query_sqlite(query: str, params: dict = None, one: bool = False) -> any:
    print(query)
    print(params)
    print()
    import sqlite3
    conn = sqlite3.connect("data/articles.db",
                           detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
    cur = conn.cursor()
    if params:
        cur.execute(query, params)
    else:
        cur.execute(query)
    if one:
        return cur.fetchone()
    else:
        return cur.fetchall()


def return_articles(request: dict):
    sql = "SELECT ID, DOI, Type, Source, PublishedDate, title_words, abstract_length, abstract_kw, abstract_kw_sum " \
          "FROM articles"
    where = []
    params = {}
    if 'source' in request and request['source']:
        where.append("Source = :source")
        params['source'] = request['source']
    if 'keywords' in request and request['keywords']:
        for idx, kw in enumerate(request['keywords'].split(',')):
            where.append("abstract_kw LIKE :kw{}".format(idx))
            params['kw{}'.format(idx)] = '%' + kw.strip() + '%'
    if 'date' in request and request['date']:
        where.append("DATE(PublishedDate) BETWEEN :date AND '2020-12-31'")
        params['date'] = request['date']
    if where:
        sql = '{} WHERE {}'.format(sql, ' AND '.join(where))
    sql = sql + " ORDER BY abstract_kw_sum DESC LIMIT 20"
    return query_sqlite(sql, params)


def return_distinct_sources():
    return query_sqlite("SELECT DISTINCT Source FROM articles")


def return_articles_per_source():
    import pandas as pd
    return pd.read_sql("SELECT Source, count(distinct ID) as nb_articles "
                       "FROM articles "
                       "GROUP BY Source "
                       "ORDER BY Source asc ",
                       "sqlite:///data/articles.db")


def return_keywords():
    import pandas as pd
    return pd.read_sql("SELECT ID, PublishedDate, abstract_kw "
                       "FROM articles "
                       "ORDER BY ScrapDate DESC ",
                       "sqlite:///data/articles.db")


def return_article_details(article_id):
    import pandas as pd
    query = '''SELECT ID, DOI, Source, title_words, abstract_words, abstract_kw, abstract_sentiment
        FROM articles
        WHERE ID = "{}"
        ORDER BY ScrapDate DESC
        LIMIT 1'''
    return pd.read_sql(str(query).format(article_id),
                       "sqlite:///data/articles.db")


def return_article_sentiments():
    import pandas as pd
    return pd.read_sql("SELECT abstract_sentiment as Sentiment "
                       "FROM articles ",
                       "sqlite:///data/articles.db")


def articles_count():
    return query_sqlite("SELECT COUNT(*) FROM articles", one=True)


def last_update():
    return query_sqlite("SELECT MAX(ScrapDate) as '[timestamp]' FROM articles", one=True)[0]
