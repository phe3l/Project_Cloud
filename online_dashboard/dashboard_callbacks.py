from dash import Dash, html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
import plotly.express as px
from dash_iconify import DashIconify
import pandas as pd
import utils
from datetime import datetime

def register_callbacks(app, df, plots_legend, dashboard_service):
    @app.callback(
        [Output("avg-air-quality-plot", "figure"),
         Output("avg-temp-plot", "figure"),
         Output("avg-humidity-plot", "figure")],
        Input('interval-component', 'n_intervals')
    )
    def update_averages_plots(n_intervals):
        return _update_averages_plots(n_intervals, df, plots_legend)
    
    @app.callback(
        [Output("temp-plot", "figure"),
        Output("humidity-plot", "figure")],
        [Input("date-selector", "value")]
    )
    def update_daily_graph(selected_date):
        return _update__daily_graph(selected_date, df)
    
    @callback(
        [Output("header-time", "children"),
        Output("header-location", "children"),
        Output("header-temperature", "children")],
        [Input('interval-component', 'n_intervals')]
    )
    def update_header(n_intervals):
        return _update_header(n_intervals, df, dashboard_service)  




def _update_averages_plots(n_intervals, df, plots_legend):
    daily_averages = utils.calculate_daily_averages(df)
    
    temperature_averages = daily_averages.dropna(subset=["Indoor Temperature", "Outdoor Temperature"], how="any")
    temperature_fig = px.line(
        temperature_averages,
        x=temperature_averages.index,
        y=["Indoor Temperature", "Outdoor Temperature"],
        labels={"datetime": "", "value": "Temperature (°C)", "variable": "", "indoor_temp": "Indoor Temperature"},
        range_y=[0, 40],
        title="<b>Daily Temperature Averages</b>",
        line_shape="spline",
        template="plotly_dark"
    )
    
    
    humidity_averages = daily_averages.dropna(subset=["Indoor Humidity", "Outdoor Humidity"], how="any")
    humidity_fig = px.line(
        humidity_averages,
        x=humidity_averages.index,
        y=["Indoor Humidity", "Outdoor Humidity"],
        labels={"datetime": "", "value": "Humidity (%)", "variable": ""},
        range_y=[0, 100],
        title="<b>Daily Humidity Averages</b>",
        line_shape="spline",
        template="plotly_dark",
        color_discrete_map={
            "Indoor Humidity": "green",  # Color for Indoor Humidity line
            "Outdoor Humidity": "orange"  # Color for Outdoor Humidity line
        }
    )
    
    air_quality_averages = daily_averages.dropna(subset=["Indoor Air Quality"], how="any")
    air_quality_fig = px.line(
        air_quality_averages,
        x=air_quality_averages.index,
        y="Indoor Air Quality",
        labels={"datetime": "", "value": "Air Quality", "variable": ""},
        range_y=[0, 100],
        title="<b>Daily Air Quality Averages</b>",
        line_shape="spline",
        template="plotly_dark"
    )

    temperature_fig.update_layout(legend=plots_legend, paper_bgcolor='rgba(0, 0, 0, 0)', title_x=0.5)
    temperature_fig.update_traces(fill='tozeroy')
    humidity_fig.update_layout(legend=plots_legend, paper_bgcolor='rgba(0, 0, 0, 0)', title_x=0.5)
    humidity_fig.update_traces(fill='tozeroy')
    air_quality_fig.update_layout(legend=plots_legend, paper_bgcolor='rgba(0, 0, 0, 0)', title_x=0.5)
    air_quality_fig.update_traces(fill='tozeroy', line=dict(color='white'))
    
    return air_quality_fig, temperature_fig, humidity_fig



def _update__daily_graph(selected_date, df):
    dff = df[df["datetime"].dt.date == pd.to_datetime(selected_date).date()]
    dff = utils.prepare_daily_data(dff, pd.to_datetime(selected_date).date())
    
    temp_fig =px.line(
        dff.dropna(),
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



def _update_header(n_intervals, df, dashboard_service):
    last_updated_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    #get last recorded row in df based on datetime
    max_datetime = df["datetime"].max()
    
    ip = df[df["datetime"] == max_datetime]["ip_address"].values[0]
    current_conditions = dashboard_service.fetch_current_weather(ip)
    location = utils.get_location_via_ip(ip)
    
    return last_updated_time, location, current_conditions
    
    