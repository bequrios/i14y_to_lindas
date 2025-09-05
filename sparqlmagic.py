# sparqlmagic.py

from IPython.core.magic import register_cell_magic
from pygments import highlight
from pygments.lexers import SparqlLexer
from pygments.formatters import HtmlFormatter
from IPython.display import HTML, display
import requests
import pandas as pd

pd.set_option("display.max_rows", None)     # show all rows
pd.set_option("display.max_columns", None)  # show all columns
pd.set_option("display.max_colwidth", None) # don't truncate long strings
pd.set_option("display.width", None)        # don't wrap columns into new line

# Default endpoint can be changed after import
sparql_endpoint = "https://ld.admin.ch/query"


@register_cell_magic
def sparql(line, cell):
    """
    Pretty-print a SPARQL query, run it, return a Pandas DataFrame.

    Usage:
      %%sparql [varname] [endpoint_url]

    Examples:
      %%sparql
      SELECT * WHERE { ?s ?p ?o } LIMIT 5

      %%sparql df
      SELECT * WHERE { ?s ?p ?o } LIMIT 5

      %%sparql df https://dbpedia.org/sparql
      SELECT * WHERE { ?s ?p ?o } LIMIT 5
    """
    from sparqlmagic import sparql_endpoint  # ensure updated value is used

    parts = line.strip().split()
    varname, endpoint = None, sparql_endpoint

    if len(parts) == 1:
        if parts[0].startswith("http"):
            endpoint = parts[0]
        else:
            varname = parts[0]
    elif len(parts) >= 2:
        varname, endpoint = parts[0], parts[1]

    query = cell.strip()

    # Highlight query
    html = highlight(query, SparqlLexer(), HtmlFormatter(full=True, style="colorful"))
    display(HTML(html))

    # Run query
    response = requests.get(
        endpoint,
        params={"query": query},
        headers={
            "User-Agent": "JupyterSPARQLMagic/0.1",
            "Accept": "application/sparql-results+json"
        },
    )
    response.raise_for_status()
    data = response.json()

    # Convert to DataFrame
    df = pd.json_normalize(data["results"]["bindings"])

    # Store variable if requested
    if varname:
        get_ipython().user_ns[varname] = df

    # Style with scrollbars and word wrapping
    styled = (
        df.style
        .set_table_attributes('style="display:block; max-height:400px; overflow:auto; white-space:normal; word-wrap:break-word;"')
        .set_table_styles(
            [{
                "selector": "thead th",
                "props": [
                    ("position", "sticky"),
                    ("top", "0"),
                    ("background-color", "#f0f0f0"),
                    ("z-index", "2")
                ]
            }]
        )
    )
    display(styled)
