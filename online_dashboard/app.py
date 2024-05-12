from dash import Dash, html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
from dashboard_service import DashboardService

df = DashboardService().fetch_weather_data()

app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div([
    html.H1(children="Weather Dashboard", style={"textAlign": "center"}), 
    dcc.Dropdown(
        id="date-selector",
        options=[date for date in df["datetime"].dt.date.unique()],
        value=df["datetime"].dt.date.unique()[0]
        ),
    dcc.Graph(id="weather-plot")
])

@callback(
    Output("weather-plot", "figure"),
    Input("date-selector", "value")
)
def update_graph(selected_date):
    dff = df[df["datetime"].dt.date == pd.to_datetime(selected_date).date()]
    
    fig =px.line(
        dff,
        x="datetime",
        y="indoor_temp",
        labels={"datetime": "Time", "temperature": "Temperature (°C)"},
    )
    
    return fig

if __name__ == "__main__":
    app.run(debug=True)