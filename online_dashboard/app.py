from dash import Dash, html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
import plotly.express as px
from dash_iconify import DashIconify
import pandas as pd
from dashboard_service import DashboardService
import utils
from dashboard_elements import separator, header, plots_legend
from datetime import datetime

dashboard_service = DashboardService()
df = dashboard_service.fetch_weather_data()

app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP])


app.layout = html.Div([
    
    header(),
    
    dcc.Interval(id='interval-component', interval=60*1000, n_intervals=0),
    html.Div([
        dbc.Row(
            dbc.Card(
                    dbc.CardBody([
                        html.H4("Current Weather", className="card-title"),
                        html.P(id="current-weather", className="card-text"),
                        DashIconify(icon="mdi:weather-partly-cloudy", width=50),
                        html.P(id="last-update-time", className="card-text"),
                    ]),
                    className="dashboard-container"
                ),
        style={"margin": "0px 0px 20px 0px"}),
        dbc.Row([
            dbc.Col(
                
                width=4),
            dbc.Col(
                dcc.Graph(id="avg-temp-plot", className="dashboard-container"),
                width={"size": 4}
            ),
            dbc.Col(
                dcc.Graph(id="avg-humidity-plot", className="dashboard-container"),
                width={"size": 4}
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
    ], style={"margin": "20px 50px 20px 50px"}),
    
])

@callback(
    [Output("avg-temp-plot", "figure"),
     Output("avg-humidity-plot", "figure")],
    Input('interval-component', 'n_intervals')
)
def update__averages_plots(n_intervals):
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

    temperature_fig.update_layout(legend=plots_legend, paper_bgcolor='rgba(0, 0, 0, 0)', title_x=0.5)
    temperature_fig.update_traces(fill='tozeroy')
    humidity_fig.update_layout(legend=plots_legend, paper_bgcolor='rgba(0, 0, 0, 0)', title_x=0.5)
    humidity_fig.update_traces(fill='tozeroy')
    
    return temperature_fig, humidity_fig


@callback(
    [Output("temp-plot", "figure"),
     Output("humidity-plot", "figure")],
    [Input("date-selector", "value")]
)
def update__daily_graph(selected_date):
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

@callback(
    [Output("header-time", "children"),
     Output("header-location", "children"),
     Output("header-temperature", "children")],
    [Input('interval-component', 'n_intervals')]
)
def update_header(n_intervals):
    last_updated_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    #get last recorded row in df based on datetime
    max_datetime = df["datetime"].max()
    
    ip = df[df["datetime"] == max_datetime]["ip_address"].values[0]
    current_conditions = dashboard_service.fetch_current_weather(ip)
    location = utils.get_location_via_ip(ip)
    
    return last_updated_time, location, current_conditions

if __name__ == "__main__":
    app.run(debug=True)