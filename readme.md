# COVID-19 Journals scraper and NLP Pipeline
This project is comprised of 2 parts: A scrap/NLP pipeline and a web application to show results.
The main motivation is to make easy to analyse scientific publications from different prestigious sources (scientific journals and websites) on a very novel topic: COVID-19
We then can show results on a website so any user can browse through results and find articles using keywords and other properties.
## 1 - Scrap and NLP Pipeline
The first part of the project is an ETL/Scrap pipeline built using [Kedro](https://github.com/quantumblacklabs/kedro), a python tool for creating simple pipelines.
It scraps covid-19 related Scientific papers and publications from different EMEA and worldwide sources/Journals, like:

- Lancet
- EMA
- ELSEVIER
- NEJM
- UPTODATE
- NATURE
- PUBMED

The pipeline has different nodes that:
1. Scraps websites using Beautifulsoup or API calls.
2. Creates Pandas Dataframes with article details.
3. Runs several NLP processes (Tokenization, Lemmatization, Sentiment, etc) .
4. Stores results in a SQLite DB to be used by the flask app on the dashboard website.

### Prerequisites
Dependencies are declared in `src/requirements.txt` for pip installation and `src/environment.yml` for conda installation.
To install them, run:
```
kedro install
```

### Running Kedro
You can run the Kedro project (Pipeline) with:
```
kedro run
```

### Demo dataset
To get an idea of the structure of the dataset that's created on the pipeline, you can look at:
[Primary Dataset](https://raw.githubusercontent.com/sansagara/ipvu_trends_dashboard/master/scrap/data/03_primary/articles/prm_articles.csv/2020-05-25T18.37.51.354Z/prm_articles.csv)

The SQLite DB that's used on the Flask visualizer is here:
[articles.db](https://github.com/sansagara/ipvu_trends_dashboard/blob/master/scrap/data/db/articles.db)

### Scrap node code
Scrap details can be seen on the scrap nodes here:
https://github.com/sansagara/ipvu_trends_dashboard/blob/master/scrap/src/ipvu_scrapper/scrap/nodes.py

### NLP Process node code
NLP processing can be seen on the process nodes here:
https://github.com/sansagara/ipvu_trends_dashboard/blob/master/scrap/src/ipvu_scrapper/process/nodes.py


## 2 - Flask Dashboard Application
This is a Flask application that displays a dashboard (Like the one on the Flask lesson)
It shows several charts and tables with different information like keyword frequency, sentiment, etc.

### Prerequisites
To install the flask app, you need:

- python3
- python packages in the requirements.txt file

Install the packages with
 `pip install -r requirements.txt`

### Running Flask
On a MacOS/linux system, installation is easy. 
Open a terminal, and go into the directory with the flask app files. 
Run `python visualize/myapp.py` in the terminal.

### Video Demo
Be sure to see my demo video on YouTube!
[Video Walkthrough](https://youtu.be/VzAYcjGuKsE)

### Deployed App
The flask application portion is deployed on Heroku for easy demoing purposes:
[App on Heroku](https://ipvu-dashboard.herokuapp.com/)