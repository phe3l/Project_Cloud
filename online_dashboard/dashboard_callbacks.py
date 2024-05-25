from dash import callback, Output, Input
import plotly.express as px
import pandas as pd
import utils
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def register_callbacks(app, df, plots_legend, dashboard_service):
    @callback(
        [Output("avg-air-quality-plot", "figure"),
         Output("avg-temp-plot", "figure"),
         Output("avg-humidity-plot", "figure")],
        Input('interval-component', 'n_intervals')
    )
    def update_averages_plots(n_intervals):
        return _update_averages_plots(n_intervals, df, plots_legend)
    
    @callback(
        Output("weather-history-plot", "figure"),
        Output("weather-history-additional-info", "children"),
        [Input("graph-selector", "value"),
        Input("date-selector", "value")]
    )
    def update_daily_graph(selected_graph, selected_date):
        return _update__daily_graph(df, selected_graph, selected_date, plots_legend)
    
    @callback(
        Output("header-time", "children"),
        Output("header-location", "children"),
        Output("header-last-data", "children"),
        [Input('interval-component', 'n_intervals')]
    )
    def update_header(n_intervals):
        df = dashboard_service.fetch_weather_data()
        return _update_header(n_intervals, df, dashboard_service)  

    @callback(
        Output("indoor_temp_thermometer", "value"),
        Output("indoor_humidity_gauge", "value"),
        Output("outdoor_temp_thermometer", "value"),
        Output("outdoor_humidity_gauge", "value"),
        Output("online_weather_icon", "icon"),
        Output("online_weather_description", "children"),
        Output("online_wind_speed", "children"),
        Output("online_weather_visibility", "children"),
        Output("current_air_quality", "children"),
        Input('interval-component', 'n_intervals')
    )
    def update_current_weather_row(n_intervals):
        return _update_current_weather_row(df, dashboard_service)


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
            "Indoor Humidity": "orange",  # Color for Indoor Humidity line
            "Outdoor Humidity": "green"  # Color for Outdoor Humidity line
        }
    )
    
    air_quality_averages = daily_averages.dropna(subset=["Indoor Air Quality"], how="any")
    air_quality_fig = px.line(
        air_quality_averages,
        x=air_quality_averages.index,
        y="Indoor Air Quality",
        labels={"datetime": "", "value": "Air Quality", "variable": ""},
        range_y=[0, 5000],
        title="<b>Daily Air Quality Averages</b>",
        line_shape="spline",
        template="plotly_dark"
    )

    temperature_fig.update_layout(legend=plots_legend, plot_bgcolor='rgba(0, 0, 0, 0)', paper_bgcolor='rgba(0, 0, 0, 0)', title_x=0.5)
    temperature_fig.update_traces(fill='tozeroy', mode='lines+markers')
    humidity_fig.update_layout(legend=plots_legend, plot_bgcolor='rgba(0, 0, 0, 0)', paper_bgcolor='rgba(0, 0, 0, 0)', title_x=0.5)
    humidity_fig.update_traces(fill='tozeroy', mode='lines+markers')
    air_quality_fig.update_layout(legend=plots_legend, plot_bgcolor='rgba(0, 0, 0, 0)', paper_bgcolor='rgba(0, 0, 0, 0)', title_x=0.5, yaxis_title="eCO2 concentration (ppm)")
    air_quality_fig.update_traces(fill='tozeroy', line=dict(color='white'), mode='lines+markers')
    
    return air_quality_fig, temperature_fig, humidity_fig



def _update__daily_graph(df, selected_graph, selected_date, plots_legend):
    
    if selected_date != "Entire History":
        selected_date = datetime.strptime(selected_date, "%d/%m/%Y")
        dff = df[df["datetime"].dt.date == selected_date.date()]
    else:
        dff = df
        
    dff = utils.prepare_daily_data(dff)
    weather_history_additional_info = ""
    
    
    if selected_graph == "Indoor & Outdoor Temperature":
        fig = px.line(
            dff,
            x=dff.index,
            y=["Indoor Temperature", "Outdoor Temperature"],
            labels={"datetime": "", "value": "Temperature (°C)", "variable": ""},
            range_y=[0, 40],
            title="<b>Indoor & Outdoor Temperature</b>",
            line_shape="spline",
            template="plotly_dark"
        )
        correlation = dff["Indoor Temperature"].corr(dff["Outdoor Temperature"])
        weather_history_additional_info = f"Correlation between indoor & outdoor temperature: {correlation:.2f}"
        
    if selected_graph == "Indoor & Outdoor Humidity":
        fig = px.line(
            dff,
            x=dff.index,
            y=["Indoor Humidity", "Outdoor Humidity"],
            labels={"datetime": "", "value": "Humidity (%)", "variable": ""},
            range_y=[0, 100],
            title="<b>Indoor & Outdoor Humidity</b>",
            line_shape="spline",
            template="plotly_dark",
            color_discrete_map={
                "Indoor Humidity": "orange",  # Color for Indoor Humidity line
                "Outdoor Humidity": "green"  # Color for Outdoor Humidity line
            }
        )
        correlation = dff["Indoor Humidity"].corr(dff["Outdoor Humidity"])
        weather_history_additional_info = f"Correlation between indoor & outdoor humidity: {correlation:.2f}"
        
    if selected_graph == "Indoor Air Quality":
        fig = px.line(
            dff,
            x=dff.index,
            y="Indoor Air Quality",
            labels={"datetime": "", "value": "Air Quality", "variable": ""},
            range_y=[0, 5000],
            title="<b>Indoor Air Quality</b>",
            line_shape="spline",
            template="plotly_dark",
        )
        fig.update_layout(yaxis_title="eCO2 concentration (ppm)")
        
    if selected_graph == "Indoor Temperature vs Indoor Humidity":
        # Create a figure with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Scatter(x=dff.index, y=dff["Indoor Temperature"], name="Indoor Temperature", line=dict(color="orange")),
            secondary_y=False,
        )
        fig.add_trace(
            go.Scatter(x=dff.index, y=dff["Indoor Humidity"], name="Indoor Humidity", line=dict(color="green")),
            secondary_y=True,
        )

        fig.update_layout(
            title_text="<b>Indoor Temperature vs Indoor Humidity</b>",
            template="plotly_dark"
        )
        fig.update_xaxes(title_text="")

        fig.update_yaxes(title_text="Indoor Temperature (°C)", secondary_y=False, range=[0, 40])
        fig.update_yaxes(title_text="Indoor Humidity (%)", secondary_y=True, range=[0, 100])

        correlation = dff["Indoor Temperature"].corr(dff["Indoor Humidity"])
        weather_history_additional_info = f"Correlation between indoor temperature & humidity: {correlation:.2f}"
        
    if selected_graph == "Indoor Temperature vs Indoor Air Quality":
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Scatter(x=dff.index, y=dff["Indoor Temperature"], name="Indoor Temperature", line=dict(color="orange")),
            secondary_y=False,
        )
        fig.add_trace(
            go.Scatter(x=dff.index, y=dff["Indoor Air Quality"], name="Indoor Air Quality", line=dict(color="white")),
            secondary_y=True,
        )

        fig.update_layout(
            title_text="<b>Indoor Temperature vs Indoor Air Quality</b>",
            template="plotly_dark"
        )
        fig.update_xaxes(title_text="")

        fig.update_yaxes(title_text="Indoor Temperature (°C)", secondary_y=False, range=[0, 40])
        fig.update_yaxes(title_text="Indoor Air Quality (ppm)", secondary_y=True, range=[0, 5000])

        correlation = dff["Indoor Temperature"].corr(dff["Indoor Air Quality"])
        weather_history_additional_info = f"Correlation between indoor temperature & air quality: {correlation:.2f}"
        
    if selected_graph == "Indoor Humidity vs Indoor Air Quality":
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])

        fig.add_trace(
            go.Scatter(x=dff.index, y=dff["Indoor Humidity"], name="Indoor Humidity", line=dict(color="green")),
            secondary_y=False,
        )
        fig.add_trace(
            go.Scatter(x=dff.index, y=dff["Indoor Air Quality"], name="Indoor Air Quality", line=dict(color="white")),
            secondary_y=True,
        )

        fig.update_layout(
            title_text="<b>Indoor Humidity vs Indoor Air Quality</b>",
            template="plotly_dark"
        )
        fig.update_xaxes(title_text="")

        fig.update_yaxes(title_text="Indoor Humidity (%)", secondary_y=False, range=[0, 100])
        fig.update_yaxes(title_text="Indoor Air Quality (ppm)", secondary_y=True, range=[0, 5000])

        correlation = dff["Indoor Humidity"].corr(dff["Indoor Air Quality"])
        weather_history_additional_info = f"Correlation between indoor humidity & air quality: {correlation:.2f}"

    
    fig.update_layout(plot_bgcolor='rgba(0, 0, 0, 0)', paper_bgcolor='rgba(0, 0, 0, 0)', title_x=0.5, legend = plots_legend)
    fig.update_traces(fill='tozeroy')
    return fig, weather_history_additional_info



def _update_header(n_intervals, df, dashboard_service):
    dashboard_last_updated_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    #get last recorded row in df based on datetime
    max_datetime = df["datetime"].max()
    iot_last_updated_time = max_datetime.strftime("%d/%m/%Y %H:%M:%S")
    
    ip = df[df["datetime"] == max_datetime]["ip_address"].values[0]
    location = utils.get_location_via_ip(ip)
    
    return dashboard_last_updated_time, location, iot_last_updated_time



def _update_current_weather_row(df: pd.DataFrame, dashboard_service):
    dff = df.dropna(subset=["indoor_temp", "outdoor_temp", "indoor_humidity", "outdoor_humidity", "indoor_air_quality"], how="any")
    #sort dff by datetime descending
    dff = dff.sort_values("datetime", ascending=False)
    
    current_indoor_temperature = dff["indoor_temp"].iloc[0]
    current_indoor_humidity = dff["indoor_humidity"].iloc[0]
    current_outdoor_temperature = dff["outdoor_temp"].iloc[0]
    current_outdoor_humidity = dff["outdoor_humidity"].iloc[0]
    
    current_weather = dashboard_service.fetch_current_weather(dff["ip_address"].iloc[0])
    
    online_weather_icon = utils.get_weather_icon_by_description(current_weather["weather"][0]["main"])
    online_weather_description = (current_weather["weather"][0]["description"]).title()
    online_wind_speed = "Wind Speed: " + str(round(current_weather["wind"]["speed"])) + " km/h"
    online_weather_visibility = "Visibility: " + str(round(current_weather["visibility"] / 1000)) + " km"
    current_air_quality = "Indoor Air Quality: " + str(int(dff["indoor_air_quality"].iloc[0])) + " ppm of eCO2"
    
    return current_indoor_temperature, current_indoor_humidity, current_outdoor_temperature, current_outdoor_humidity, \
        online_weather_icon, online_weather_description, online_wind_speed, online_weather_visibility, current_air_quality
    