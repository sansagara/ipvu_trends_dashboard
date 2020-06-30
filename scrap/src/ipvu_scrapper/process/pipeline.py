from kedro.pipeline import node, Pipeline

from .nodes import join_articles, lemmatize, drop_duplicates


def create_pipeline(**kwargs):
    return Pipeline(
        [
            node(
                func=join_articles,
                inputs=['raw_elsevier', 'raw_ema', 'raw_lancet', 'raw_nejm',
                        'raw_pubmed', 'raw_uptodate', 'raw_nature', 'raw_acp'],
                outputs='int_articles',
                name="join"
            ),
            node(
                func=lemmatize,
                inputs=['int_articles', 'params:keywords', 'params:stopwords', 'params:stems'],
                outputs='prm_articles',
                name="lemmatize"
            ),
            node(
                func=drop_duplicates,
                inputs=['prm_articles', 'db_articles_in'],
                outputs='db_articles_out',
                name="drop_duplicates"
            ),
        ]
    )
