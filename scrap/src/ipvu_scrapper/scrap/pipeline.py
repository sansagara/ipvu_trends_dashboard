from kedro.pipeline import node, Pipeline

from .nodes import scrap_lancet, scrap_elsevier, scrap_pubmed, scrap_nejm, scrap_ema, scrap_uptodate, scrap_nature, \
    scrap_acp


def create_pipeline(**kwargs):
    return Pipeline(
        [
            node(
                func=scrap_lancet,
                inputs=None,
                outputs='raw_lancet',
                name="scrap_lancet"),
            node(
                func=scrap_elsevier,
                inputs=None,
                outputs='raw_elsevier',
                name="scrap_elsevier"),
            node(
                func=scrap_pubmed,
                inputs=None,
                outputs='raw_pubmed',
                name="scrap_pubmed"),
            node(
                func=scrap_nejm,
                inputs=None,
                outputs='raw_nejm',
                name="scrap_nejm"),
            node(
                func=scrap_ema,
                inputs=None,
                outputs='raw_ema',
                name="scrap_ema"),
            node(
                func=scrap_uptodate,
                inputs=None,
                outputs='raw_uptodate',
                name="scrap_uptodate"),
            node(
                func=scrap_nature,
                inputs=None,
                outputs='raw_nature',
                name="scrap_nature"),
            node(
                func=scrap_acp,
                inputs=None,
                outputs='raw_acp',
                name="scrap_acp"),
        ]
    )
