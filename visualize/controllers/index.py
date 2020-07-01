import ast
from collections import Counter
from datetime import datetime, timedelta

import networkx as nx
import numpy as np
import pandas as pd

import plotly.graph_objs as go
from data.model import return_articles_per_source, return_keywords


def return_figures():
    """
    Creates plotly visualizations showing aggregated info:
        Number of articles per source
        Count of appearance of keywords in abstract, for a specific period
        Network of keywords appearing together in an abstract, for a specific period
        Evolution of appearance of keywords over time

    Args:
        None

    Returns:
        figures (list): list containing the plotly visualizations

    """

    # REPORTING ON SCRAPED SOURCES #
    ###################################################################################################################

    # this chart plots the number of unique articles scraped per source  as a bar chart
    articles_per_source = return_articles_per_source()
    total = articles_per_source.nb_articles.sum()

    graph_articles_per_source = [
        go.Bar(
            x=articles_per_source.Source,
            y=articles_per_source.nb_articles,
            text=articles_per_source.nb_articles,
            textposition="auto",
            hoverinfo="none",
        )
    ]

    layout_articles_per_source = go.Layout(margin=go.layout.Margin(l=50, b=100))

    # EXPLORATION OF BUSINESS KEYWORDS #
    ###################################################################################################################
    # this chart plots the number of occurrences of the top n keywords in the past d days

    # Parameters:
    # number of keywords to show:
    n = 50
    # timeframe in days
    d = 7

    keywords = return_keywords()
    keywords.drop_duplicates(subset="ID", keep="first", inplace=True)
    keywords["PublishedDate"] = keywords["PublishedDate"].apply(
        lambda x: try_parsing_date(x)
    )

    # generate two dataframes, one wit keywords before d days ago and one with keywords in the past d days
    t = (datetime.today() - timedelta(days=d)).date()
    after = keywords[keywords.PublishedDate >= t]["abstract_kw"]
    before = keywords[keywords.PublishedDate < t]["abstract_kw"]

    # combine all keywords of dataframes into one dictionary
    after_kw = Counter({})
    before_kw = Counter({})
    for abstr in after:
        dict_to_add = Counter(ast.literal_eval(abstr))
        after_kw = after_kw + dict_to_add
    for abstr in before:
        dict_to_add = Counter(ast.literal_eval(abstr))
        before_kw = before_kw + dict_to_add
    recurring_entities = list((after_kw & before_kw).keys())
    top_n = after_kw.most_common(n)
    col = []
    for key in list(zip(*top_n)):
        if key in recurring_entities:
            col.append("steelblue")
        else:
            col.append("darkgoldenrod")

    graph_keyword_count = [
        go.Bar(
            x=list(zip(*top_n)),
            y=list(zip(*top_n)),
            text=list(zip(*top_n)),
            textposition="auto",
            hoverinfo="none",
            marker={"color": col},
        )
    ]

    layout_keyword_count = go.Layout(
        height=500,
        width=800,
        margin=dict(l=50, r=50, t=50, b=120),
        annotations=[
            dict(
                xref="paper",
                yref="paper",
                x=0,
                xanchor="left",
                y=-0.35,
                yanchor="bottom",
                showarrow=False,
                align="left",
                text="<i>Only keywords of articles published during the past "
                + str(d)
                + " days are taken into account."
                + "<br>"
                + "New keywords are accentuated in gold"
                + "</i>",
            )
        ],
    )

    # this chart shows a network view of keywords
    # ------------------------------------------------------

    kw = Counter({})
    for abstr in return_keywords()["abstract_kw"]:
        dict_to_add = Counter(ast.literal_eval(abstr))
        kw = kw + dict_to_add

    adj = return_keywords()
    adj.drop_duplicates(subset="ID", keep="first", inplace=True)
    for keyword in kw.keys():
        adj[keyword] = adj["abstract_kw"].apply(
            lambda x: ast.literal_eval(x)[keyword]
            if keyword in ast.literal_eval(x).keys()
            else 0
        )
    evolution = adj.copy()  # for plot 4
    adj["PublishedDate"] = adj["PublishedDate"].apply(lambda x: try_parsing_date(x))
    adj = adj[adj.PublishedDate >= t]
    adj = adj.groupby(["ID"], as_index=True)[list(kw.keys())].sum()
    adj = adj.T
    adj.sort_index(inplace=True)
    # adjacency matrix of keywords based on articles
    A = np.dot(adj, adj.T)
    adj = pd.DataFrame(A, index=adj.index, columns=adj.index)

    gr = nx.from_numpy_matrix(A)
    matching = {x: adj.index.values[x] for x in range(len(adj.index))}
    gr = nx.relabel_nodes(gr, matching)

    # Draw graph
    # ref: https://plotly.com/python/network-graphs/

    # choose layout
    # pos = nx.shell_layout(gr)
    pos = nx.spiral_layout(gr)
    # pos = nx.fruchterman_reingold_layout(gr)

    edge_x = []
    edge_y = []
    for edge in gr.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        line=dict(width=0.5, color="#888"),
        hoverinfo="none",
        mode="lines",
    )

    node_x = []
    node_y = []
    for node in gr.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

    node_labels = list(gr.nodes())

    node_trace = go.Scatter(
        x=node_x, y=node_y, text=node_labels, mode="markers+text", hoverinfo="text"
    )

    # Resize node points by the number of connections.
    node_adjacencies = []
    for node, adjacencies in enumerate(gr.adjacency()):
        node_adjacencies.append(len(adjacencies[1]))
    node_trace.marker.size = node_adjacencies

    graph_network = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            showlegend=False,
            hovermode="closest",
            margin=dict(b=50, l=20, r=20, t=50),
            annotations=[
                dict(
                    xref="paper",
                    yref="paper",
                    x=0,
                    xanchor="left",
                    y=-0.1,
                    yanchor="bottom",
                    showarrow=False,
                    align="left",
                    text="<i>Only keywords of articles published during the past "
                    + str(d)
                    + " days are taken "
                    + "<br>"
                    + "into account."
                    + "</i>",
                )
            ],
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        ),
    )

    # this chart plots the evolution of keywords over time
    # ------------------------------------------------------

    evolution = evolution.groupby(["PublishedDate"], as_index=True)[
        list(kw.keys())
    ].sum()
    evolution.sort_values(by="PublishedDate", inplace=True)

    graph_keyword_evolution = go.Figure()
    for keyword in kw.keys():
        graph_keyword_evolution.add_trace(
            go.Scatter(
                x=evolution.index, y=evolution[keyword], mode="lines", name=keyword
            )
        )

    graph_keyword_evolution.update_layout(
        height=500, width=800, margin=dict(l=20, r=20, t=50, b=100)
    )

    # append all charts to the figures list
    figures = []
    figures.append(
        dict(data=graph_articles_per_source, layout=layout_articles_per_source)
    )
    figures.append(dict(data=graph_keyword_count, layout=layout_keyword_count))
    figures.append(dict(data=graph_network))
    figures.append(dict(data=graph_keyword_evolution))

    return figures


def try_parsing_date(text):
    if not text:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S+00:00", "%Y-%m-%d"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    raise ValueError('no valid date format found for "' + text + '"')
