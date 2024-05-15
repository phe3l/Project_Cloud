from dash import Dash, html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify

def separator():
    return html.Div(style={'height': '1px', 'background-color': '#85929E', 'margin': 30})


import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
from dash import html

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
        color="#525f7f",
        dark=True,
        sticky="top"
    )
    return navbar


plots_legend=dict(
    orientation="h",
    yanchor="top",
    y=-0.15,  # Position the legend below the graph
    xanchor="center",
    x=0.5
)