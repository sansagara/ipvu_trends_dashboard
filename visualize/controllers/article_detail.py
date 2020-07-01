import ast
import base64
import io
from collections import Counter

import plotly.graph_objs as go
from PIL import Image
from wordcloud import WordCloud

from data.model import return_article_details, return_article_sentiments


def return_detail_figures(article_id="ID:126981"):
    """
    Creates plots visualizing a particular article:
        Wordcloud of title and keywords (stripped of stopwords, stemmed)
        Occurence of keywords in the abstract
        Sentiment of article abstract, compared to average sentiment (visualized via violin plot)

    Args:
        article_id (str): list of countries for filtering the data

    Returns:
        title (str): title words of the article
        fig_wordcloud (image): wordcloud image in png
        figures (list): list containing the plotly visualizations
    """

    # collect data
    data = return_article_details(article_id)
    if len(data) == 0:
        figures = []
        return figures

    # this chart creates a word cloud of the abstract and title

    text_title = ' '.join([str(word) for word in ast.literal_eval(data['title_words'][0])])
    text_abstract = ' '.join([str(word) for word in ast.literal_eval(data['abstract_words'][0])])
    text = text_title + ' ' + text_abstract

    wordcloud = Image.new('RGB', (550, 450), (255, 255, 255))
    bg_w, bg_h = wordcloud.size
    img_w, img_h = (550, 350)
    offset = ((bg_w - img_w) // 2, (bg_h - img_h))
    pil_img = WordCloud(background_color="white", width=img_w, height=img_h, prefer_horizontal=0.9,
                        random_state=123).generate(text).to_image()
    wordcloud.paste(pil_img, offset)
    img = io.BytesIO()
    wordcloud.save(img, "PNG")
    img.seek(0)
    fig_wordcloud = "data:image/png;base64,"
    fig_wordcloud += base64.b64encode(img.getvalue()).decode('utf8')

    # This chart creates a bar chart of the top keywords ###
    kw = Counter(ast.literal_eval(data['abstract_kw'][0]))
    top = kw.most_common(10)
    if top:
        terms = list(zip(*top))[0]
        counts = list(zip(*top))[1]
        graph_keywords = [go.Bar(x=terms, y=counts, text=counts, textposition='auto', hoverinfo="none")]
    else:
        graph_keywords = go.Figure()
        graph_keywords.update_layout(annotations=[
            dict(xref='paper', yref='paper', x=0, y=1, align='left', showarrow=False, text='No keywords available.',
                 font={'size': 22})], xaxis={'visible': False}, yaxis={'visible': False})

    ### Violin plot of sentiment ###

    if not data['abstract_sentiment'][0]:
        graph_violin_sent = go.Figure()
        graph_violin_sent.update_layout(annotations=[
            dict(xref='paper', yref='paper', x=0, y=1, align='left', showarrow=False,
                 text='Article sentiment not available ' + '<br>' + 'for this article.', font={'size': 22})],
            xaxis={'visible': False}, yaxis={'visible': False})
    else:
        groups = return_article_sentiments()

        graph_violin_sent = go.Figure(
            data=go.Violin(y=groups['Sentiment'], box_visible=True, line_color='black', meanline_visible=True,
                           opacity=0.6, fillcolor='steelblue', x0=' ', hoverinfo='skip'))
        graph_violin_sent.add_shape(type="line", x0=-0.4, y0=data['abstract_sentiment'][0], x1=0.4,
                                    y1=data['abstract_sentiment'][0], line=dict(color="darkgoldenrod", width=4))
        graph_violin_sent.update_yaxes(ticktext=["negative", "neutral", "positive"],
                                       tickvals=[-1, 0, 1, groups.index.max()], )

        graph_violin_sent.update_layout(yaxis_zeroline=False, annotations=[
            dict(xref='paper', yref='paper', x=0, xanchor='left', y=-0.1, yanchor='bottom', showarrow=False,
                 align='left', text='<i>Article sentiment indicated in gold.</i>')], height=600)

    # append all charts
    figures = [dict(data=graph_keywords), dict(data=graph_violin_sent)]
    return text_title, data['DOI'][0], data['Source'][0], fig_wordcloud, figures
