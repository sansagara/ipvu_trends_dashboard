from myapp import app
import json
import plotly
from flask import render_template
from data.wrangle_data import return_figures, return_articles


@app.route('/')
@app.route('/index')
def index():

    figures = return_figures()

    # plot ids for the html id tag
    ids = ['figure-{}'.format(i) for i, _ in enumerate(figures)]

    # Convert the plotly figures to JSON for javascript in html template
    figures_json = json.dumps(figures, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('index.html',
                           ids=ids,
                           figuresJSON=figures_json)


@app.route('/articles')
def articles():
    df = return_articles()
    return render_template('articles.html',
                           articles=[df.to_html(classes='table')],
                           titles=df.columns.values)
