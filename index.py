# -*- coding: utf-8 -*-
import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import flask
import plotly.plotly as py
from plotly import graph_objs as go
import math
from app import app, server, rds_manager
from apps import users

tabs_styles = {
    'height': '44px'
}
tab_style = {
    'borderBottom': '1px solid #d6d6d6',
    'padding': '6px',
    'fontWeight': 'bold'
}

tab_selected_style = {
    'borderTop': '1px solid #d6d6d6',
    'borderBottom': '1px solid #d6d6d6',
    #'backgroundColor': '#ED1F33',
    #'color': 'white',
    'color': "#ED1F33",
    'padding': '6px'
}


app.layout = html.Div(
    [
        # header
        html.Div([

            html.Div(
                html.Img(src=app.get_asset_url('x10logo.png'),height="100%")
                ,style={"float":"left","height":"100%"}),

            html.Span("10 Academy Dash Board",
                      style={
                          "color": "#ffffff",
                          "fontWeight": "normal",
                          "float":"right",
                          "fontSize": "20",
                          "marginBottom": "0",
                      },
                      className='app-title'),

            ],
            className="row header",
            style={
                "color": "#ED1F33",
                "fontWeight": "bold",
                "fontSize": "20",
                "background-color":"#ED1F33",
            },
            ),

        # tabs
        html.Div([

            dcc.Tabs(
                id="tabs",
                style={"height":"20","verticalAlign":"middle"},
                children=[
                    dcc.Tab(label="Users", value="users_tab", style=tab_style, selected_style=tab_selected_style),
                    dcc.Tab(label="Engagement", value="engagement_tab", style=tab_style, selected_style=tab_selected_style),
                    #dcc.Tab(id="skill_tab",label="Skill Profile", value="skill_tab",
                    # style=tab_style, selected_style=tab_selected_style),
                ],
                value="users_tab",
            ),
            html.Div(id='tabs-content-inline')
        ],
            className="row tabs_div"
            ),

        #
        html.Div('',
            className="row header2",
            style={'color':"#ED1F33"},
        ),

        # divs that save dataframe for each tab
        html.Div(rds_manager.read_latest_users().to_json(orient="split"),
                id="users_df",
                style={"display": "none"},
            ),
        html.Div(rds_manager.read_latest_log_summary().to_json(orient="split"), # leads df
                     id="engagement_df",
                     style={"display": "none"}
            ), 
        #html.Div(rds_manager.get_skill().to_json(orient="split"),    # cases df
        #             id="skill_df",
        #             style={"display": "none"}
        #    ),



        # Tab content
        html.Div(id="tab_content", className="row", style={"margin": "2% 3%"}),
        
        #html.Link(href="https://use.fontawesome.com/releases/v5.2.0/css/all.css",rel="stylesheet"),
        #html.Link(href="https://fonts.googleapis.com/css?family=Dosis", rel="stylesheet"),
        #html.Link(href="https://fonts.googleapis.com/css?family=Open+Sans", rel="stylesheet"),
        #html.Link(href="https://fonts.googleapis.com/css?family=Ubuntu", rel="stylesheet"),

    ],
    className="row",
    style={"margin": "0%"},
)


@app.callback(Output("tab_content", "children"), [Input("tabs", "value")])
def render_content(tab):
    if tab == "users_tab":
        layout =  users.layout
    elif tab == "engagement_tab":
        layout =  users.layout
    elif tab == "skill_tab":
        layout =  users.layout
    else:
        layout =  users.layout

    return layout

if __name__ == "__main__":
    app.run_server(debug=True,host='0.0.0.0')
