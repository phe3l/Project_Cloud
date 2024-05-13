from dash import Dash, html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
import plotly.express as px
import pandas as pd
from dashboard_service import DashboardService
import utils
from dashboard_elements import separator, header

df = DashboardService().fetch_weather_data()

app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP])


app.layout = html.Div([
    
    header(),
    
    html.Div([
        separator(),
        dbc.Row([
            dbc.Col(
                dcc.Graph(id="avg-temp-plot"),
                width={"size": 6},
            ),
            dbc.Col(
                dcc.Graph(id="avg-humidity-plot"),
                width={"size": 6},
            )
        ]),
        separator(),
        dcc.Dropdown(
            id="date-selector",
            options=[date for date in df["datetime"].dt.date.unique()],
            value=df["datetime"].dt.date.unique()[0]
            ),
        dbc.Row([
            dbc.Col(
                dcc.Graph(id="temp-plot"),
                width={"size": 6},
            ),
            dbc.Col(
                dcc.Graph(id="humidity-plot"),
                width={"size": 6},
            )
        ]
        ),
    ], style={"margin": 50}),
    
])

@callback(
    [Output("temp-plot", "figure"),
     Output("humidity-plot", "figure")],
    [Input("date-selector", "value")]
)
def update_graph(selected_date):
    dff = df[df["datetime"].dt.date == pd.to_datetime(selected_date).date()]
    dff = utils.prepare_daily_data(dff, pd.to_datetime(selected_date).date())
    
    temp_fig =px.line(
        dff,
        x="datetime",
        y=["indoor_temp", "outdoor_temp"],
        labels={"datetime": "Time", "temperature": "Temperature (°C)"}
    )
    
    humidity_fig = px.line(
        dff,
        x="datetime",
        y=["indoor_humidity", "outdoor_humidity"],
        labels={"datetime": "Time", "humidity": "Humidity (%)"}
    )
    
    return temp_fig, humidity_fig

if __name__ == "__main__":
    app.run(debug=True)