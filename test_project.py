from project import *
import pytest
#To test API imports
import unittest.mock
#To test dataframes
import json
import pandas as pd
from pandas import json_normalize
#To test dates
from datetime import datetime, timedelta
import datetime as dt


def test_get_dates():
    #Check with right dates
    assert get_dates("2023-01-15", "2023-01-17") == ['2023-01-15', '2023-01-17']

    #Check with wrong dates : Bad formatting
    with pytest.raises(ValueError, match="Format de la date incorrect, elle devrait être au format AAAA-MM-JJ."):
        get_dates("2023-01-15", "2023-01-")

    #Check with wrong dates : more than 7 days
    with pytest.raises(ArithmeticError, match="L'écart maximum entre les deux dates doit être de 7 jours maximum."):
        get_dates("2023-01-15", "2023-01-30")

def test_get_enedis_data():
    with unittest.mock.patch("requests.get") as mock_get:
        #Define the response of the mocked request
        mock_response = unittest.mock.MagicMock(json=lambda: {"test_key": "test_value"})
        mock_get.return_value = mock_response

        #Call the function that performs the request
        get_enedis_data("2022-01-01", "2022-01-07")

        #Check that the request is performed with the right URL
        mock_get.assert_called_with("https://www.myelectricaldata.fr/consumption_load_curve/24336324046198/start/2022-01-01/end/2022-01-07", headers={"accept": "application/json", "Authorization": "8CeDbwrStg9bEAs9CVpq0CHc_C71axGZjfLPp14HBIw="})

        #Check if the response was written to the file
        with open("enedis_data.json", "r") as f:
            content = f.read()
            assert content == '{"test_key": "test_value"}'

#Get a test dataframe to run the test for clean_enedis_data
@pytest.fixture
def setup_df_enedis():
    #Load test JSON to a df variable
    df_test = pd.read_json('{"meter_reading": {"usage_point_id": "24336324046198", "start": "2023-01-15", "end": "2023-01-16", "quality": "BRUT", "reading_type": {"measurement_kind": "power", "unit": "W", "aggregate": "average"}, "interval_reading": [{"value": "552", "date": "2023-01-15 00:30:00", "interval_length": "PT30M", "measure_type": "B"}]}}', orient="index")
    return df_test

def test_clean_enedis_data(setup_df_enedis):
    #Get the df to test
    resut_df_test_1 = clean_enedis_data(setup_df_enedis)

    # Assert that the resulting dataframe has the correct number of rows
    assert len(resut_df_test_1) == len(setup_df_enedis)

    #Assert that the resulting dataframe has the correct columns
    assert set(resut_df_test_1.columns) == {"Date", "Time", "value"}

    #Assert that the dates have been converted to the correct format
    assert resut_df_test_1["Date"][0] == datetime.strptime("2023-01-15", '%Y-%m-%d').date()

    #Assert that the time have been converted to the correct format
    assert resut_df_test_1["Time"][0] == datetime.strptime("00:30:00", '%H:%M:%S').time()

    #Assert that the values have been preserved
    assert resut_df_test_1["value"][0] == "552"


def test_get_co2_data():
    with unittest.mock.patch("requests.get") as mock_get:
        #Define the response of the mocked request
        mock_response = unittest.mock.MagicMock(json=lambda: {"test_key": "test_value"})
        mock_get.return_value = mock_response

        #Call the function that performs the request
        get_co2_data("2022-01-02", "2022-01-08")

        #Check that the request is performed with the right URL
        mock_get.assert_called_with("https://odre.opendatasoft.com/api/records/1.0/search/?dataset=eco2mix-national-tr&q=date_heure%3A%5B2022-01-01T23%3A00%3A00Z+TO+2022-01-07T22%3A59%3A59Z%5D&lang=fr&rows=10000&sort=-date_heure&facet=nature&facet=date_heure")

        #Check if the response was written to the file
        with open("enedis_data.json", "r") as f:
            content = f.read()
            assert content == '{"test_key": "test_value"}'

#Get a test dataframe to run the test for test_clean_co2_data
@pytest.fixture
def setup_df_co2():
    #Load test content to a df variable
    data = {
        "fields.date_heure": [
            "2022-01-01 00:00:00",
            "2022-01-01 00:30:00",
            "2022-01-01 01:00:00",
            "2022-01-01 01:30:00",
            "2022-01-01 02:00:00",
        ],
        "fields.taux_co2": [100, 110, 120, 130, 140],
    }
    df_test_2 = pd.DataFrame(data)
    return df_test_2

def test_clean_co2_data(setup_df_co2):
    #Get the df to test
    resut_df_test_2 = clean_co2_data(setup_df_co2)

    #Assert that the resulting dataframe has the correct columns
    assert set(resut_df_test_2.columns) == {"Taux_co2", "Date", "Time"}

    #Assert that the dates have been converted to the correct format
    assert resut_df_test_2["Date"][0] == datetime.strptime("2022-01-01", '%Y-%m-%d').date()

    #Assert that the time have been converted to the correct format
    assert resut_df_test_2["Time"][0] == datetime.strptime("02:00:00", '%H:%M:%S').time()

    #Assert that the values have been calculated
    assert resut_df_test_2["Taux_co2"][0] == 115.0

#Get a test dataframe to run the test for test_combine_dataframes
@pytest.fixture
def setup_df_merge():
    df_enedis = pd.DataFrame({
        'value': [552, 50, 24, 54, 300],
        'Date': ['2023-01-15'] * 5,
        'Time': ['00:30:00', '01:00:00', '01:30:00', '02:00:00', '02:30:00']
    })

    df_co2 = pd.DataFrame({
        'Date': ['2023-01-15'] * 5,
        'Time': ['00:30:00', '01:00:00', '01:30:00', '02:00:00', '02:30:00'],
        'Taux_co2': [30.5, 32.0, 32.5, 32.5, 32.5]
    })

    return df_enedis,df_co2

def test_combine_dataframes(setup_df_merge):
    #Get the df to test
    resut_df_test_3 = combine_dataframes(setup_df_merge[0],setup_df_merge[1])

    #Check the result has the expected shape
    assert resut_df_test_3.shape == (5, 6)

    #Assert that the values have been calculated and correct
    assert resut_df_test_3["Taux_co2"][0] == 30.5
    assert resut_df_test_3["value"][0] == 0.276
    assert resut_df_test_3["Emissions"][0] == 8.418000000000001

    #Assert that the dates have been converted to the correct format
    assert resut_df_test_3["DateTime"][0] == datetime.strptime("2023-01-15 00:30:00", '%Y-%m-%d %H:%M:%S').date()

#Get a test dataframe to run the test for test_df_edit_to_plot
@pytest.fixture
def setup_df_final():
    df_final = pd.DataFrame({
        "value": [0.276, 0.025, 0.012, 0.027, 0.150],
        "Date": ["2023-01-15", "2023-01-15", "2023-01-15", "2023-01-15", "2023-01-15"],
        "Time": ["00:30:00", "01:00:00", "01:30:00", "02:00:00", "02:30:00"],
        "DateTime": ["2023-01-15 00:30:00", "2023-01-15 01:00:00", "2023-01-15 01:30:00", "2023-01-15 02:00:00", "2023-01-15 02:30:00"],
        "Taux_co2": [30.5, 32.0, 32.5, 32.5, 32.5],
        "Emissions": [8.4180, 0.8000, 0.3900, 0.8775, 4.8750]
    })

    add_col = pd.DataFrame({
        "value": [0.150],
        "Date": ["2023-01-22"],
        "Time": ["00:30:00"],
        "DateTime": ["2023-01-22 00:30:00"],
        "Taux_co2": [32.5],
        "Emissions": [4.8750]
    })

    df_final_7 = pd.concat([df_final, add_col])

    return df_final, df_final_7

def test_df_edit_to_plot(setup_df_final):
    #Dates for the test
    start = "2023-01-15"
    end = "2023-01-15"

    #Test case 1: difference in days between start and end dates is less than or equal to 3
    #Get the test df
    resut_df_test_4 = setup_df_final[0]

    #Get df to do the asserts
    result = df_edit_to_plot(start, end, resut_df_test_4)

    #Assert for the columns
    assert set(result.columns) == {"value", "Date", "Time", "DateTime", "Taux_co2", "Emissions", "Emissions_bar"}

    #Assert for the new column "Emissions_bar", check if there is the NaN value
    assert result["Emissions_bar"].isnull().values.any()

    # Test case 2: difference in days between start and end dates is less than or equal to 7
    #Get the test df
    resut_df_test_5 = setup_df_final[1]
    end = "2023-01-22"

    #Get df to do the asserts
    result2 = df_edit_to_plot(start, end, resut_df_test_5)
    print(result2)

    #Assert for the columns
    assert set(result2.columns) == {"DateTime", "value", "Taux_co2", "Emissions"}

    #Assert for the new column "Emissions_bar", check if there is the NaN value
    assert result2["Emissions"].round(decimals=0).tolist() == [15.0, 5.0]

    #Assert if the df size is correct
    assert result2.shape == (2, 4)

#Get a test dataframe to run the test for test_plot_data
@pytest.fixture
def setup_df_plot():
    #Create a test dataframe
    df = pd.DataFrame({
        "DateTime": ["2023-01-15", "2023-01-16", "2023-01-17", "2023-01-18", "2023-01-19", "2023-01-20", "2023-01-21"],
        "value": [11.404, 8.709, 9.360, 9.905, 12.761, 20.169, 29.023],
        "Taux_co2": [1384.0, 1832.5, 2778.0, 2594.0, 2882.5, 3386.0, 3320.5],
        "Emissions": [316.0, 355.0, 534.0, 535.0, 789.0, 1383.0, 1983.0]
    })
    return df

def test_plot_data(setup_df_plot,setup_df_final):
    #Call the function and check that it runs without error
    try:
        plot_data(setup_df_plot,setup_df_final[1])
    except Exception as e:
        pytest.fail(f"plot_data raised an exception: {e}")