# -*- coding: utf-8 -*-
import math
import json
from datetime import date
import dateutil.parser
import iso3166

import pandas as pd
import flask
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import plotly.plotly as py
from plotly import graph_objs as gox

import logging
import logging.handlers

from app import app
from utils.logger import get_logger

logger = get_logger('users')

millnames = ["", " K", " M", " B", " T"] # used to convert numbers

colors = {
    'background': '#111111',
    'text': "#00000"
}

dropdown_styles = {
    'height': '44px',
    'borderBottom': '1px solid #d6d6d6',
    'padding': '6px',
    'fontWeight': 'bold'
}

fig_title_style = {
    "height": "1%",
    "width": "98%",
    "color": 'white',
    "background-color": "#ED1F33",
    'textAlign': 'left',
    "fontSise":15,
    'padding': '6px'
}

fig_text_style = {
    "height": "1%",
    "width": "98%",
    "color": 'white',
    #"background-color": "#ED1F33",
    'textAlign': 'left',
    "fontSise":12,
    #'padding': '6px'
}

fig_style = {
    "height": "2%",
    "width": "49%",
    "color": 'black',
    #"background-color": "#ED1F33",
    'textAlign': 'left',
    "fontSise":12,
    'padding': '15px'
}

indicators_style = {
    'borderTop': '1px solid #d6d6d6',
    'borderBottom': '1px solid #d6d6d6',
    'backgroundColor': 'white',
    'color': '#ED1F33',
    'padding': '6px',
    'fontWeight': 'bold',
    "fontSise":12,
}

#
#{"paddingRight": "15", "marginBottom": "20"},

#{
# return html Table with dataframe values
def df_to_table(df):
    return html.Table(
        # Header
        [html.Tr([html.Th(col) for col in df.columns])] +

        # Body
        [
            html.Tr(
                [
                    html.Td(df.iloc[i][col])
                    for col in df.columns
                ]
            )
            for i in range(len(df))
        ]
    )


#returns most significant part of a number
def millify(n):
    n = float(n)
    millidx = max(
        0,
        min(
            len(millnames) - 1, int(math.floor(0 if n == 0 else math.log10(abs(n)) / 3))
        ),
    )

    return "{:.0f}{}".format(n / 10 ** (3 * millidx), millnames[millidx])


#returns top indicator div
def indicator(color, text, id_value):
    return html.Div(
        [

            html.P(
                text,
                style=indicators_style,
                className="twelve columns indicator_text"
            ),
            html.P(
                id = id_value,
                className="indicator_value"
            ),
        ],
        className="four columns indicator",

    )


def top_name_mapper(toptype):
    return {'logincount':'LoginCount',
           'timespent': 'TotalSecondsSpent',
           'activitycount': 'ActivitiesCount'}[toptype]

def get_df_matching_index(df, index_list):
    em = set(pd.Index(index_list).tolist())
    eg = set(df.index.tolist())
    e = list(em & eg)  #intersection
    return df.loc[e]

def get_top_user_index(topid, toptype, df_log):
    
    col = top_name_mapper(toptype)
    if 'top' in topid.lower():
        q = {'top%s'%x : float(x)/100.0 for x in range(101)}[topid]
        qdf = df_log[col].sort_values(ascending=False).to_frame()
        qdf = qdf.quantile(1.0-q)
        qval = qdf.values[0] #df_log[col].values[int((1.0-q)*len(df_log))] #
        mask = df_log[col] >= qval
        df = df_log[mask]
    else:
        df = df_log
        
    return df.index.tolist()
    
def get_top_user_df(topid, toptype, df_log, df_user=None):
    
    col = top_name_mapper(toptype)

    if 'top' in topid.lower():
        q = {'top%s'%x : float(x)/100.0 for x in range(101)}[topid]
        qdf = df_log[col].sort_values(ascending=False).to_frame()
        qdf=qdf.quantile(1.0-q)
        mask = df_log[col] >= qdf.values[0]
        df_log_top = df_log[mask]

        if df_user is None:
            return df_log_top
        else:
            #get_top_user_index(topid, toptype, df_log)                
            em = df_log_top.index.tolist()
            df_user_top = get_df_matching_index(df_user,em)
            return df_log_top, df_user_top
    else:
        #retur
        if df_user is None:
            return df_log
        else:
            return df_log, df_user


def user_group_by_gender(df,cmapper=None):
    if cmapper is None:
        cmapper = {'Ivory Coast': "CÔTE D'IVOIRE",
                   'Other':'Nigeria',
                   'Tanzania':'Tanzania, UNITED REPUBLIC OF'}

    gdict = {x:[] for x in ['country','Male','Female']}

    groups = df.groupby('country')
    for c, g in groups:
        if c=='Other':
            continue
            
        gc = g.groupby('gender').count()['email']
        #
        for k in gdict.keys():
            #append country
            if k=='country':
                gdict['country'].append(c)
            else:
                #append gender count
                if k in gc.keys():
                    gdict[k].append(gc.loc[k])
                else:
                    gdict[k].append(0)


    #print(gdict)
    cdf = pd.DataFrame.from_dict(gdict)
    cdf['total'] = cdf['Male'] + cdf['Female']

    fmap = lambda x: cmapper.get(x,x)
    f = lambda x : iso3166.countries_by_name.get(x.upper()).alpha2

    cdf['CountryCode'] = cdf['country'].map(fmap).map(f)
    cdf = cdf.set_index('CountryCode').sort_values('total',ascending=False)

    return cdf

def histgram_countries(cdf):


    trace1 = gox.Bar(
        x=cdf.index,
        y = cdf['Male'],
        name='Male',
        marker=dict(
            color='#FFD7E9',
        ),
        text = ['%s, %s'%(row['country'],row['Male']) for index, row in cdf.iterrows()],  #cdf['country'], #
        hoverinfo = 'text',
        opacity=0.75
    )

    trace2 = gox.Bar(
        x=cdf.index,
        y=cdf['Female'],
        name='Female',
        marker=dict(
           color='#EB89B5'
        ),
        text = ['%s, %s'%(row['country'],row['Female']) for index, row in cdf.iterrows()], #cdf['country'], #
        hoverinfo = 'text',
        opacity=0.75
    )

    data = [trace1,trace2]

    layout = gox.Layout(
        #title='Gender Distribution by Country',
        xaxis=dict(
            title='Countries'
        ),
        yaxis=dict(
            title='Count'
        ),
        bargap=0.2,
        bargroupgap=0.1
    )

    return {"data": data, "layout": layout}


def histogram_topx_users(df_log,col):

    y = df_log[col]
    if col=='TotalSecondsSpent':
        y = y.map(lambda x:float(x)/3600.0)
        col = 'Dedication Time (Hrs)'
        
    trace1 = gox.Bar(
        x = df_log.index,
        y=y,
        #histnorm='percent',
        #name='control',
        #xbins=dict(
        #    start=-4.0,
        #    end=3.0,
        #    size=0.5
        #),
        marker=dict(
            color='#FFD7E9',
        ),
        opacity=0.75
    )

    # trace2 = gox.Histogram(
    # x=x1,
    # name='experimental',
    # xbins=dict(
    #     start=-3.0,
    #     end=4,
    #     size=0.5
    # ),
    # marker=dict(
    #     color='#EB89B5'
    # ),
    # opacity=0.75
    # )

    data = [trace1]

    layout = gox.Layout(
        #title='Users Profile',
        xaxis=dict(
            title='Users Index'
        ),
        yaxis=dict(
            title=col
        ),
    )


    # layout = go.Layout(
    #     xaxis=dict(showgrid=False),
    #     margin=dict(l=35, r=25, b=23, t=5, pad=4),
    #     paper_bgcolor="white",
    #     plot_bgcolor="white",
    # )

    return {"data": data, "layout": layout}


#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------

layout = [

    # top controls
    html.Div(
        [
            # Hidden div inside the app that stores the intermediate value
            html.Div(id='intermediate-value', style={'display': 'none'}),
            
            html.Div(
                dcc.Dropdown(
                    id="source_dropdown",
                    options=[
                        {"label": "Moodle Users", "value": "MU"},
                        #{"label": "Applicants", "value": "AP"},
                    ],
                    value="MU",
                    clearable=False,
                ),
                className="two columns",
            ),

            html.Div(
                dcc.Dropdown(
                    id="topusers_dropdown",
                    options=[
                        {"label": "Top 1%", "value": "top1"},
                        {"label": "Top 5%", "value": "top5"},
                        {"label": "Top 10%", "value": "top10"},                        
                        {"label": "Top 25%", "value": "top25"},
                        {"label": "Top 50%", "value": "top50"},
                        {"label": "All Users", "value": "all"},                        
                    ],
                    value="all",
                    clearable=False,
                ),
                className="two columns",
            ),

            html.Div(
                dcc.Dropdown(
                    id="topestimator_dropdown",
                    options=[
                        {"label": "Activity Count", "value": "activitycount"},
                        {"label": "Login Count", "value": "logincount"},
                        {"label": "Dedication Time", "value": "timespent"},
                    ],
                    value="timespent",
                    clearable=False,
                ),
                className="two columns",

            ),

            #add button
            # html.Div(
            #     html.Span(
            #         "Add new",
            #         id="new_opportunity",
            #         n_clicks=0,
            #         className="button button--primary add"
            #     ),
            #     className="two columns",
            #     style={"float": "right"},
            # ),
        ],
        className="row",
        style=dropdown_styles,
    ),

    #indicators row
    html.Div(
        [
            indicator(
                "#ED1F33", #00cc96",
                "Number of Users",
                "left_users_indicator",
            ),
            indicator(
                "#119DFF",
                "Number of Activities",
                "middle_users_indicator",
            ),
            indicator(
                "#EF553B",
                "Total Engagement Hours",
                "right_users_indicator",
            ),
        ],
        className="row",
        style={"marginBottom": "10"},
    ),

    #"font-size": "120%",
    #             "width": "100%"
    #charts row div 
    html.Div(
        [
            html.Div(
                [
                    html.H1(children='Engagement Counts',
                            style=fig_title_style), #,'color': colors['text']

                    dcc.Graph(
                        id="activities_count",
                        style={"height": "90%", "width": "98%"},
                        config=dict(displayModeBar=False),
                    ),
                ],

                html.Div(children='''
                    Depending on the dropdowns, this figure shows wsers number of logins, 
                    number of activities or time spent doing active learning.
                    ''',style=fig_text_style,
                        ),

                className="six columns chart_div",
                style=fig_style
                ),

            html.Div(
                [
                    html.H1(children='Gender Distribution',
                            style=fig_title_style),


                    dcc.Graph(
                        id="gender_distribution",
                        style={"height": "90%", "width": "98%"},
                        config=dict(displayModeBar=False),
                    ),

                ],

                html.Div(children='''
                    Gender distribution of enrolled users per country country.
                    ''',style=fig_text_style,
                         ),

                className="six columns chart_div",
                style=fig_style
            ),
        ],
        className="row",
        style={"marginTop": "20px"}
    ),
 ]


@app.callback(
    Output('intermediate-value', 'children'),
    [
        Input("topusers_dropdown", "value"),
        Input("topestimator_dropdown", "value"),
        Input("engagement_df", "children")
    ],  
)
# some expensive clean data step
def clean_data(topid, toptype, df_log):
    
    #read input
    df_log = pd.read_json(df_log, orient="split")
    
    #process
    index_toplist = [int(x) for x in get_top_user_index(topid, toptype, df_log)]

    
    # more generally, this line would be
    #return top.to_json(date_format='iso', orient='split')    
    return json.dumps(index_toplist)


 
# updates user figure based on dropdowns values or df updates
@app.callback(
    Output("activities_count", "figure"),
    [
        Input("topusers_dropdown", "value"),
        Input("topestimator_dropdown", "value"),        
        Input('intermediate-value', 'children'),
        Input("engagement_df", "children")
    ],
)
def topusers_callback(topid, toptype, topindex, df_log):


    #read input
    index_list = json.loads(topindex) #pd.read_json(topindex).to_list()     
    df_log = pd.read_json(df_log, orient="split")

    #process
    df_top = get_df_matching_index(df_log,index_list)        
    col = top_name_mapper(toptype)

    #logger.debug('figure topusers: col=%s, len(df_log), len(df_log_top)=%s'%(col, len(df_log), len(df_top)))  
    
    return histogram_topx_users(df_top, col)


# updates converted opportunity count graph based on dropdowns values or df updates
@app.callback(
    Output("gender_distribution", "figure"),
    [
        Input("topusers_dropdown", "value"),
        Input("topestimator_dropdown", "value"),         
        Input('intermediate-value', 'children'),
        Input("users_df", "children"),
    ],
)
def gender_distribution_callback(topid, toptype, topindex, df_user):

    #read input
    index_list = json.loads(topindex) #pd.read_json(topindex).to_list() 
    df_user = pd.read_json(df_user, orient="split")

    #process
    df_top = get_df_matching_index(df_user,index_list)      
    cdf = user_group_by_gender(df_top)

    col = top_name_mapper(toptype)    
    #logger.debug('figure genderdist: col=%s, len(df_log), len(df_log_top)=%s'%(col, len(df_user), len(df_top)))
    
    return histgram_countries(cdf)



@app.callback(
    Output("left_users_indicator", "children"),
    [
        Input("topusers_dropdown", "value"),
        Input("topestimator_dropdown", "value"),                
        Input('intermediate-value', 'children'),
        Input("engagement_df", "children")
    ],
)
def left_users_indicator_callback(topid, toptype, topindex, df_log):

    #read input
    index_list = json.loads(topindex) #pd.read_json(topindex).to_list() 
    df = pd.read_json(df_log, orient="split")

    #process
    df_top = get_df_matching_index(df,index_list)
    
    #df = pd.read_json(df, orient="split")
    #df_top= get_top_user_df(topid, toptype, df)

    #
    nuser = millify(str( len(df_top) ))
    return nuser


# updates middle indicator value based on df updates
@app.callback(
    Output("middle_users_indicator", "children"),
    [
        Input("topusers_dropdown", "value"),
        Input("topestimator_dropdown", "value"),        
        Input('intermediate-value', 'children'),
        Input("engagement_df", "children")
    ],
)
def middle_users_indicator_callback(topid, toptype, topindex, df_log):

    #read input
    index_list = json.loads(topindex) #pd.read_json(topindex).to_list() 
    df = pd.read_json(df_log, orient="split")

    #process
    df_top = get_df_matching_index(df,index_list)
    
    #
    col = top_name_mapper('activitycount')
    #print('middle col', col, df_top[col].sum())
    active = millify(
        str( df_top[col].sum() )
    )

    return active


# updates right indicator value based on df updates
@app.callback(
    Output("right_users_indicator", "children"),
    [
        Input("topusers_dropdown", "value"),
        Input("topestimator_dropdown", "value"),         
        Input('intermediate-value', 'children'),
        Input("engagement_df", "children")
    ],
)
def right_users_indicator_callback(topid, toptype, topindex, df_log):
    #read input
    index_list = json.loads(topindex) #pd.read_json(topindex).to_list() 
    df = pd.read_json(df_log, orient="split")

    #process
    df_top = get_df_matching_index(df,index_list)
    
    #
    col = top_name_mapper('timespent')
    timespent = millify(
        str( df_top[col].map(lambda x:float(x)/3600.0).sum() )
    )

    return '%s hrs'%timespent

