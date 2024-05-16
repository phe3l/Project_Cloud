from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
from dashboard_service import DashboardService
from dashboard_elements import header, plots_legend, average_metrics_plots_row, current_metrics_row
from dashboard_callbacks import register_callbacks

dashboard_service = DashboardService()
df = dashboard_service.fetch_weather_data()

app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP])


app.layout = html.Div([
    
    header(),
    
    dcc.Interval(id='interval-component', interval=60*1000, n_intervals=0),
    html.Div([
        
        current_metrics_row(),
        
        average_metrics_plots_row(),
        
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

register_callbacks(app, df, plots_legend, dashboard_service)


if __name__ == "__main__":
    app.run(debug=True)