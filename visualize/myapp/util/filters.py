from myapp import app
from ast import literal_eval


@app.template_filter('evaluate')
def evaluate(text):
    """Evaluates a string."""
    return literal_eval(text)
