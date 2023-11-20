# Electricity Carbon Calculator : Your Carbon Footprint from Your Electricity Consumption
#### Video Demo:  https://youtu.be/sn67N6IRzbI
#### Description:

This simple project has been done for the [OpenCourseWare CS50P : Introduction to Programming with Python](https://cs50.harvard.edu/python/2022/).
The objective of this Electricity Carbon Calculator is to estimate the amount of CO2 emitted from a personal residence based on the electricity consumption.
It provides this information for a maximum period of 7 days, either per hour (for periods less than 3 days) or per day (for periods less than 7 days).
To estimate the CO2 emissions this script use the API from [éCO2mix](https://www.rte-france.com/eco2mix/les-emissions-de-co2-par-kwh-produit-en-france). The data is aggregated at a national level (France), so depending on your location, the data may be an approximation. The data is aggregated at a national level (France), so depending on your location, the data may be an approximation.


#### **Requirements**:

To use this python script, you will need:

1. To reside in France.
2. To have a Linky meter.
3. Access to your [Enedis account](https://mon-compte-particulier.enedis.fr/home-connectee/).
4. To use this service to get your token and PDL (points de livraison) in order to pull the data from Enedis API : [MyElectricalData](https://myelectricaldata.fr/).
5. Add this token and PDL inside the `get_enedis_data` function as shown below.


#### **0 - Get date input:**

At the begining of the scrpit, the user is prompted to enter a start date and an end date in the format "YYYY-MM-DD" for a date range of electricity consumption and CO2 emissions data to retrieve. The start date is inclusive while the end date is exclusive, meaning that the consumption data will be retrieved up to the day before the end date.


#### **1 - Retrive data from the Enedis API:**

This function `get_enedis_data(start,end)` is used to retrieve the energy consumption data from the Enedis API within the specified date range by the user. It takes two parameters, "start" and "end", which represent the start and end dates of the desired data range. The maximum date range is 7 days because of the API limitations.

The function then makes an API call to retrieve a JSON file containing the consumption data, which is cleaned and written to a local JSON file named "enedis_data.json". The function requires a valid authorization token and a PDL number to access the Enedis API.

*You can change the token here :*

`#Import the token to get the consumption data
headers = {
'accept': 'application/json',
'Authorization': 'TOKENTOKENTOKENTOKENTOKENTOKENTOKENTOKENTOKEN',
}`

`#Get a JSON file containing the consumption data
r = requests.get(f'https://www.myelectricaldata.fr/consumption_load_curve/PDLPDLPDLPDLPDL/start/{start}/end/{end}',headers=headers,)`


#### **2 - First cleaning of the Enedis data:**

This function takes in a Pandas DataFrame as an argument. The DataFrame should contain interval readings of electricity consumption from the Enedis API. The function extracts the values (in watts) and the corresponding time for each reading and creates a new DataFrame with these values.

It then splits the date/time into separate columns for date and time, drops the original date/time column, and returns the resulting cleaned DataFrame. The cleaned DataFrame will be used for subsequent calculations and will be merged with CO2 emission data.


#### **3 - Get the CO2 emissions data:**

This code defines a function `get_co2_data(start,end)` that retrieves CO2 emission data from an API provided by [éCO2mix](https://odre.opendatasoft.com/explore/dataset/eco2mix-national-tr/information/). The function takes two arguments start and end which represent the start and end dates (in the format "YYYY-MM-DD") for the time period of the CO2 emission data to be retrieved.

The function converts the start and end dates to datetime objects, and then subtracts one day from each of them to account for the time zone difference. It then uses these modified dates to construct a URL to send a GET request to the API using the requests module. The response is a JSON file containing the CO2 emission data.

The function then cleans up the JSON data by replacing single quotes with double quotes and writes the cleaned data to a file called co2_data.json.

#### **4 - First cleaning of the emissions data:**

The `clean_co2_data(df)` function takes a DataFrame `df` and returns a cleaned DataFrame with CO2 emissions data.

The function selects two columns of the input DataFrame `df`, cleans the datetime format, splits it into date and time, and calculates average emissions for every 30-minute interval. This step aims to prepare the data for joining with the electricity consumption DataFrame.

It then adds a row to the DataFrame to ensure there is a full 24 hours of data, merges the two DataFrames, and cleans the final DataFrame. The function finally adjusts the last row to ensure it is correctly formatted and returns the final cleaned DataFrame.

#### **5 - Combine the emissions and the Enedis data:**

This function combines two dataframes, `df_enedis` and `df_co2`, and prepares them for further analysis.

First, the `value` column of `df_enedis` is converted to an integer type, and then converted to kilowatt hours (kWh) by dividing by 1000 and then by 2 to get the value for 30 minutes.

Next, a new `DateTime` column is created in `df_enedis` by combining the `Date` and `Time` columns and converting them to a `datetime` type using the `pd.to_datetime()` function.

Then, the two dataframes are merged on the `Date` and `Time` columns, using a left join to keep all rows from `df_enedis`.

Finally, a new `Emissions` column is added to the merged dataframe, which is the product of the `value` and `Taux_co2` columns. This gives an estimate of CO2 emissions in grams for each half-hour interval based on the electricity consumption during that time period and the average CO2 emissions rate during that same time period. The resulting merged and processed dataframe is returned.

#### **6 - Edit the final df prepare it to plot:**

This code defines a function `df_edit_to_plot()` that takes three inputs: `start`, `end`, and `dataframe_final`.

The function first converts the `start` and `end` inputs into datetime objects using `datetime.strptime()` function. It then calculates the difference between the two dates and assigns it to a global variable diff.

If the difference is less than or equal to three days, the function creates a new column in `dataframe_final` called `Emissions_bar`, which contains the same values as the `Emissions` column. Values in the `Emissions_bar` column that are less than 1 are replaced with an empty string to have a more readable plot. The values in `Emissions_bar` column are then rounded to 0 decimals also for visibility purpose and the updated `dataframe_final` is returned.

If the difference is between four and seven days, the function groups the data in `dataframe_final` by day and sums the `Emissions` column. The `DateTime` column is converted to datetime object using `pd.to_datetime()`, and the last row of the `DateTime column` is adjusted by subtracting one day and one second. The values in `Emissions` column are then rounded to 0 decimals and the updated `dataframe_final` is returned.

This function prepares the data in `dataframe_final` for plotting a graph in the following function.

#### **7 - Plot the data with Plotly:**

This code defines a function `plot_data` that creates a bar chart to visualize CO2 emissions for a given period. The function takes two dataframes as input, `df` and `df_dates`, which contain information about the CO2 emissions and the dates of the emissions, respectively.

The first step of the function is to extract the dataframes and calculate the total CO2 emissions for the given period. This information is showed in the title of the plot.

Then, depending on the duration of the period, the function creates either an hourly or daily bar chart.

For a period less than or equal to 3 days, the function creates an hourly bar chart using the Plotly library. The bar chart shows the CO2 emissions for each hour in the given period, and the color of each bar represents the emission value. Additionally, the function formats the x-axis to show the date and hour, and sets the tick angle and tick format for better readability.

For a period less than or equal to 7 days, the function creates a daily bar chart that shows the total CO2 emissions for each day in the given period.

Finally, the function updates the text format for the bar chart and displays the chart using the `show` method.

#### **Examples of Plotly outputs:**
##### For less than 3 days
\
![Alt text](3_days_graph.png?raw=true "Less than 3 days plot")

##### For less than 7 days
\
![Alt text](7_days_graph.png?raw=true "Less than 7 days plot")


