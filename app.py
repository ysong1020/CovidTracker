import dash
from dash import dcc
from dash import html
import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash.dependencies import Input, Output
from utils import get_state_codes, get_state_name, daily_increase, moving_average
from utils import all_states, state_code_dict, state_map_dict, fip_to_county, fip_to_state
from functools import reduce
from datetime import datetime
from urllib.request import urlopen
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from database import fetch_all_data_as_df

# Definitions of constants. This projects uses extra CSS stylesheet at `./assets/style.css`
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css', '/assets/style.css']
colors = {
"cases": 'rgb(49,130,189)',
"deaths": 'rgb(16, 112, 2)'
}

# Define the dash app first
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
df_dict = fetch_all_data_as_df()

# Define component functions


def page_header():
    """
    Returns the page header as a dash `html.Div`
    """
    return html.Div(id='header', children=[
        html.Div([html.H3('DATA1050 Final Project')],
                 className="ten columns"),
        html.A([html.Img(id='logo', src=app.get_asset_url('github.png'),
                         style={'height': '35px', 'paddingTop': '7%'}),
                html.Span('Doudou Yu & Yifei Song', style={'fontSize': '2rem', 'height': '35px', 'bottom': 0,
                                                'paddingLeft': '6px', 'color': '#a3a7b0',
                                                'textDecoration': 'none'})],
               className="two columns row",
               href='https://github.com/ddfishbean/CovidTracker'),
    ], className="row")


def project_description():
    """
    Returns overall project description in markdown
    """
    return html.Div(children=[dcc.Markdown('''
        # US Covid Tracker
        An web app to visualize the covid cases and deaths in the US
        
        ## Data Source
        Covid tracker utilizes historical and live covid-19 data from
        [New York Times github repository](https://github.com/nytimes/covid-19-data).
        **is regularly updated every day**.
        ''', className='eleven columns', style={'paddingLeft': '5%'})], className="row")

def visualization_description():
    """
    Returns the text and plots of EDA and interactive visualization of this project.
    """
    return html.Div(children=[
      dcc.Markdown('''
            ## EDA & Interactive Visualization
            This project uses `Dash` and `Plotly` for visualization. 
            Curve plots are used to show the time variation of cumulative and daily reported
            cases and deaths for the  national-level and state-level covid-19 data. Heat maps of
            geography data integrated are used o track the outbreak geographically. Pie chart helps
            visualize the cases in a state-wise manner
        ''', className='row eleven columns', style={'paddingLeft': '5%'}),
    ]
    )

def enhancement_description():
    """
    Returns the text and plots of Enhancements of this project.
    """
    return html.Div(children=[
      dcc.Markdown('''
      ## Enhancement
      Correlation analysis
        ''', className='row eleven columns', style={'paddingLeft': '5%'}),
    ]
    )

# Defines the dependencies of interactive components
@app.callback(Output('cd', 'figure'),
             Input('target-label', 'value'))
def cd(label):
    df = df_dict['us']
    x = df['date']
    stack=False
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=df[label], mode='lines', name=label,
                                line={'width': 3, 'color': colors[label]},
                                stackgroup='stack' if stack else None))
    # fig.add_trace(go.Scatter(x=x, y=df['Load'], mode='lines', name='Load',
    #                          line={'width': 2, 'color': 'orange'}))
    title = 'Accumulated cases and deaths in the US'
    if stack:
        title += ' [Stacked]'

    fig.update_layout(template='plotly_dark',
                      title=title,
                      plot_bgcolor='#23272c',
                      paper_bgcolor='#23272c',
                      yaxis_title='MW',
                      xaxis_title='Date/Time')
    return fig

@app.callback(Output('cd_stack', 'figure'),
             Input('daily-label', 'value'))
def cd_stack(label, window_size=7):
    df = df_dict['us']
    x = df['date']
    stack=True
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x, y=df[label], mode='lines', name=label,
                                line={'width': 2, 'color': colors[label]},
                                stackgroup='stack' if stack else None))
    # fig.add_trace(go.Scatter(x=x, y=df['Load'], mode='lines', name='Load',
    #                          line={'width': 2, 'color': 'orange'}))
    title = 'Accumulated cases and deaths in the US'
    if stack:
        title += ' [Stacked]'

    fig.update_layout(template='plotly_dark',
                      title=title,
                      plot_bgcolor='#23272c',
                      paper_bgcolor='#23272c',
                      yaxis_title='MW',
                      xaxis_title='Date/Time')
    return fig



@app.callback(Output('heat-map-by-state', 'figure'),
              Input('label-radioitems', 'value'))
def heat_map(label):
    """Create the heap map of given label in US at the beginning of given month"""
    df = df_dict['states']
    df['month'] = df.date.dt.month_name()
    df['state_code'] = df['state'].apply(lambda x: get_state_codes(x))
    df_month = df[((df.date.dt.day == 1) | (df.date == max(df.date)))]
    fig = px.choropleth(df_month,
                    locations='state_code',
                    locationmode="USA-states",
                    scope="usa",
                    color=label, # a column in the dataset
                    hover_name='state', # column to add to hover information
                    hover_data = {'cases': ':.0f', 'deaths': ':.0f', 'state_code': False, 'month': False},
                    color_continuous_scale=px.colors.sequential.Sunsetdark if \
                        label == 'cases' else px.colors.sequential.Greys,
                    animation_group='state',
                    animation_frame='month'
                   )
    fig.update_layout(title_text=f"Heat Map - Total {label.title()} in US States"),
    fig.update_layout(margin={"r":0,"l":0,"b":0})
    fig.update_layout(transition_duration=500)

    last_frame_num = len(fig.frames) -1

    fig.layout['sliders'][0]['active'] = last_frame_num

    fig = go.Figure(data=fig['frames'][-1]['data'], frames=fig['frames'], layout=fig.layout)
    fig.update_coloraxes(colorbar_title=f"<b>Color</b><br>Confirmed {label.title()}")
    fig.layout.pop('updatemenus')
    return fig


def architecture_summary():
    """
    Returns the text and image of architecture summary of the project.
    """
    return html.Div(children=[
        dcc.Markdown('''
            ## Project Architecture
            This project uses MongoDB as the database. All data acquired are stored in raw form to the
            database (with de-duplication). An abstract layer is built in `database.py` so all queries
            can be done via function call. For a more complicated app, the layer will also be
            responsible for schema consistency. A `plot.ly` & `dash` app is serving this web page
            through. Actions on responsive components on the page is redirected to `app.py` which will
            then update certain components on the page.
        ''', className='row eleven columns', style={'paddingLeft': '5%'}),

        html.Div(children=[
            html.Img(src="https://docs.google.com/drawings/d/e/2PACX-1vQNerIIsLZU2zMdRhIl3ZZkDMIt7jhE_fjZ6ZxhnJ9bKe1emPcjI92lT5L7aZRYVhJgPZ7EURN0AqRh/pub?w=670&amp;h=457",
                     className='row'),
        ], className='row', style={'textAlign': 'center'}),

        dcc.Markdown('''
        ''')
    ], className='row')


def visualization_summary():
    """
    All EDA figures should be arranged in this function.
    """
    return html.Div(children=[
        dcc.Markdown('''
        ### US Case and Death Count
        ''', className='row eleven columns', style={'paddingLeft': '5%'}),

            # Time series curves for cumulative cases and deaths in US
            dcc.Markdown('''
            #### Accumulated cases and deaths in the US
            ''', className='row eleven columns', style={'paddingLeft': '5%'}),

            html.Div([
                html.Div([
                    html.Label( ['Label:'],
                        style={'font-weight': 'bold', 'float': 'left',
                               'color': 'white', 'display': 'inline-block',
                               },
                        ),
                    dcc.RadioItems(
                        id='target-label',
                        options=[{'label': i.title(), 'value': i} for i in ['cases', 'deaths']],
                        value='cases',
                        labelStyle={
                        'display': 'inline-block',
                        },
                        style={
                        'width': '20%',
                        'float': 'left',
                        'font-weight': 'bold',
                        'color': 'white',
                        }),],  style={'width': '98%', 'display': 'inline-block'}),
                dcc.Graph(id='cd', style={'height': 500, 'width': 1100})
                ],
                style={'width': '98%', 'float': 'right', 'display': 'inline-block'}),

            # Time series curves for daily cases and deaths in US
                    dcc.Markdown('''
            #### Accumulated cases and deaths in the US (Stacked)
            ''', className='row eleven columns', style={'paddingLeft': '5%'}),
            html.Div([
                html.Div([
                    html.Label( ['Label:'],
                        style={'font-weight': 'bold', 'float': 'left',
                               'color': 'white', 'display': 'inline-block',
                               },
                        ),
                    dcc.RadioItems(
                        id='daily-label',
                        options=[{'label': i.title(), 'value': i} for i in ['cases', 'deaths']],
                        value='cases',
                        labelStyle={
                        'display': 'inline-block',
                        },
                        style={
                        'width': '20%',
                        'float': 'left',
                        'font-weight': 'bold',
                        'color': 'white',
                        }),],  style={'width': '98%', 'display': 'inline-block'}),
                dcc.Graph(id='cd_stack', style={'height': 500, 'width': 1100})
            ],
                style={'width': '98%', 'float': 'right', 'display': 'inline-block'}),


            # Heat map by month
            dcc.Markdown('''
            #### Heat Map - Covid in US states
            We use the state-level COVID-19 data to power the heat map and track the outbreak
            over all states of US.
            ''', className='row eleven columns', style={'paddingLeft': '0%'}),

            html.Div([
                html.Div([
                    html.Label( ['Label:'],
                        style={'font-weight': 'bold', 'float': 'left',
                               'color': 'white', 'display': 'inline-block',
                               },
                        ),
                    dcc.RadioItems(
                        id='label-radioitems',
                        options=[{'label': i.title(), 'value': i} for i in ['cases', 'deaths']],
                        value='cases',
                        labelStyle={
                        'display': 'inline-block',
                        },
                        style={
                        'width': '20%',
                        'float': 'left',
                        'font-weight': 'bold',
                        'color': 'white',
                        }),],  style={'width': '98%', 'display': 'inline-block'}),
                dcc.Graph(id='heat-map-by-state', style={'height': 800, 'width': 1000})
            ],
                style={'width': '100%', 'float':'right', 'display': 'inline-block'}),

    ])

app.layout = html.Div([
        page_header(),
        html.Hr(),
        project_description(),
        visualization_description(),
        visualization_summary(),
        enhancement_description(),
        architecture_summary(),
    ], className='row', id='content')

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0')