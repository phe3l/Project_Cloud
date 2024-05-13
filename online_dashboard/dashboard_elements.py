from dash import Dash, html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify

def separator():
    return html.Div(style={'height': '1px', 'background-color': '#85929E', 'margin': 30})


def header():
    header = html.Div([
        dbc.Row([
            dbc.Col(html.Div([
                html.Span("Last Updated Time: ", className="header-label"),
                html.Span("19-01-2022 11:58:43", className="header-value")
                ]), 
                width=4
            ),
            dbc.Col(html.Div([
                DashIconify(icon="material-symbols:home", width=15, style={"marginRight": 5}),
                html.Span("IoT Device Location:", className="header-label"),
                html.Span("Lausanne, Switzerland", className="header-location")
                ]), 
                width=4
            ),
            dbc.Col(html.Div([
                html.Span("8°C", className="header-temperature")
                ]), 
                width=4,
                style={"textAlign": "right"}
            )
        ], className="header-row"),
    ], className="header-container")
    return header