from dash import Dash, html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
import dash_daq as daq


plots_legend=dict(
    orientation="h",
    yanchor="top",
    y=-0.15,  # Position the legend below the graph
    xanchor="center",
    x=0.5
)

theme = {
    'dark': True,
    'detail': 'lightblue',
    'primary': '#00EA64',
    'secondary': 'white',
}

def header():
    navbar = dbc.Navbar(
        dbc.Container([
            dbc.Col(html.Div([
                DashIconify(icon="mdi:clock", width=15, style={"marginRight": 5, "color": "#fff"}),
                html.Span("Dashboard Last Updated: ", className="header-label"),
                html.Span("Loading...", className="header-value", id="header-time")
                ]), 
                width=4
            ),
            dbc.Col(html.Div([
                DashIconify(icon="material-symbols:home", width=15, style={"marginRight": 5, "color": "#fff"}),
                html.Span("IoT Device Last Location: ", className="header-label"),
                html.Span("Loading...", className="header-location", id="header-location")
                ]), 
                width=4, 
                style={"textAlign": "center"}
            ),
            dbc.Col(html.Div([
                DashIconify(icon="material-symbols:info", width=15, style={"marginRight": 5, "color": "#fff"}),
                html.Span("IoT Device Last Data Entry: ", className="header-label"),
                html.Span("Loading...", className="header-value", id="header-last-data")
                ]), 
                width=4,
                style={"textAlign": "right"}
            )
        ], className="header-row"),
        color="#34495E",
        dark=True,
        sticky="top"
    )
    return navbar

def average_weather_plots_row():
    row = dbc.Row([
            dbc.Col(
                dcc.Graph(id="avg-temp-plot", className="dashboard-container"),
                width=4
            ),
            dbc.Col(
                dcc.Graph(id="avg-humidity-plot", className="dashboard-container"),
                width=4
            ),
            dbc.Col(
                dcc.Graph(id="avg-air-quality-plot", className="dashboard-container"),
                width=4
            )
        ], style={"margin-bottom": "20px"})
    return row 

def current_weather_row():
    row = daq.DarkThemeProvider(theme=theme, children=[
        dbc.Row([
            dbc.Col(
                dbc.Card(
                    dbc.CardBody([
                        html.P("Current Weather", className="card-title", style={"fontSize": 17, "fontWeight": "bold", "marginBottom": 10}),
                        dbc.Row([
                            dbc.Col(DashIconify(icon="bxs:message-rounded-error", width=35, id="online_weather_icon"), width="auto"),
                            dbc.Col(html.P("loading...", className="card-text", id="online_weather_description"), width="auto", style={"fontSize": 17}),
                        ], align="center"),
                        dbc.Row([
                            dbc.Col(DashIconify(icon="ph:wind", width=35), width="auto"),
                            dbc.Col(html.P("loading...", className="card-text", id="online_wind_speed"), width="auto", style={"fontSize": 17}),
                        ], align="center"),
                        dbc.Row([
                            dbc.Col(DashIconify(icon="material-symbols:visibility", width=35), width="auto"),
                            dbc.Col(html.P("loading...", className="card-text", id="online_weather_visibility"), width="auto", style={"fontSize": 17}),
                        ], align="center"),
                        dbc.Row([
                            dbc.Col(DashIconify(icon="ic:outline-diamond", width=35), width="auto"),
                            dbc.Col(html.P("loading...", className="card-text", id="current_air_quality"), width="auto", style={"fontSize": 17}),
                        ], align="center"),
                    ]), color="rgba(0,0,0,0)", style={"color": "white", "border": "0px"}
                ), 
                width=4
            ),
            dbc.Col(
                html.Div(
                    daq.Thermometer(
                        id='indoor_temp_thermometer',
                        value=5,
                        min=-10,
                        max=40,
                        height=100,
                        width = 10,
                        color="#FFA07A",
                        label={"label": "Indoor Temperature", "style": {"fontSize": 17, "color": "white", "fontWeight": "bold"}},
                        showCurrentValue=True,
                        style = {"margin-bottom": -25}
                    ), className="m-auto"
                ),
                width=2, style={"margin": "20px 0px 0px 0px"}, className="d-flex",
            ), 
            dbc.Col([
                html.Div(
                    daq.Gauge(
                        id='indoor_humidity_gauge',
                        min=0,
                        max=100,
                        size=130,
                        color="#FFA07A",
                        units="%",
                        showCurrentValue=True,
                        label={"label": "Indoor Humidity", "style": {"fontSize": 17, "color": "white", "fontWeight": "bold"}},
                        style = {"margin-bottom": -25}
                    ), className="m-auto"
                ),
                ],
                width=2, style={"margin": "20px 0px 0px 0px"}, className="d-flex"
            ),
            dbc.Col(
                html.Div(
                    daq.Thermometer(
                        id='outdoor_temp_thermometer',
                        value=5,
                        min=-10,
                        max=40,
                        height=100,
                        width = 10,
                        color="lightblue",
                        label={"label": "Outdoor Temperature", "style": {"fontSize": 17, "color": "white", "fontWeight": "bold"}},
                        showCurrentValue=True,
                        style = {"margin-bottom": -25}
                    ), className="m-auto"
                ),
                width=2, style={"margin": "20px 0px 0px 0px"}, className="d-flex",
            ), 
            dbc.Col([
                html.Div(
                    daq.Gauge(
                        id='outdoor_humidity_gauge',
                        min=0,
                        max=100,
                        size=130,
                        color="lightblue",
                        units="%",
                        showCurrentValue=True,
                        label={"label": "Outdoor Humidity", "style": {"fontSize": 17, "color": "white", "fontWeight": "bold"}},
                        style = {"margin-bottom": -25}
                    ), className="m-auto"
                ),
                ],
                width=2, style={"margin": "20px 0px 0px 0px"}, className="d-flex"
            ),
            ],
            className="dashboard-container", style={"margin": "0px 0px 20px 0px"}
        )]
    )
    return row

def history_explore_row(dates_list):
    row = dbc.Row([
            dbc.Col([
                html.P("Explore Weather History", style={"fontSize": 17, "fontWeight": "bold", "marginBottom": 40}),
                html.P("Select the graph type and date to explore the weather history", style={"fontSize": 17, "marginBottom": 40}),
                dcc.Dropdown(
                    id="graph-selector",
                    options=["Indoor & Outdoor Temperature", "Indoor & Outdoor Humidity", "Indoor Air Quality", "Indoor Temperature vs Indoor Humidity", "Indoor Temperature vs Indoor Air Quality", "Indoor Humidity vs Indoor Air Quality"],
                    value="Indoor & Outdoor Temperature",
                    style={"margin-bottom": "20px"},
                    clearable=False,
                    searchable=False,
                    optionHeight=60
                ),
                dcc.Dropdown(
                    id="date-selector",
                    options=dates_list,
                    value=dates_list[0],
                    clearable=False,
                    style={"margin-bottom": "40px"}
                ),
                html.P("", style={"fontSize": 17, "fontWeight": "bold"}, id="weather-history-additional-info"),
                ],
                width={"size": 4, "offset": 1},
                align="top",
                style={"padding-right": "30px", "margin-top": "40px"}
            ),
            dbc.Col(
                dcc.Graph(id="weather-history-plot"),
                width=6
            )
        ], style={"margin": "0px 0px 60px 0px", "color": "white"}, className="dashboard-container")
    return row 