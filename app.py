import dash
from dash import dcc
from dash import html
import numpy as np
import plotly.graph_objects as go
from dash.dependencies import Input, Output
from utils import get_state_codes, get_state_name, daily_increase, moving_average
from utils import all_states, state_code_dict, state_map_dict, fip_to_county, fip_to_state
from database import fetch_all_data_as_df

# Definitions of constants. This projects uses extra CSS stylesheet at `./assets/style.css`
COLORS = ['rgb(67,67,67)', 'rgb(115,115,115)', 'rgb(49,130,189)', 'rgb(189,189,189)']
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css', '/assets/style.css']

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
                html.Span('Old boys', style={'fontSize': '2rem', 'height': '35px', 'bottom': 0,
                                                'paddingLeft': '4px', 'color': '#a3a7b0',
                                                'textDecoration': 'none'})],
               className="two columns row",
               href='https://github.com/ddfishbean/CovidTracker'),
    ], className="row")


def project_description():
    """
    Returns overall project description in markdown
    """
    return html.Div(children=[dcc.Markdown('''
        # US COVID-19 Tracker
        The coronavirus pandemic has caused more than one and half million deaths over the world.
        The COVID-19 has exhausted the United States, and it seems a dark and deadly winter is waiting ahead.
        Therefore, it is of crucial importance to understand and project the trend of COVID-19 cases in US
        so that policy-makers can come up with short-term and long-term strategies to limit the spread and
        mitigate the effect of another outbreak in the near future.
        **US COVID-19 tracker is also a tool to assist making strategies.**
        It can be used to understand what factors might affect the spread of the pandemic in US
        and project the trend if more precautions and restrictions are imposed.
        ## Data Source
        Covid-19 tracker mainly utilizes historical and live covid-19 data from
        [New York Times github repository](https://github.com/nytimes/covid-19-data).
        The hirarchical case and death [data](https://raw.githubusercontent.com/nytimes/covid-19-data/master/us.csv)
        **is regularly updated every day**.
        Also, the data for state and county population is merged to obtain the positive rate over population at different
        geographical levels.
        Additionally, the [survey data](https://raw.githubusercontent.com/nytimes/covid-19-data/master/mask-use/mask-use-by-county.csv)
        by New York time on maks use by county is investigated to see if there exists a
        correlation between the outbreak and mask use frequency in each state. All data sets in this project are well-structured.
        ''', className='eleven columns', style={'paddingLeft': '5%'})], className="row")

def visualization_description():
    """
    Returns the text and plots of EDA and interactive visualization of this project.
    """
    return html.Div(children=[
      dcc.Markdown('''
            ## EDA & Interactive Visualization
            This project uses `Dash` and `Plotly` for visualization. We use the
            high-level components/tools in Dash to provide compact figures which allow user
            to choose what to display. For example, we utilized radio items to select targets
            (case or death number), dropdown layout to select the state, and slider to select
            time points.
            Curve plots are used to show the time variation of cumulative and daily reported
            cases and deaths for the  national-level and state-level covid-19 data. Heat maps are used
            to track the outbreak geographically.
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
      Public health experts suggest that face coverings can substantially slow the transmission
      of covid. In this section, we firstly use a heatmap to show the propensity of people to wear
      masks in each county. This heat map is based on the survey data from a large number of interviews
      conducted by the global data and survey firm Dynata at the request of The New York Times.
      Next, we attempt to understand what factors might affect the spread of the pandamic in US states.
      For this analysis, we select two responsive variables including case fatality rate and infection rate,
      and two predictors, namely average wear-mask probability and population density. A simple and intuitive
      linear correlation analysis is conducted. For Covid data, we use the latest state-level data for demonstration.
      In order to obtain the state-level mask-use data, the county-level data is aggregated over states and we take
      the average of features in each state to get the state-level features.
        ''', className='row eleven columns', style={'paddingLeft': '5%'}),
    ]
    )

# Defines the dependencies of interactive components
@app.callback(Output('time-series-total', 'figure'),
             Input('target-label', 'value'))
def time_series_cumulative(label):
    df = df_dict['us']
    x = df['date']
    trace = go.Scatter(x=x, y=df[label], mode='lines', name=label, fill='tozeroy',
                       fillcolor=colors[label],
                       line={'width': 2, 'color': colors[label]},
                       hovertemplate='%{x|%b %d, %Y} <br> %{y:-.0f}'
                      )

    title = f'Cumulative Covid {label.lower()} in U.S. over time'
    layout = dict(title=title,
                  yaxis_title=f'# of {label}',
                  xaxis_title='Date/Time',
                  font=dict(family="Courier New, monospace",
                            size=16))
    data = [trace]
    fig = dict(data=data, layout=layout)
    return fig

@app.callback(Output('time-series-daily', 'figure'),
             Input('daily-label', 'value'))
def time_series_daily(label, window_size=7):
    df = df_dict['us']
    x = df['date']
    daily = daily_increase(df[label])
    moving_avg = moving_average(daily, window_size)

    trace1 = go.Bar(x=x, y=daily, name=f'Daily new {label}',
                    marker = dict(color = colors_bar[label],
                                  line=dict(color=colors_bar[label],width=1.5),
                                  opacity=0.2),
                    hovertemplate='%{x|%b %d, %Y} <br>Daily: %{y:-.0f}'
                   )
    trace2 = go.Scatter(x=x, y=moving_avg,
                        name=f'Moving average in {window_size} days',
                        line={'width':3, 'color': colors_line[label]},
                        hovertemplate='Moving average: %{y:-.0f}'
                        )

    title = f'Daily reported new Covid {label.lower()} in U.S. over time'
    layout = dict(title=title,
                  yaxis_title=f'# of {label} per day',
                  xaxis_title='Date/Time',
                  font=dict(family="Courier New, monospace",
                            size=16),
                  hoverlabel=dict(
                            bgcolor="white",
                            font_size=16,
                            font_family="Rockwell"),
                  hovermode='x Unified',
                  legend=dict(
                        yanchor="top",
                        y=0.99,
                        xanchor="left",
                        x=0.01)
                 )
    data = [trace1, trace2]
    fig = dict(data=data, layout=layout)
    return fig

@app.callback(Output('time-series-state', 'figure'),
            Input('plot-type', 'value'),
            Input('state-name', 'value'),
            Input('label-by-state', 'value'),
             )
def time_series_state(plot_type='daily', state_name='Rhode Island', label='cases',):
#     print(label, plot_type, state_name)
    df = df_dict['states']
    df['state_code'] = df['state'].apply(lambda x: state_code_dict[x])
    state_code = state_code_dict[state_name]
    df_state = df[df.state_code == state_code]
    state = state_name
    df_state = df_state.sort_values(by='date')
    df_state = pd.DataFrame(df_state, columns=df_state.columns)
    x = df_state.date
    y = df_state[label].values
    if plot_type == 'daily':
        window_size = 7
        daily_cases = daily_increase(y)
        moving_avg = moving_average(daily_cases, window_size)
        trace_bar = go.Bar(x=x, y=daily_cases, name=f'Daily new {label}',
                    marker = dict(color = colors_bar[label],
                                  line=dict(color=colors_bar[label],width=1.5),
                                  opacity=0.2),
                    hovertemplate='Date: %{x|%A, %b %d, %Y} <br> Daily increase : %{y:.0f}'
                   )
        trace_line = go.Scatter(
            x=x,
            y=moving_avg,
            name=f'Moving average in {window_size} days',
            line={'width':1.5, 'color': colors_line[label]},
            hovertemplate='7 Day Avg. : %{y:.0f}')
        title = f'Daily reported new Covid {label.lower()} in {state}'
        layout = dict(title=title,
              yaxis_title=f'# of {label} per day',
              xaxis_title='Date/Time',
              font=dict(family="Courier New, monospace",
                        size=16),
              hoverlabel=dict(
                bgcolor="white",
                font_size=16,
                font_family="Rockwell"),
              hovermode='x Unified',
              legend=dict(
                        yanchor="top",
                        y=0.99,
                        xanchor="left",
                        x=0.01))
        fig = dict(data=[trace_bar, trace_line], layout=layout)
        return fig
    elif plot_type == 'cumulative':
        trace = go.Scatter(x=x, y=y, mode='lines', name=label, fill='tozeroy',
                       fillcolor=colors[label],
                       line={'width': 2, 'color': colors[label]},
                       hovertemplate='%{x|%b %d, %Y} <br> %{y:-.0f}'
                      )

        title = f'Cumulative Covid {label.lower()} in {state}'
        layout = dict(title=title,
                      yaxis_title=f'Confirmed # of {label}',
                      xaxis_title='Date/Time',
                      font=dict(family="Courier New, monospace",
                                size=16))
        data = [trace]
        fig = dict(data=data, layout=layout)
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


def heat_map_mask_use():
    df = df_dict['counties']
    df['countyfp'] = df['countyfp'].apply(lambda x: str(int(x)).zfill(5))
    df['wear_mask_prob'] = 0.25 * df['rarely'] + 0.5 * df['sometimes'] + \
                0.75 * df['frequently'] + 1.0 * df['always']
    df['county'] = df.apply(lambda x: fip_to_county(x.countyfp), axis=1)
    df['state_code'] = df.apply(lambda x: fip_to_state(x.countyfp), axis=1)
    df = df.drop(df[df['state_code'] == 'N/A'].index).reset_index(drop=True)
    df['state'] = df['state_code'].apply(lambda x: state_map_dict[x])
    fig = px.choropleth(df,
                        locations='countyfp',
                        geojson=county_json,
                        scope="usa",
                        color='wear_mask_prob', # a column in the dataset
                        hover_name='state', # column to add to hover information
                        hover_data = {'county': True, 'countyfp': False, 'wear_mask_prob': ':.3f'},
                        color_continuous_scale=px.colors.sequential.Reds,
                       )
    fig.update_layout(title_text="Heat Map - Who is Wearing Masks in US Counties"),
    fig.update_coloraxes(colorbar_title="<b>Color</b><br>Wear Mask Prob")
    #fig.update(layout_coloraxis_showscale=False)
    fig.update_layout(margin={"r":0,"l":0,"b":0})
    return fig

def scatter_matrix():
    df = df_dict['states']
    df.fips = df.fips.apply(lambda x: str(x).zfill(2))
    df = df[df.date == max(df.date)]
    df = df.drop(columns='date', axis=1).reset_index(drop=True)
    state_pop = df_dict['state-population']
    state_area =  df_dict['state-area']

    mask_use = df_dict['counties']
    mask_use.countyfp = mask_use.countyfp.apply(lambda x: str(x).zfill(5))
    mask_use['wear_mask_prob'] = 0.25 * mask_use['rarely'] + 0.5 * mask_use['sometimes'] + \
                    0.75 * mask_use['frequently'] + 1.0 * mask_use['always']
    mask_use['state_code'] = mask_use.apply(lambda x: fip_to_state(x.countyfp), axis=1)
    mask_use['county'] = mask_use.apply(lambda x: fip_to_county(x.countyfp), axis=1)
    df_agg = mask_use.groupby('state_code').agg(['mean'])
    df_agg.columns = ["_".join(x) for x in np.ravel(df_agg.columns)]
    df_agg.reset_index(inplace=True)
    df_agg.rename(columns={'wear_mask_prob_mean' : 'wear_mask_prob'}, inplace=True)
    df_agg = df_agg[['state_code', 'wear_mask_prob']]
    df_agg.drop(df_agg[df_agg['state_code'] == 'N/A'].index, inplace = True)
    df_agg.drop(df_agg[df_agg['state_code'] == 'DC'].index, inplace = True)
    df_agg['state'] = df_agg['state_code'].apply(lambda x: state_map_dict[x])
    df_agg = df_agg[['state', 'wear_mask_prob']]
    data_frames = [df, state_pop, state_area, df_agg]
    df_merged = reduce(lambda left, right: pd.merge(left,right,on=['state'],
                                                how='inner'), data_frames)

    df_merged['CFR'] = df_merged['deaths'] / df_merged['cases']
    df_merged['IR'] = df_merged['cases'] / df_merged['total']
    df_merged['PD'] = df_merged['total'] / df_merged['area']
    df_merged['WMP'] = df_merged['wear_mask_prob']
    df_ana = df_merged.loc[:, ['state', 'CFR', 'IR', 'PD', 'WMP']]
    df_ana[['CFR', 'IR', 'PD', 'WMP']] = np.round(df_ana[['CFR', 'IR', 'PD', 'WMP']], 3)

    fig = go.Figure(data=go.Splom(
                dimensions=[dict(label='CFR', # 'Fatality rate',
                                 values=df_ana['CFR']),
                            dict(label='IR', #'Infection rate',
                                 values=df_ana['IR']),
                            dict(label='PD', #'Population density',
                                 values=df_ana['PD']),
                            dict(label='WMP', #'Wear mask prob.',
                                 values=df_ana['WMP'])],
                text=df_ana['state'],
#                 hovertemplate="%{x}, %{y}",
                marker=dict(showscale=False, # colors encode categorical variables
                            line_color='white', line_width=0.5),
                showupperhalf=False,
                ))

    fig.update_layout(
    title='Scatter Matrix',
    dragmode='select',
    width=600,
    height=600,
    hovermode='closest',
    )
    return fig


def correlation_matrix():
    df = df_dict['states']
    df.fips = df.fips.apply(lambda x: str(x).zfill(2))
    df = df[df.date == max(df.date)]
    df = df.drop(columns='date', axis=1).reset_index(drop=True)
    state_pop = df_dict['state-population']
    state_area =  df_dict['state-area']

    mask_use = df_dict['mask-use-by-county']
    mask_use.countyfp = mask_use.countyfp.apply(lambda x: str(x).zfill(5))
    mask_use['wear_mask_prob'] = 0.25 * mask_use['rarely'] + 0.5 * mask_use['sometimes'] + \
                    0.75 * mask_use['frequently'] + 1.0 * mask_use['always']
    mask_use['state_code'] = mask_use.apply(lambda x: fip_to_state(x.countyfp), axis=1)
    mask_use['county'] = mask_use.apply(lambda x: fip_to_county(x.countyfp), axis=1)
    df_agg = mask_use.groupby('state_code').agg(['mean'])
    df_agg.columns = ["_".join(x) for x in np.ravel(df_agg.columns)]
    df_agg.reset_index(inplace=True)
    df_agg.rename(columns={'wear_mask_prob_mean' : 'wear_mask_prob'}, inplace=True)
    df_agg = df_agg[['state_code', 'wear_mask_prob']]
    df_agg.drop(df_agg[df_agg['state_code'] == 'N/A'].index, inplace = True)
    df_agg.drop(df_agg[df_agg['state_code'] == 'DC'].index, inplace = True)
    df_agg['state'] = df_agg['state_code'].apply(lambda x: state_map_dict[x])
    df_agg = df_agg[['state', 'wear_mask_prob']]
    data_frames = [df, state_pop, state_area, df_agg]
    df_merged = reduce(lambda left, right: pd.merge(left,right,on=['state'],
                                                how='inner'), data_frames)

    df_merged['CFR'] = df_merged['deaths'] / df_merged['cases']
    df_merged['IR'] = df_merged['cases'] / df_merged['total']
    df_merged['PD'] = df_merged['total'] / df_merged['area']
    df_merged['WMP'] = df_merged['wear_mask_prob']
    df_ana = df_merged.loc[:, ['state', 'CFR', 'IR', 'PD', 'WMP']]
    df_ana[['CFR', 'IR', 'PD', 'WMP']] = np.round(df_ana[['CFR', 'IR', 'PD', 'WMP']], 3)
    df_corr = df_ana[['CFR', 'IR', 'PD', 'WMP']].corr()

    fig = go.Figure(data=go.Heatmap(z=df_corr,
                                    x=['CFR', 'IR', 'PD', 'WMP'],
                                    y=['CFR', 'IR', 'PD', 'WMP'],
                                    colorscale='Blues',
                                   hovertemplate=" Corr(%{x}, %{y}) = %{z:.2f}"),
                   )
    fig.update_layout(
        title='Correlation Matrix',
        height=600,
        width=600,
        )
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
            #### Time-series cumulative cases and deaths
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
                dcc.Graph(id='time-series-total', style={'height': 500, 'width': 1100})
                ],
                style={'width': '98%', 'float': 'right', 'display': 'inline-block'}),

            # Time series curves for daily cases and deaths in US
                    dcc.Markdown('''
            #### Time-series daily reported cases and deaths
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
                dcc.Graph(id='time-series-daily', style={'height': 500, 'width': 1100})
            ],
                style={'width': '98%', 'float': 'right', 'display': 'inline-block'}),

        dcc.Markdown('''
        ### Case and Death Count by State
        ''', className='row eleven columns', style={'paddingLeft': '0%'}),

             # Time series curves for cases and deaths by state
            dcc.Markdown('''
            #### Time-series cases and deaths by state
            ''', className='row eleven columns', style={'paddingLeft': '5%'}),

            html.Div([
                html.Div([
                    html.Label( ['Label:'],
                        style={'font-weight': 'bold', 'float': 'left',
                               'color': 'white', 'display': 'inline-block',
                               },
                        ),
                    dcc.RadioItems(
                        id='label-by-state',
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
                        }),
                    html.Label( ['Plot type:'],
                        style={'font-weight': 'bold', 'float': 'left',
                               'color': 'white', 'display': 'inline-block',
                               },
                        ),
                    dcc.RadioItems(
                        id='plot-type',
                        options=[{'label': i.title(), 'value': i} for i in ['cumulative', 'daily']],
                        value='daily',
                        labelStyle={
                        'display': 'inline-block',
                        },
                        style={
                        'width': '20%',
                        'float': 'left',
                        'font-weight': 'bold',
                        'color': 'white',
                        }),
                    html.Label( ['State:'],
                        style={'font-weight': 'bold', 'float': 'left',
                               'color': 'white', 'display': 'inline-block',
                               'margin-right': '10px'
                               },
                        ),
                    dcc.Dropdown(
                        id='state-name',
                        options=[{'label': i, 'value': i} for i in list(all_states)],
                        value='Rhode Island',
                        style={'width': '40%', 'float':'left', 'display': 'inline-block'}
                    ),],  style={'width': '98%', 'display': 'inline-block'}),
                dcc.Graph(id='time-series-state', style={'height': 500, 'width': 1100})
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

def enhancement_summary():
    """
    All Enhancement details should be arranged here.
    """
    return html.Div(children=[
         dcc.Markdown('''
          ### Who is Wearing Masks in US Counties？
         ''', className='row eleven columns', style={'paddingLeft': '6%'}),
         dcc.Graph(id='mask-use-by-county', figure=heat_map_mask_use(),
                   style={'height': 800, 'width': 1000, 'display': 'inline-block'}),

         dcc.Markdown('''
          ### Whether Population Density and Propensity of Wearing Masks Affect the Spread?
         ''', className='row eleven columns', style={'paddingLeft': '0%'}),
        html.Div([
             html.Label( ['CFR: Case Fatality Rate'],
                        style={'font-weight': 'bold', 'float': 'left',
                               'color': 'white', 'display': 'inline-block',
                               },
                        ),
             html.Label( ['IR: Infeaction Rate',],
                        style={'font-weight': 'bold', 'float': 'left','margin-left': '100px',
                               'color': 'white', 'display': 'inline-block',
                               },
                        ),
             html.Label( ['PD: Population Density',],
                        style={'font-weight': 'bold', 'float': 'left', 'margin-left': '100px',
                               'color': 'white', 'display': 'inline-block',
                               },
                        ),
             html.Label( ['WMP: Wear Mask Probability'],
                style={'font-weight': 'bold', 'float': 'left','margin-left': '100px',
                       'color': 'white', 'display': 'inline-block',
                       },
                ),
             dcc.Graph(id='scatter-matrix', figure=scatter_matrix(),
                       style={'width': '48%',  'display': 'inline-block'}),
             dcc.Graph(id='correlation-matrix', figure=correlation_matrix(),
                       style={'width': '48%', 'float':'right', 'display': 'inline-block'}),
         ], style={'width': '100%',  'display': 'inline-block'}),
    ]
                   )

# Sequentially add page components to the app's layout
def dynamic_layout():
    return html.Div([
        page_header(),
        html.Hr(),
        project_description(),
        visualization_description(),
        visualization_summary(),
        enhancement_description(),
        enhancement_summary(),
        # architecture_summary(),
    ], className='row', id='content')

# set layout to a function which updates upon reloading
app.layout = dynamic_layout

if __name__ == '__main__':
    app.run_server(debug=True, port=8888, host='0.0.0.0')