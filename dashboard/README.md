# Career Market Intelligence - Dashboard Guide

This project includes an interactive Streamlit dashboard that predicts the expected salary band for a given job posting based on its characteristics (role, location, seniority, and required skills).

## Prerequisites
Ensure that all dependencies are installed, including Streamlit:
```bash
pip install -r requirements.txt
```

*(Note: If you are using a virtual environment like `venv`, ensure it is activated first).*

## Running the Dashboard
To start the dashboard locally, simply run the following command from the root of the project:

```bash
streamlit run dashboard/app.py
```

If you are using the virtual environment directly, you can run:
```bash
venv/bin/streamlit run dashboard/app.py
```

## Accessing the Dashboard
Once the command is executed, Streamlit will start a local server and provide you with a URL in the terminal (usually `http://localhost:8501`). Open this link in any web browser to view and interact with the predictor!

## Features
- **Job Selection**: Choose from top Data and Software roles.
- **Location Filter**: Select prominent tech hubs.
- **Skill Selection**: Select from high-demand technical skills to see how they impact predicted salary bands.
- **Confidence Matrix**: View not just the predicted band, but the underlying probability for all classes (e.g. what percentage chance the model assigns to High vs Medium vs Low salary bands).
