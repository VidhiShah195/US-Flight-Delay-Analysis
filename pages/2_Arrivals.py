import streamlit as st
import pandas as pd
import plotly.express as px
import base64
import plotly.graph_objects as go

st.set_page_config(
    page_title="Arrival Analysis",
    page_icon='✈️'
    )

# reading the gif file as binary data and then encoding it as a base64, and storing the result as a string.
with open("data/landing.gif", "rb") as f:
    gif_data = f.read()
gif = base64.b64encode(gif_data).decode()

# creating a centrerd layout with the gif and tile being in the same line and there being 10 pixels of space between the gif and title.
st.markdown(
    f"""
    <div style="display: flex; justify-content: center; align-items: center;">
        <img src="data:image/gif;base64,{gif}" alt="gif" width="100">
        <h1 style="margin-left: 10px;"> Arrival Analysis</h1>
    </div>
    """,
    unsafe_allow_html=True
)
# making a gray horizontal line under my title (used just for fun).
st.markdown("<hr style='border: 1px solid #f0f0f0;'>", unsafe_allow_html=True)

st.write("On this page, you will gain more insights into arrival patterns and airline performance at various airports. Explore the busiest arrival times, track flight status distributions, and delve into the average delay times caused by different delay types.")

# added cache to ensure that the data doesn't have to be reloaded everytime the file runs.
@st.cache_data
def load_data(csv):
    return pd.read_csv(csv)

# reading the csv.
flights_data = load_data("data/flights_sample_3m.csv")


st.header("Filter Flight Data by Airlines and Arrival Airport")
# CREATING THE SELECT BOXES ONE FOR AIRPORT AND THEN ANOTHER WHICH FILTERS BASED ON THAT 
selected_airport_arr = st.selectbox('Select Arrival Airport', sorted(flights_data['DEST'].unique()))
filtered_airlines = flights_data[flights_data['DEST'] == selected_airport_arr]['AIRLINE'].unique()
selected_airline_arr = st.selectbox('Select Airline', sorted(filtered_airlines))
st.markdown("<b>*Note: </b> This selection will be used to filter all the charts below.",unsafe_allow_html=True)



# BUSIEST ARRIVAL TIMES
st.subheader(f'Busiest Arrival Times at {selected_airport_arr} with {selected_airline_arr}')

# converting arrival time to datetime format and then extracting hour from arrival time.
flights_data['CRS_ARR_TIME'] = pd.to_datetime(flights_data['CRS_ARR_TIME'], format='%H%M', errors='coerce')
flights_data['ArrHour'] = flights_data['CRS_ARR_TIME'].dt.hour

# filtering data based on user's selected airport and airline.
filtered_data_arr = flights_data[(flights_data['DEST'] == selected_airport_arr) & (flights_data['AIRLINE'] == selected_airline_arr)]

# counting occurrences of each arrival hour.
arrival_counts = filtered_data_arr['ArrHour'].value_counts().sort_index()

# setting the hours and initializing departure counts for all hours.
hours = [(f'{h % 12 if h % 12 != 0 else 12} {"AM" if h < 12 else "PM"}') for h in range(24)]
count_all_hours = {hour: 0 for hour in range(24)}

# counting occurrences of each arrival hour.
for hour, count in arrival_counts.items():
    count_all_hours[hour] = count

# plotting, formatting x-axis to display in AM/PM and adding a tooltip.
fig1 = px.bar(x=hours, y=[count_all_hours[hour] for hour in range(24)],
              labels={'x': 'Arrival Hour', 'y': 'Number of Flights'},
              title=f'Busiest Arrival Times at {selected_airport_arr} with {selected_airline_arr}')
fig1.update_xaxes(tickmode='array')
fig1.update_traces(hovertemplate='<b>Arrival Hour:</b> %{x}<br><b>Number of Flights:</b> %{y}<extra></extra>', marker_color='#048092')
st.plotly_chart(fig1)



# FLIGTH STATUS AND DELAYS TYPE DISTRIBUTION DUNUT CHART
st.subheader("Flight Status Distribution")

# calculating flight count for cancelled, delayed and or diverted flights.
flight_status_counts = {"Cancelled": filtered_data_arr['CANCELLED'].sum(),
    "Delayed": filtered_data_arr[filtered_data_arr['ARR_DELAY'] > 0].shape[0],
    "On time": filtered_data_arr[(filtered_data_arr['CANCELLED'] == 0) & (filtered_data_arr['ARR_DELAY'] <= 0)].shape[0]
}

# setting color based on the flight status.
colors = {'Delayed': '#83C9FF', 'Cancelled': '#FF2B2B', 'On time': '#0068C9'}

st.write(f"The donut chart below shows the the percent of flights landing at {selected_airport_arr} airport on {selected_airline_arr} that were on time, or experienced delays and/or cancellations.")
    
# making the donut chart with flight overall status and adding a tooltip.
fig3 = go.Figure()
fig3.add_trace(go.Pie(
    labels=list(flight_status_counts.keys()),
    values=list(flight_status_counts.values()),
    textinfo='label+percent', 
    hole=0.5,
    hovertemplate='<b>Flight Status:</b> %{label}<br>' + '<b>Value:</b> %{value}<br>' + '<b>Percent of Total:</b> %{percent}',
    marker=dict(colors= [colors[key] for key in flight_status_counts.keys()])))
fig3.update_layout(
    title_text="Flight Status Distribution")
st.plotly_chart(fig3, use_container_width=True, center=True)



# setting it so that if no flights were delayed, it prints my defined staement and if they were, then the second donut chart is printed.
if flight_status_counts["Delayed"] == 0:
    st.write("*No flights were delayed thus further analysis on delay distribution is not applicable.*")

else:
    # renaming my columns so that I can use it later to make sure its easy for my users. 
    filtered_data_arr.rename(columns={'DELAY_DUE_CARRIER': 'Carrier Delay','DELAY_DUE_WEATHER': 'Weather Delay',
                              'DELAY_DUE_NAS': 'NAS Delay','DELAY_DUE_SECURITY': 'Security Delay',
                              'DELAY_DUE_LATE_AIRCRAFT': 'Late Aircraft Delay'}, inplace=True)

    st.subheader("Average Dalay caused by Each Delay Type")
    st.write(f"The donut chart below shows the the percent of flights landing at {selected_airport_arr} airport on {selected_airline_arr} that experienced delays due to specific delay types. Hover over the chart to view the average delay time (in minutes) caused by each delay type.")
    
    fig4 = go.Figure()

    # filtering and then counting the data which includes only rows where arrival delay is positive since if its negaitve it suggets that it was early/ on time.
    pos_delay = filtered_data_arr[filtered_data_arr['ARR_DELAY'] > 0]
    delay_counts = pos_delay[['Carrier Delay', 'Weather Delay', 'NAS Delay', 'Security Delay', 'Late Aircraft Delay']].apply(lambda x: (x > 0).sum())

    # calculating average delay times for each delay category just to add that to my tooltip. 
    avg_delay_times = pos_delay[['Carrier Delay', 'Weather Delay', 'NAS Delay', 'Security Delay', 'Late Aircraft Delay']].mean()

    # setting color based on the delay type.
    colors = {'Carrier Delay': '#FF2B2B', 'Weather Delay': '#7DEFA1', 'NAS Delay': '#29B09D','Security Delay':'#483C32', 'Late Aircraft Delay':'#FF8700'}

    # making the donut chart with delay types and adding a tooltip.
    fig4.add_trace(go.Pie(
        labels=delay_counts.index,
        values=delay_counts.values,
        textinfo='label+percent', 
        hole=0.5,
        hovertemplate='<b>Cause of Delay:</b> %{label}<br>' + '<b>Average Delay Time:</b> ' + avg_delay_times.round(2).astype(str) + ' minutes <br>' + '<b>Percent of Total:</b> %{percent}',        
        marker=dict(colors= [colors[key] for key in delay_counts.keys()])))
    fig4.update_layout(
        title_text="Average Delay Times by Delay Type")
    st.plotly_chart(fig4, use_container_width=True, center=True) 