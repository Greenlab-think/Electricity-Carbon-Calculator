#To import API data from My Electrical Data/éCO2mix
import requests
#To navigate through the JDON file
import json
#To manipulate dates
from datetime import datetime, timedelta
import datetime as dt
#To manipulate dataframe and JSON
import pandas as pd
from pandas import json_normalize
#To create plot
import plotly.express as px
from matplotlib import pyplot as plt

def main():
    #Get date input from user
    date_start = input("Entrer une date de début au format AAAA-MM-JJ : ")
    date_end = input("Jour non inclus. Entrer une date de fin au format AAAA-MM-JJ : ")

    #Verify dates
    global dates
    dates = get_dates(date_start,date_end)

    #Get JSON file with Enedis data
    get_enedis_data(date_start,date_end)

    #Clean data
    get_co2_data(date_start,date_end)

    #Get enedis df
    df_enedis_0 = pd.read_json("enedis_data.json", orient="index")

    #Clean enedis df
    df_enedis = clean_enedis_data(df_enedis_0)

    #Get co2 df
    with open("co2_data.json") as f:
        data = json.load(f)
    df_co2_0 = json_normalize(data, record_path=["records"])

    #Clean co2 df
    df_co2 = clean_co2_data(df_co2_0)

    #Combine data
    dataframe_final = combine_dataframes(df_enedis,df_co2)

    #Get the final dataframe ready to plot
    df_ready_plot = df_edit_to_plot(date_start,date_end,dataframe_final)

    #Plot data
    plot_data(df_ready_plot,df_ready_plot)


def get_dates(start,end):
    #Validate the dates format and check the maximum of 7 days between the two dates
    try:
        dt.date.fromisoformat(start)
        dt.date.fromisoformat(end)
        dates_start_check = datetime.strptime(start, "%Y-%m-%d")
        dates_end_check = datetime.strptime(end, "%Y-%m-%d")
        diff = dates_end_check - dates_start_check
        if diff > timedelta(days=7):
            raise ArithmeticError("L'écart maximum entre les deux dates doit être de 7 jours maximum.")
    except ValueError:
        raise ValueError("Format de la date incorrect, elle devrait être au format AAAA-MM-JJ.")

    return [start, end]


def get_enedis_data(start,end):
    #Import the token to get the consumption data
    headers = {
    'accept': 'application/json',
    'Authorization': '8CeDbwrStg9bEAs9CVpq0CHc_C71axGZjfLPp14HBIw=',
    }

    #Get a JSON file containing the consumption data
    r = requests.get(f'https://www.myelectricaldata.fr/consumption_load_curve/24336324046198/start/{start}/end/{end}',headers=headers,)

    #Clean the JSON file
    jsonResponse = r.json()
    jsonResponse = str(jsonResponse).replace("'", '"')

    #Write to JSON file
    writeFile = open("enedis_data.json", "w")
    writeFile.write(jsonResponse)
    writeFile.close()


def clean_enedis_data(df):
    #Get the dataframe with value (W) and the hour of consumption
    df1 = pd.DataFrame(df.loc["meter_reading"]["interval_reading"])
    df1 = df1.drop(columns=["interval_length", "measure_type"])

    #Split date/time
    df1["date"] = pd.to_datetime(df1["date"])
    df1["Date"] = df1["date"].dt.date
    df1["Time"] = df1["date"].dt.time
    df1 = df1.drop(columns=["date"])

    return df1

def get_co2_data(start,end):
    #New dates to get the correct day because of the time zone
    dates_start = datetime.strptime(start, "%Y-%m-%d")
    dates_start = dates_start - timedelta(days=1)
    dates_start = dates_start.date()

    dates_end = datetime.strptime(end, "%Y-%m-%d")
    dates_end = dates_end - timedelta(days=1)
    dates_end = dates_end.date()

    #Get a JSON file containing the co2 data
    r = requests.get(f"https://odre.opendatasoft.com/api/records/1.0/search/?dataset=eco2mix-national-tr&q=date_heure%3A%5B{dates_start}T23%3A00%3A00Z+TO+{dates_end}T22%3A59%3A59Z%5D&lang=fr&rows=10000&sort=-date_heure&facet=nature&facet=date_heure")

    #Clean the JSON file
    jsonResponse = r.json()
    jsonResponse = str(jsonResponse).replace("'", '"')

    #Write to JSON file
    writeFile = open("co2_data.json", "w")
    writeFile.write(str(jsonResponse))
    writeFile.close()

def clean_co2_data(df):
    #Get the dataframe with CO2 emissions and the hour
    df1 = df[["fields.date_heure", "fields.taux_co2"]]
    df1 = df1.copy()

    #Clean, correct time zone to France and split date and time
    df1["Date_time"] = pd.to_datetime(df1["fields.date_heure"])
    df1["Date_time"] = df1["Date_time"].dt.tz_localize(None)
    df1["Date_time"] = df1["Date_time"] + pd.Timedelta(hours=1)
    df1["Date"] = df1["Date_time"].dt.date
    df1["Time"] = df1["Date_time"].dt.time

    #Prepare data to join the My Electrical Data/éCO2mix on Date/Time
    #Get dataframe without first row
    df2 = df1.drop([0]).reset_index(drop=True)

    #Get everage of every two rows to have every 30 mins of average emissions
    idx = len(df2) - 1 if len(df2) % 2 else len(df2)
    df3 = df2[:idx].groupby(df2.index[:idx] // 2).mean()

    df3 = df3.rename(columns={"fields.taux_co2": "Taux_co2"})

    #Get dataframe with every 30 mins
    df4 = df1.iloc[::2]
    df4 = df4.drop([0]).reset_index(drop=True)

    #Add one row to get full 24h with approximation for 23h30 to midnight
    last_row = df2.tail(1)
    last_row = last_row.rename(columns={"fields.taux_co2": "Taux_co2_2"})
    df4 = df4.append(last_row, ignore_index = True)

    #Merge and clean last data frame
    df5 = pd.concat([df3, df4], axis=1)
    df5 = df5[["Taux_co2","Taux_co2_2","Date","Time"]]

    #Clean for last row
    df5["Taux_co2"] = df5["Taux_co2"].fillna(0) + df5["Taux_co2_2"].fillna(0)
    df5 = df5[["Taux_co2","Date","Time"]]

    #Adjust date/time for last row
    df5["Date"].iloc[-1] = df5["Date"].iloc[-1] + timedelta(days=1)
    delta = dt.timedelta(minutes = 15)
    df5["Time"].iloc[-1] = (dt.datetime.combine(dt.date(1,1,1),df5["Time"].iloc[-1]) + delta).time()

    return df5

def combine_dataframes(df_enedis,df_co2):
    #Get corrects types
    df_enedis["value"] = df_enedis["value"].astype(int)

    #Transform to Kwh
    df_enedis["value"] = df_enedis["value"].div(1000)
    df_enedis["value"] = df_enedis["value"].div(2)

    #Get a DateTime column
    DateTime_column = pd.to_datetime(df_enedis.Date.astype(str) + " " + df_enedis.Time.astype(str))
    df_enedis.insert(3, "DateTime", DateTime_column)

    #Merge
    new_df = df_enedis.merge(df_co2, left_on=["Date","Time"], right_on = ["Date","Time"], how='left')

    #Get emissions
    new_df["Emissions"] = new_df["value"]*new_df["Taux_co2"]

    return new_df

def df_edit_to_plot(start,end,dataframe_final):
    #Conditionnal graph creation by input dates
    dstart = datetime.strptime(start, "%Y-%m-%d")
    dend = datetime.strptime(end, "%Y-%m-%d")
    global diff
    diff = dend - dstart

    #Add a column to show values only > 1 in bar plot if days less than 3
    if diff <= timedelta(days=3):
        dataframe_final["Emissions_bar"] = dataframe_final["Emissions"]
        dataframe_final.loc[dataframe_final["Emissions_bar"] < 1, "Emissions_bar"] = ""
        #Round values to 0 decimals
        dataframe_final["Emissions_bar"] = pd.to_numeric(dataframe_final["Emissions_bar"])
        dataframe_final["Emissions_bar"] = dataframe_final["Emissions_bar"].round(decimals = 0)
        return dataframe_final

    #Get emissions per day if days less than 7
    if diff <= timedelta(days=7):
        #Clean last day to correctly sum
        dataframe_final["DateTime"] = pd.to_datetime(dataframe_final["DateTime"])
        dataframe_final.iloc[-1, dataframe_final.columns.get_loc("DateTime")] -= timedelta(days=1,seconds=1)
        #Get sum group by day
        dataframe_final = dataframe_final.groupby([dataframe_final["DateTime"].dt.date]).agg("sum").reset_index()
        #Round values of emissions to 0 decimals
        dataframe_final["Emissions"] = pd.to_numeric(dataframe_final["Emissions"])
        dataframe_final["Emissions"] = dataframe_final["Emissions"].round(decimals = 0)
        #Clean last day for plot
        return dataframe_final


def plot_data(df,df_dates):
    #Get last dataframes
    df_plot = df
    dataframe_final = df_dates

    #Get total of emissions for the period
    total = round(df_plot["Emissions"].sum())

    #if days <3 then create a hourly bar chart
    if diff <= timedelta(days=3):
        #Plot a bar chart
        plot = px.bar(df_plot, x = "DateTime",y = "Emissions",
                      color="Emissions",
                      text="Emissions_bar",
                      title=f"Émissions de CO2 eq par heure du {dataframe_final.iloc[1, dataframe_final.columns.get_loc('Date')]} au {dataframe_final.iloc[-2, dataframe_final.columns.get_loc('Date')]}. Total des émissions sur la période : {total}g",
                      labels={
                        "DateTime": "Jour et heure",
                        "Emissions": "Émissions de CO2 eq/kWh en g"},
                      hover_data={"Emissions": ":.2f"}
                      )
        #Formatage de l'axe x
        plot.update_xaxes(tickangle=-45)
        plot.update_layout(xaxis={
                             "tickformat": "%d-%m %Hh%M",
                             "tick0": df_plot["DateTime"].iloc[0],
                             "dtick": 86400000.0/24}
                           )

    #if days <7 then create a daily bar chart
    elif diff <= timedelta(days=7):
        #Plot a bar chart
        plot = px.bar(df_plot, x = "DateTime",y = "Emissions",
                      color="Emissions",
                      text="Emissions",
                      title=f"Émissions de CO2 eq par heure du {dataframe_final.iloc[0, dataframe_final.columns.get_loc('DateTime')]} au {dataframe_final.iloc[-1, dataframe_final.columns.get_loc('DateTime')]}. Total des émissions sur la période : {total}g",
                      labels={
                        "DateTime": "Jour et heure",
                        "Emissions": "Émissions de CO2 eq/kWh en g"},
                      hover_data={"Emissions": ":.2f"}
                      )

    #Change bar text format
    plot.update_layout(uniformtext_minsize=8, uniformtext_mode="show")

    #Show plot
    plot.show()

if __name__ == "__main__":
    main()