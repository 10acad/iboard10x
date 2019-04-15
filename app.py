import math

import pandas as pd
import flask
#from flask_caching import Cache

import dash
import dash_core_components as dcc
import dash_html_components as html
import dateutil.parser

from dbManager import rds_manager

server = flask.Flask(__name__)

# # Serve JS and CSS files locally instead of from global CDN
# # app.scripts.config.serve_locally = True
# # app.css.config.serve_locally = True
#
# cache = Cache(app.server, config={
#     'CACHE_TYPE': 'filesystem',
#     'CACHE_DIR': 'cache-directory',
#     'CACHE_THRESHOLD': 50  # should be equal to maximum number of active users
# })


app = dash.Dash(__name__, server=server, url_base_pathname='/')

app.css.append_css({
    "external_url": "https://codepen.io/chriddyp/pen/bWLwgP.css"
})

url='https://cdn.rawgit.com/plotly/dash-app-stylesheets/2d266c578d2a6e8850ebce48fdb52759b2aef506/stylesheet-oil-and-gas.css'
app.css.append_css({'external_url': url})

#app.scripts.config.serve_locally=True
#app.css.config.serve_locally=True

app.config.suppress_callback_exceptions = True

rds_manager = rds_manager()

