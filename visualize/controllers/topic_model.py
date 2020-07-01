import plotly.graph_objs as go
from plotly.subplots import make_subplots
import plotly.express as px
import pandas as pd
import numpy as np
import ast
from math import ceil
from collections import Counter
import gensim
import gensim.corpora as corpora

from data.model import return_keywords


def return_topic_figures(n_topics=5):
    """Creates plotly visualizations generated from topic model

    Args:
        n_topics = number of topics to generate from articles, default 5

    Returns:
        figures (list): list containing the plotly visualizations

    """

    ### import data ###

    data = return_keywords()
    data_for_topics = data["abstract_kw"].apply(
        lambda x: list(ast.literal_eval(x).keys())
    )

    ### Build topic model ###

    # parameters
    n_topics = n_topics

    # Create Dictionary
    id2word = corpora.Dictionary(data_for_topics)

    # Create Corpus: Term Document Frequency
    corpus = [id2word.doc2bow(text) for text in data_for_topics]

    # Build LDA model
    lda_model = gensim.models.ldamodel.LdaModel(
        corpus=corpus,
        id2word=id2word,
        num_topics=n_topics,
        random_state=100,
        update_every=1,
        chunksize=10,
        passes=10,
        alpha="symmetric",
        iterations=100,
        per_word_topics=True,
    )

    topics = lda_model.show_topics(formatted=False)
    data_flat = [w for w_list in data_for_topics for w in w_list]
    counter = Counter(data_flat)
    out = []
    for i, topic in topics:
        for word, weight in topic:
            out.append([word, i, weight, counter[word]])
    df = pd.DataFrame(out, columns=["word", "topic_id", "importance", "word_count"])

    specs = np.full((ceil(n_topics / 2), 2), {"secondary_y": True})
    topic_bar_charts = make_subplots(
        rows=ceil(n_topics / 2),
        cols=2,
        specs=specs.tolist(),
        horizontal_spacing=0.1,
        vertical_spacing=0.15,
    )
    row, col = (0, 0)
    for topic in range(n_topics):
        if (topic % 2) != 0:
            col = 2
        else:
            col = 1
            row += 1
        color = px.colors.qualitative.Vivid[topic]
        topic_bar_charts.add_trace(
            go.Bar(
                x=df.loc[df.topic_id == topic, "word"],
                y=df.loc[df.topic_id == topic, "word_count"],
                width=0.5,
                opacity=0.3,
                marker_color=color,
                name=("Topic " + str(topic) + " word count"),
            ),
            secondary_y=False,
            row=row,
            col=col,
        )
        topic_bar_charts.add_trace(
            go.Bar(
                x=df.loc[df.topic_id == topic, "word"],
                y=df.loc[df.topic_id == topic, "importance"],
                width=0.2,
                marker_color=color,
                name=("Topic " + str(topic) + " weight"),
            ),
            secondary_y=True,
            row=row,
            col=col,
        )
        topic_bar_charts.update_layout(barmode="overlay")

    topic_bar_charts.update_layout(
        height=800, width=1000, margin=dict(l=50, r=50, t=50, b=100)
    )

    # append all charts
    figures = [dict(data=topic_bar_charts)]

    return figures
