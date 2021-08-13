import pydata_google_auth
import pandas as pd
import holoviews as hv

from query import get_query

def get_data():
    # Get user credentials for BQ
    credentials = pydata_google_auth.get_user_credentials(
    ['https://www.googleapis.com/auth/bigquery'],)

    # Get the query from query.py
    QUERY = get_query()

    # Read query and write to dataframe
    df = pd.read_gbq(QUERY, project_id='einride-dataform', dialect='standard', credentials=credentials)

    # Convert from lon/lat to web-mercator easting/northing coordinates
    df["easting"], df["northing"] = hv.Tiles.lon_lat_to_easting_northing(
        df["lon"], df["lat"]
    )

    # Return dataframe
    return df