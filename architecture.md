# Project Architecture

## M5stack Device Folder (m5stack_device/)
- device_ui.py: Manages the M5stack's local display including data presentation and user inputs.
- device_services.py: Handles sensor data processing and integration, manages local alerts specific to the device, and
communicates with shared services for weather updates.

## Streamlit Dashboard Folder (streamlit_dashboard/)
- dashboard_ui.py: Constructs and maintains the Streamlit dashboard for remote monitoring, focusing on historical and real-time
data visualization without handling alerts.
- dashboard_services.py: Focuses on fetching and processing data specifically for web-based visualization, without involvement in the alert processes.

## Service Folder (service/):
- app.py: where it all starts (Flask)
- bigquery_client.py: Centralized BigQuery operations to ensure both the device and the dashboard can perform data operations efficiently (push current conditions from device and pull weather from the API).
- weather_api_client.py: Shared service for fetching outdoor weather data, used by both the M5stack device and the Streamlit dashboard to get real-time and historical weather information.