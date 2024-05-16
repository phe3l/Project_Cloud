from dash import Dash, html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify

def separator():
    return html.Div(style={'height': '1px', 'background-color': '#85929E', 'margin': 30})


import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
from dash import html

plots_legend=dict(
    orientation="h",
    yanchor="top",
    y=-0.15,  # Position the legend below the graph
    xanchor="center",
    x=0.5
)

def header():
    navbar = dbc.Navbar(
        dbc.Container([
            dbc.Col(html.Div([
                DashIconify(icon="mdi:clock", width=15, style={"marginRight": 5, "color": "#fff"}),
                html.Span("Dashboard Last Updated: ", className="header-label"),
                html.Span("19-01-2022 11:58:43", className="header-value", id="header-time")
                ]), 
                width=4
            ),
            dbc.Col(html.Div([
                DashIconify(icon="material-symbols:home", width=15, style={"marginRight": 5, "color": "#fff"}),
                html.Span("IoT Device Last Location:", className="header-label"),
                html.Span("Lausanne, Switzerland", className="header-location", id="header-location")
                ]), 
                width=4, 
                style={"textAlign": "center"}
            ),
            dbc.Col(html.Div([
                DashIconify(icon="tabler:temperature-sun", width=15, style={"marginRight": 5, "color": "#fff"}),
                html.Span("Current Outside Conditions:", className="header-label"),
                html.Span("20°C", className="header-temperature", id="header-temperature"),
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

def average_metrics_plots_row():
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

def current_metrics_row():
    row = dbc.Row(
            dbc.Card(
                    dbc.CardBody([
                        html.H4("Current Weather", className="card-title"),
                        html.P(id="current-weather", className="card-text"),
                        DashIconify(icon="mdi:weather-partly-cloudy", width=50),
                        html.P(id="last-update-time", className="card-text"),
                    ]),
                    className="dashboard-container"
                ),
        style={"margin": "0px 0px 20px 0px"}
    )
    return row