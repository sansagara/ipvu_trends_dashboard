import json

import plotly
from flask import render_template, request

from controllers.article_detail import return_detail_figures
from controllers.index import return_figures
from controllers.topic_model import return_topic_figures
from data.model import return_articles, return_distinct_sources, articles_count, last_update
from myapp import app


@app.route('/')
@app.route('/index')
def index():
    figures = return_figures()

    # plot ids for the html id tag
    ids = ['figure-{}'.format(i) for i, _ in enumerate(figures)]

    # Convert the plotly figures to JSON for javascript in html template
    figures_json = json.dumps(figures, cls=plotly.utils.PlotlyJSONEncoder)

    topic_figures = return_topic_figures(n_topics=5)
    # plot ids for the html id tag
    ids_topic = ['figure-topic-{}'.format(i) for i, _ in enumerate(topic_figures)]
    # Convert the plotly figures to JSON for javascript in html template
    topics_figures_json = json.dumps(topic_figures, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('index.html',
                           ids=ids,
                           articles_count=articles_count(),
                           last_update=last_update(),
                           figuresJSON=figures_json,
                           ids_topic=ids_topic,
                           topics_figures_json=topics_figures_json)


@app.route('/articles')
def articles():
    return render_template('articles.html',
                           articles=return_articles(request.args),
                           sources=return_distinct_sources(),
                           args=request.args,
                           columns=['ID', 'Type', 'Source', 'Title',
                                    'Keywords', 'Keyword density'])


@app.route('/articles/<article_id>/<doi2>')
@app.route('/articles/<article_id>')
def article_detail(article_id, doi2=""):
    if doi2:
        article_id = article_id + "/" + doi2
    title, doi, source, wordcloud, figures = return_detail_figures(article_id)
    ids = ['figure-{}'.format(i) for i, _ in enumerate(figures, start=0)]
    figures_json = json.dumps(figures, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('article_detail.html',
                           article_id=article_id,
                           doi=doi,
                           source=source,
                           title=title,
                           ids=ids,
                           figuresJSON=figures_json,
                           image=wordcloud)
