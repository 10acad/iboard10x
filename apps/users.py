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

from app import app

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
            em = set(df_log_top.index.to_list())
            eg = set(df_user.index.to_list())
            e = list(em & eg)  #intersection
            df_user_top = df_user.loc[e]
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

    trace1 = gox.Scatter(
        x = df_log.index,
        y=df_log[col],
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
            title='User ID'
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




# returns modal (hidden by default)
def modal():
    return html.Div(
        html.Div(
            [
                html.Div(
                    [

                        # modal header
                        html.Div(
                            [
                                html.Span(
                                    "New Opportunity",
                                    style={
                                        "color": "#506784",
                                        "fontWeight": "bold",
                                        "fontSize": "20",
                                    },
                                ),
                                html.Span(
                                    "×",
                                    id="opportunities_modal_close",
                                    n_clicks=0,
                                    style={
                                        "float": "right",
                                        "cursor": "pointer",
                                        "marginTop": "0",
                                        "marginBottom": "17",
                                    },
                                ),
                            ],
                            className="row",
                            style={"borderBottom": "1px solid #C8D4E3"},
                        ),


                        # modal form 
                        html.Div(
                            [

                                # left div
                                html.Div(
                                    [
                                        html.P(
                                            [
                                                "Name"
                                            ],
                                            style={
                                                "float": "left",
                                                "marginTop": "4",
                                                "marginBottom": "2",
                                            },
                                            className="row",
                                        ),
                                        dcc.Input(
                                            id="new_opportunity_name",
                                            placeholder="Name of the opportunity",
                                            type="text",
                                            value="",
                                            style={"width": "100%"},
                                        ),

                                        html.P(
                                            [
                                                "StageName"
                                            ],
                                            style={
                                                "textAlign": "left",
                                                "marginBottom": "2",
                                                "marginTop": "4",
                                            },
                                        ),
                                        dcc.Dropdown(
                                            id="new_opportunity_stage",
                                            options=[
                                                {
                                                    "label": "Prospecting",
                                                    "value": "Prospecting",
                                                },
                                                {
                                                    "label": "Qualification",
                                                    "value": "Qualification",
                                                },
                                                {
                                                    "label": "Needs Analysis",
                                                    "value": "Needs Analysis",
                                                },
                                                {
                                                    "label": "Value Proposition",
                                                    "value": "Value Proposition",
                                                },
                                                {
                                                    "label": "Id. Decision Makers",
                                                    "value": "Closed",
                                                },
                                                {
                                                    "label": "Perception Analysis",
                                                    "value": "Perception Analysis",
                                                },
                                                {
                                                    "label": "Proposal/Price Quote",
                                                    "value": "Proposal/Price Quote",
                                                },
                                                {
                                                    "label": "Negotiation/Review",
                                                    "value": "Negotiation/Review",
                                                },
                                                {
                                                    "label": "Closed/Won",
                                                    "value": "Closed Won",
                                                },
                                                {
                                                    "label": "Closed/Lost",
                                                    "value": "Closed Lost",
                                                },
                                            ],
                                            clearable=False,
                                            value="Prospecting",
                                        ),

                                        html.P(
                                            "Source",
                                            style={
                                                "textAlign": "left",
                                                "marginBottom": "2",
                                                "marginTop": "4",
                                            },
                                        ),
                                        dcc.Dropdown(
                                            id="new_opportunity_source",
                                            options=[
                                                {"label": "Web", "value": "Web"},
                                                {
                                                    "label": "Phone Inquiry",
                                                    "value": "Phone Inquiry",
                                                },
                                                {
                                                    "label": "Partner Referral",
                                                    "value": "Partner Referral",
                                                },
                                                {
                                                    "label": "Purchased List",
                                                    "value": "Purchased List",
                                                },
                                                {"label": "Other", "value": "Other"},
                                            ],
                                            value="Web",
                                        ),

                                        html.P(
                                            [
                                                "Close Date"
                                            ],
                                            style={
                                                "textAlign": "left",
                                                "marginBottom": "2",
                                                "marginTop": "4",
                                            },
                                        ),
                                        html.Div(
                                            dcc.DatePickerSingle(
                                                id="new_opportunity_date",
                                                min_date_allowed=date.today(),
                                                # max_date_allowed=dt(2017, 9, 19),
                                                initial_visible_month=date.today(),
                                                date=date.today(),
                                            ),
                                            style={"textAlign": "left"},
                                        ),

                                    ],
                                    className="six columns",
                                    style={"paddingRight": "15"},
                                ),

                                
                                # right div
                                html.Div(
                                    [
                                        html.P(
                                            "Type",
                                            style={
                                                "textAlign": "left",
                                                "marginBottom": "2",
                                                "marginTop": "4",
                                            },
                                        ),
                                        dcc.Dropdown(
                                            id="new_opportunity_type",
                                            options=[
                                                {
                                                    "label": "Existing Customer - Replacement",
                                                    "value": "Existing Customer - Replacement",
                                                },
                                                {
                                                    "label": "New Customer",
                                                    "value": "New Customer",
                                                },
                                                {
                                                    "label": "Existing Customer - Upgrade",
                                                    "value": "Existing Customer - Upgrade",
                                                },
                                                {
                                                    "label": "Existing Customer - Downgrade",
                                                    "value": "Existing Customer - Downgrade",
                                                },
                                            ],
                                            value="New Customer",
                                        ),

                                        html.P(
                                            "Amount",
                                            style={
                                                "textAlign": "left",
                                                "marginBottom": "2",
                                                "marginTop": "4",
                                            },
                                        ),
                                        dcc.Input(
                                            id="new_opportunity_amount",
                                            placeholder="0",
                                            type="number",
                                            value="",
                                            style={"width": "100%"},
                                        ),

                                        html.P(
                                            "Probability",
                                            style={
                                                "textAlign": "left",
                                                "marginBottom": "2",
                                                "marginTop": "4",
                                            },
                                        ),
                                        dcc.Input(
                                            id="new_opportunity_probability",
                                            placeholder="0",
                                            type="number",
                                            max=100,
                                            step=1,
                                            value="",
                                            style={"width": "100%"},
                                        ),

                                    ],
                                    className="six columns",
                                    style={"paddingLeft": "15"},
                                ),
                            ],
                            className="row",
                            style={"paddingTop": "2%"},
                        ),


                        # submit button
                        html.Span(
                            "Submit",
                            id="submit_new_opportunity",
                            n_clicks=0,
                            className="button button--primary add"
                        ),
                    ],
                    className="modal-content",
                    style={"textAlign": "center"},
                )
            ],
            className="modal",
        ),
        id="opportunities_modal",
        style={"display": "none"},
    )


layout = [

    # top controls
    html.Div(
        [
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
                        {"label": "Top 25%", "value": "top25"},
                        {"label": "Top 50%", "value": "top50"},
                        {"label": "All Users", "value": "all"},                        
                    ],
                    value="all_s",
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


#     # tables row div
#     html.Div(
#         [
#             html.Div(
#                 [
#                     html.P(
#                         "Activities Count",
#                         style={
#                             "color": "#2a3f5f",
#                             "fontSize": "13px",
#                             "textAlign": "center",
#                             "marginBottom": "0",
#                         },
#                     ),
#                     html.Div(
#                         id="top_active_users",
#                         style={"padding": "0px 13px 5px 13px", "marginBottom": "5"},
#                     ),
#
#                 ],
#                 className="six columns",
#                 style={
#                     "backgroundColor": "white",
#                     "border": "1px solid #C8D4E3",
#                     "borderRadius": "3px",
#                     "height": "100%",
#                     "overflowY": "scroll",
#                 },
#             ),
#             html.Div(
#                 [
#                     html.P(
#                         "Dedication Time",
#                         style={
#                             "color": "#2a3f5f",
#                             "fontSize": "13px",
#                             "textAlign": "center",
#                             "marginBottom": "0",
#                         },
#                     ),
#                     html.Div(
#                         id="top_dedicated_users",
#                         style={"padding": "0px 13px 5px 13px", "marginBottom": "5"},
#                     )
#                 ],
#                 className="six columns",
#                 style={
#                     "backgroundColor": "white",
#                     "border": "1px solid #C8D4E3",
#                     "borderRadius": "3px",
#                     "height": "100%",
#                     "overflowY": "scroll",
#                 },
#             ),
#
#
#             modal(),
#         ],
#          className="row",
#          style={"marginTop": "5px", "max height": "200px"},
#      ),


 ]


# updates heatmap figure based on dropdowns values or df updates
@app.callback(
    Output("activities_count", "figure"),
    [Input("topusers_dropdown", "value"), Input("topestimator_dropdown", "value"),
     Input("users_df", "children"), Input("engagement_df", "children")],
)
def topusers_callback(topid, toptype, df_user,df_log):

    dfu = pd.read_json(df_user, orient="split")
    dfl = pd.read_json(df_log, orient="split")

    col = top_name_mapper(toptype)
    dfl_top, dfu_top = get_top_user_df(topid, toptype, dfl, df_user=dfu)

    #print('topid=%s, toptype=%s, lendf=%s'%(topid,toptype, len(dfl_top) ))
    #print('dfl_top, head:',dfl_top.head())

    return histogram_topx_users(dfl_top, col)


# updates converted opportunity count graph based on dropdowns values or df updates
@app.callback(
    Output("gender_distribution", "figure"),
    [
        Input("topusers_dropdown", "value"), Input("users_df", "children"),
    ],
)
def gender_distribution_callback(topid, df_user):
    df = pd.read_json(df_user, orient="split")
    cdf = user_group_by_gender(df)
    #print('gender cdf',cdf.head())

    return histgram_countries(cdf)



@app.callback(
    Output("left_users_indicator", "children"),
    [Input("topusers_dropdown", "value"), Input("topestimator_dropdown", "value"),
     Input("engagement_df", "children")],
)
def left_users_indicator_callback(topid, toptype, df):
    df = pd.read_json(df, orient="split")
    df_top= get_top_user_df(topid, toptype, df)

    #
    nuser = millify(str( len(df_top) ))
    return nuser


# updates middle indicator value based on df updates
@app.callback(
    Output("middle_users_indicator", "children"),
    [Input("topusers_dropdown", "value"), Input("topestimator_dropdown", "value"),
     Input("engagement_df", "children")],
)
def middle_users_indicator_callback(topid, toptype, df):
    df = pd.read_json(df, orient="split")
    df_top= get_top_user_df(topid, toptype, df)

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
    [Input("topusers_dropdown", "value"), Input("topestimator_dropdown", "value"),
     Input("engagement_df", "children")],
)
def right_users_indicator_callback(topid, toptype, df):
    df = pd.read_json(df, orient="split")
    df_top= get_top_user_df(topid, toptype, df)

    #
    col = top_name_mapper('timespent')
    #print('right col', col, df_top[col].sum())
    timespent = millify(
        str( df_top[col].map(lambda x:float(x)/3600.0).sum() )
    )


    return '%s hrs'%timespent


# # hide/show modal
# @app.callback(
#     Output("opportunities_modal", "style"), [Input("new_opportunity", "n_clicks")]
# )
# def display_opportunities_modal_callback(n):
#     if n > 0:
#         return {"display": "block"}
#     return {"display": "none"}
#
#
# # reset to 0 add button n_clicks property
# @app.callback(
#     Output("new_opportunity", "n_clicks"),
#     [
#         Input("opportunities_modal_close", "n_clicks"),
#         Input("submit_new_opportunity", "n_clicks"),
#     ],
# )
# def close_modal_callback(n, n2):
#     return 0
#
#
# # add new opportunity to salesforce and stores new df in hidden div
# @app.callback(
#     Output("opportunities_df", "children"),
#     [Input("submit_new_opportunity", "n_clicks")],
#     [
#         State("new_opportunity_name", "value"),
#         State("new_opportunity_stage", "value"),
#         State("new_opportunity_amount", "value"),
#         State("new_opportunity_probability", "value"),
#         State("new_opportunity_date", "date"),
#         State("new_opportunity_type", "value"),
#         State("new_opportunity_source", "value"),
#         State("opportunities_df", "children"),
#     ],
# )
# def add_opportunity_callback(
#     n_clicks, name, stage, amount, probability, date, o_type, source, current_df
# ):
#     if n_clicks > 0:
#         if name == "":
#             name = "Not named yet"
#         query = {
#             "Name": name,
#             "StageName": stage,
#             "Amount": amount,
#             "Probability": probability,
#             "CloseDate": date,
#             "Type": o_type,
#             "LeadSource": source,
#         }
#
#         sf_manager.add_opportunity(query)
#
#         df = sf_manager.get_opportunities()
#
#         return df.to_json(orient="split")
#
#     return current_df
#
#
# # updates top open opportunities based on df updates
# @app.callback(
#     Output("top_open_opportunities", "children"),
#     [Input("opportunities_df", "children")],
# )
# def top_open_opportunities_callback(df):
#     df = pd.read_json(df, orient="split")
#     return top_open_opportunities(df)
#
#
#
# # updates top lost opportunities based on df updates
# @app.callback(
#     Output("top_lost_opportunities", "children"),
#     [Input("opportunities_df", "children")],
# )
# def top_lost_opportunities_callback(df):
#     df = pd.read_json(df, orient="split")
#     return top_lost_opportunities(df)
