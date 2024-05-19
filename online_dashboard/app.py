from dash import Dash, html, dcc
import dash_bootstrap_components as dbc
from dashboard_service import DashboardService
from dashboard_elements import header, plots_legend, average_weather_plots_row, current_weather_row, history_explore_row
from dashboard_callbacks import register_callbacks

dashboard_service = DashboardService()
df = dashboard_service.fetch_weather_data()

app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP])


app.layout = html.Div([
    
    header(),
    
    dcc.Interval(id='interval-component', interval=60*1000, n_intervals=0),
    html.Div([
        
        current_weather_row(),
        
        average_weather_plots_row(),
        
        history_explore_row(dates_list=df['datetime'].dt.strftime('%d/%m/%Y').unique())
        
    ], style={"margin": "20px 50px 20px 50px"}),
    
])

register_callbacks(app, df, plots_legend, dashboard_service)


if __name__ == "__main__":
    app.run_server(host='0.0.0.0', port=8080, debug=True)