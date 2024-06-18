"""
Date Finalized: 5/14/2024
Author: Ojasvi Mukkoti

Script is a dashboard that is for the Dual USB ATP Reports.
    Need to first run the "ConvertFormat.py" file, then this file with: "streamlit run {name of file}.py"

Dashboard Contains:
1. Dual USB ATP Pass/Fail Chart
2. First Pass Yield bar chart
3. Top 10 Fail reasons bar chart
4. First Pass Yield analysis for certain date ranges
5. Pall/Fail Count analysis for certain date ranges
6. Top 10 Fial reasons analysis for certain date ranges
"""

import streamlit as st
import plotly.express as px
import plotly.io as pio
import plotly.graph_objs as go
from io import BytesIO
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

st.set_page_config(layout='wide',
                   initial_sidebar_state="expanded")
@st.cache_data
def load_data(filename, selected_year):
    """
    Function that loads data from a directory that holds all the consice ATP Reports for each year.

    Parameters:
        filename: (String) Name of the file
        selected_year: (String) Selected year

    Returns:
        Dataframe: The Loaded Dataframe.
    """
    #listing needed path to get to files
    # UNC_path = r'\\empowering.apcd.local\public'
    # folder_name = "PANASONIC DUAL USB"
    # subfolder_name = "DUAL USB Sheets DASHBOARD"

    # #setting up file path
    # full_file_path = os.path.join(UNC_path, folder_name, subfolder_name, filename)
    try:
        #load data based on file extension
        if filename.endswith(".csv"):
            try:
                data = pd.read_csv(filename)
            except PermissionError as e:
                st.write("Permission denied error occurred while reading CSV file:", e)
                raise
        elif filename.endswith(".xlsm"):
            try:
                xls = pd.ExcelFile(filename)
                data = pd.read_excel(xls, 'RITA')
            except PermissionError as e:
                st.write("Permission denied error occurred while reading Excel file:", e)
                raise
            expected_columns = {
                'TEST \nDATE': 'TEST DATE',
            }
            #renanming columns
            data.rename(columns=expected_columns, inplace=True)
            # Converting the whole 'TEST DATE' column to be an object
            data['TEST DATE'] = data['TEST DATE'].astype('object')
            data['TEST RESULT (PASS/FAIL)'].replace({'PASS':'PASSED', 'FAIL':'FAILED'}, inplace=True)
    #establishing an error message
    except FileNotFoundError as e:
        st.warning(f"File for the year {selected_year} does not exist.")
        return None
    return data

@st.cache_data
# looking for only the needed data and storing in Dataframe
def filter_data(data, year_option):
    """
    Function that filters the data

    Parameters:
        data (Dataframe): Dataframe of the ATP data
        year_option (String): Slected year option

    Returns:
        Dataframe: filtered dataframe
    """
    #ignoring all the Comments that have "SHIPPED"
    combined_data = data[data['TEST DATE'].astype(str).str.contains(year_option, na=False) & ~data['COMMENTS'].astype(str).str.contains('SHIPPED', na=False)]
    return combined_data


@st.cache_data
#function that gets all the data that failed
def fail_data(c_d):
    """
    Function that gets the failed data

    Parameteres:
        c_d (Dataframe): the combinded dataframe that contains data that have specfic requirements
    Returns:
        Dataframe: All the failed dataframe
    """
    fail_data = c_d[c_d['TEST RESULT (PASS/FAIL)']=='FAILED']
    #ordering failed data based on their reason counts
    fail_ordered=fail_data["COMMENTS"].value_counts().sort_values(ascending=False)
    #getting the top 10 fails
    fail_10 = fail_ordered.head(10)
    return fail_10

@st.cache_data
# Function that will find and display the number of failed reasons
def fail_display_counts(combinded_data):
    """
    Function that will find and display the number of failed reasons

    Parameters:
        combinded_data (Dataframe): Combinded DataFrame
    Returns:
        None
    """
    #getting the failed data
    fail_data = combinded_data[combinded_data['TEST RESULT (PASS/FAIL)']=='FAILED']
    #counting the different Comments in dataframe column
    failed_reasons_count = fail_data['COMMENTS'].value_counts()
    st.write(failed_reasons_count) #writing the counts dataframe out

@st.cache_data
def display_failed_data_percentages(combinded_data):
    """
    Function that displays the Failed Reasons, their counts, and percentages.

    Paramteres: 
        combinded_data (Dataframe): Combinded Dataframe of specfic comments or requirements for dashboard

    Returns:
        Dataframe: DF w/ counts and percentages
    """
    #get failed data
    fail_data = combinded_data[combinded_data['TEST RESULT (PASS/FAIL)']=='FAILED']
    # Get the counts of failed reasons
    failed_reasons_count = fail_data['COMMENTS'].value_counts()

    # Calculate the total count of failed data
    total_failed_count = len(fail_data)

    # Create a DataFrame with counts and percentages
    results_df = pd.DataFrame({
        'Failed Reason': failed_reasons_count.index,
        'Count': failed_reasons_count.values,
        'Percentage (%)': (failed_reasons_count / total_failed_count) * 100
    })

    # Display the table in Streamlit
    st.subheader("Failed Reason Counts and Percentages")

    # Return the DataFrame with counts for other potential use
    return results_df

@st.cache_data
def FirstPassYield_GRAPH(range_date_list, range_names):
    """
    Function that creates a First Pass Yield graph for certain date ranges. 

    Parameters:
        range_date_list (List): List of data for each date range
        range_names (List): List of names for each date range
    Returns:
        Plotly Figure: First Pass Yield graph.
    """
    fig_FPY = go.Figure() #creating a new empty figure
    colors = ['firebrick', 'darkcyan']
    #iterating through range_date_list
    for i, range_data in enumerate(range_date_list):
        # Getting first pass yield data
        first_testNum = range_data[range_data['Test Number'] == 1]
        #counting the test results for pass/fail
        first_passed_count = (first_testNum['TEST RESULT (PASS/FAIL)'] == 'PASSED').sum()
        first_failed_count = (first_testNum['TEST RESULT (PASS/FAIL)'] == 'FAILED').sum()
        #calculating the First Pass Yield percentages
        total_items = len(first_testNum)
        FPY = ((total_items - first_failed_count) / total_items) * 100
        #creating a dataframe that holds the Test results and their respective counts
        bar_data = pd.DataFrame({'Test Result': ['PASS', 'FAIL'], 'Count': [first_passed_count, first_failed_count]})
        #plotting bar chart on the same figure for each date range
        fig_FPY.add_trace(go.Bar(x=bar_data['Test Result'], y=bar_data['Count'], 
                                  name=range_names[i],
                                  text=bar_data['Count'],
                                  marker_color=colors[i]))
        st.write(f'First Pass Yield of {range_names[i]}: {FPY:.2f}%')
    # Customize the layout
    fig_FPY.update_layout(title=f'Dual USD First Pass Yield {selected_year}',
                          xaxis_title='Test Result', yaxis_title='Count',
                          barmode='group')
    return fig_FPY
#STREAMLIT CODE STARTS HERE
selected_year = st.selectbox("Select a Year", ('2020','2022','2023'), key='selectbox')
st.write(f'You selected year: {selected_year}')
#checking if selected year is current use is different than current slected year
if st.session_state.selectbox != selected_year:
    st.experimental_rerun()
#gettinf filename based on selected year
filename = f"Example Data {selected_year}.csv"


#getting the needed data
data  = load_data(filename, selected_year)
if data is not None:
    #filtering out 'data'
    combined_data = filter_data(data, selected_year)

    #creating the Renaming Code here
    #PASS/FAIL counts rename
    combined_data['TEST RESULT (PASS/FAIL)'].replace({'fAILED': 'FAILED'}, inplace=True)

    #FAIL comments rename
    # Select rows where the 'TEST RESULT (PASS/FAIL)' column is equal to 'FAIL'
    fail_comments = combined_data[combined_data['TEST RESULT (PASS/FAIL)'] == 'FAILED']

    # Replace values in the 'COMMENTS' column for the selected rows
    combined_data['COMMENTS'].replace({'USG C Comms': 'USBC-COMMS', 'USBC-COMM': 'USBC-COMMS', 'USBA-COMM': 'USBA-COMMS'}, inplace=True)
    #getting fail data that will be used for Top 10 Fail reason bar chart
    fail_10 = fail_data(combined_data)

    #finding percentages for PASS/FAIL
    total_result_count = len(combined_data)
    pass_count = (combined_data['TEST RESULT (PASS/FAIL)']=='PASSED').sum()
    fail_count = (combined_data['TEST RESULT (PASS/FAIL)']=='FAILED').sum()
    pass_percentage = (pass_count/total_result_count)*100
    fail_percentage = (fail_count/total_result_count)*100
    #creating dataframe for the pass/fail %'s
    passFail_df = pd.DataFrame({'Test Result': ['PASSED', 'FAILED'], 'Count':[pass_count, fail_count]})

    st.info("This is a sample of what the dashboard looks like. The official one uses local files to get data.")
    
    #start of the streamlit creation
    st.title(f"Dual USB ATP Data Visualization Dashboard For {selected_year}")

    #columns for the first two graphs: PASS/FAIL: Count and the First Pass Yield
    col = st.columns([1,1,1], gap='small')

    #PASS/FAIL test result chart
    col[0].subheader("Dual USB ATP PASS/FAIL Chart")

    # Create a pass/fail count chart
    fig_pass_fail = px.bar(passFail_df, x='Test Result', y='Count', text='Count', color='Test Result',
                        labels={'Test Result': 'Test Result', 'Count': 'Count'},
                        title='Pass/Fail Counts Result',
                        color_discrete_map={'PASSED': 'green', 'FAILED': 'red'})
    fig_pass_fail.update_layout(height=430, width=500)


    with col[0]:
        #displaying the pass/fail chart
        st.plotly_chart(fig_pass_fail, use_container_width=True)
        #checkbox for seeing the count results of how many pass/fail
        if st.checkbox('Show PASS/FAIL Count Results with Percentages'):
            st.subheader("PASS/FAIL Count Results")
            counts = combined_data[['TEST RESULT (PASS/FAIL)']].value_counts().reset_index()
            counts.columns= ['Test Result', 'Count']

            counts['Percentage (%)'] = (counts['Count']/total_result_count)*100
            st.write(counts)

    #generating a figure for the Top 10 fail reasons
    fig_fail = px.bar(x=fail_10.index, y=fail_10.values, text=fail_10.values,
                    labels={'x': 'Categories', 'y': 'Count'}, title=f'Top 10- Fail Reason for Dual USB {selected_year}',
                    category_orders={'x': fail_10.index})

    # Customize layout
    fig_fail.update_layout(xaxis=dict(tickangle=45, tickmode='array', tickvals=list(range(len(fail_10.index))),
                                    ticktext=fail_10.index))

    with col[2]:
        st.subheader('Fail Result Reasons')
        # Display top 10 fail chart in Streamlit
        st.plotly_chart(fig_fail, use_container_width=True, height=400)
        #checkbox to display dataframe of fail reasons
        if st.checkbox('Show Fail Result Reasons with Percentages'):
            failed_reason_data = display_failed_data_percentages(combined_data)
            st.write(failed_reason_data)

    col[1].subheader(f"First Pass Yield Results for Dual USD {selected_year}")

    #getting first pass yield data by doing calculations for FPY
    first_testNum = combined_data[combined_data['Test Number']==1]

    first_passed_count = (first_testNum['TEST RESULT (PASS/FAIL)']=='PASSED').sum()
    first_failed_count = (first_testNum['TEST RESULT (PASS/FAIL)']=='FAILED').sum()

    total_items = len(first_testNum)
    FPY = ((total_items-first_failed_count)/total_items)*100

    bar_data = pd.DataFrame({'Test Result': ['PASSED', 'FAILED'], 'Count': [first_passed_count, first_failed_count]})
    #create plotly express bar plot for the FPY chart
    fig_FPY = px.bar(bar_data, x='Test Result', y='Count', text='Count', color='Test Result',
                labels={'Test Result': 'Test Result', 'Count': 'Count'},
                title=f'Dual USD First Pass Yield {selected_year}',
                color_discrete_map={'PASSED': 'blue', 'FAILED': 'red'})

    with col[1]:
    # Shows FPY plot
        st.plotly_chart(fig_FPY, use_container_width=True, height=400)
        st.write(f'**First Pass Yield: {FPY:.2f}%**')
    #FPY for certain date ranges expander
    with st.expander("Click to see First Pass Yield for Certain Date Ranges"):
        st.subheader("First Pass Yield for Certain Date Ranges")
        st.write("***Select Specfic Range of Dates to get First Pass Yield Comparison Chart***")

        #dropping any 'N/A' values in the TEST DATE column
        valid_dates = data['TEST DATE'].dropna()

        #converts values in TEST DATE column and see which are valid or not
        date_errors = []
        #converts each value in TEST DATE column to datetime 
        valid_dates = valid_dates.apply(lambda x: pd.to_datetime(x, errors = 'coerce',exact=False, cache=True, format=None ))
        #extracts the indices of values that are NaT and stores them in list
        date_errors = valid_dates[valid_dates.isna()].index
        #dropping any invalid or N/A dates in dataframe
        valid_dates=valid_dates.dropna()
        #converting dates to a specfic format
        valid_dates = valid_dates.dt.strftime('%m/%d/%Y')
        #checking if the list of data error is not zero
        if len(date_errors) > 0:
            #writing out the invalid dates
            st.write("Following values could not be convert to datetime:")
            st.write(data.loc[date_errors, 'TEST DATE'])

        col_FPY = st.columns([1,1], gap='small')
        with col_FPY[0]:
            st.write("*Select First Date Data*")
            #selectbox for date range 1
            start_date_range1 = st.selectbox("Select Start Date", sorted(valid_dates.unique()))
            end_date_range1 = st.selectbox("Select End Date", sorted(valid_dates.unique()))
        #selectbox for date range 2
        with col_FPY[1]:
            st.write("*Select Second Date Data*")
            start_date_range2 = st.selectbox("Select Start Date", sorted(valid_dates.unique()), key="start_date_2")
            end_date_range2 = st.selectbox("Select End Date", sorted(valid_dates.unique()), key="end_date_2")

        #converting start and end dates to datatime
        start_date_range1 = pd.to_datetime(start_date_range1)
        end_date_range1 = pd.to_datetime(end_date_range1)
        start_date_range2 = pd.to_datetime(start_date_range2)
        end_date_range2 = pd.to_datetime(end_date_range2)

        #ensuring that the whole TEST DATE column is in datetime
        data['TEST DATE'] = pd.to_datetime(data['TEST DATE'], errors= 'coerce')

        # Filter data based on selected dates
        filtered_date_data_range1 = data[(data['TEST DATE'] >= start_date_range1) & (data['TEST DATE'] <= end_date_range1)]
        filtered_date_data_range2 = data[(data['TEST DATE'] >= start_date_range2) & (data['TEST DATE'] <= end_date_range2)]
        #Check if either of the date ranges contains data for the first text number 
        if (filtered_date_data_range1['Test Number'] == 1).any() or (filtered_date_data_range2['Test Number'] == 1).any():
            #combinding the data ranges 
            range_data_list = [filtered_date_data_range1, filtered_date_data_range2]
            range_names = ['Range 1', 'Range 2']
            #display checkboxes to show/hide for each range
            with col_FPY[0]:
                if st.checkbox('Click to see Date Range 1 Data'):
                    st.write(filtered_date_data_range1)
            with col_FPY[1]:
                if st.checkbox('Click to see Date Range 2 Data'):
                    st.write(filtered_date_data_range2)
            #generating the FPY graph and displaying it
            fig = FirstPassYield_GRAPH(range_data_list, range_names)
            st.plotly_chart(fig)
        else:
            #if data for the frist text number doesn't exist in either range, display warning messages
            if (filtered_date_data_range1['Test Number'] != 1).any():
                st.warning("The First Date Range can not compute the First Pass Yield Test.")
            if (filtered_date_data_range2['Test Number'] != 1).any():
                st.warning("The Second Date Range can not compute the First Pass Yield Test.")
            st.warning("**Try again with another Date Range.**")
    #Expander for the Pass/Fail Counts chart for certain date ranges, follows same format as FPY section above
    with st.expander("Click to see the Pass/Fail Counts Chart for Certain Date Ranges"):
        #dropping any 'N/A' values in the TEST DATE column
        valid_dates = data['TEST DATE'].dropna()

        #converts values in TEST DATE column and see which are valid or not
        date_errors = []
        #converts each value in TEST DATE column to datetime 
        valid_dates = valid_dates.apply(lambda x: pd.to_datetime(x, errors = 'coerce',exact=False, cache=True, format=None ))
        #extracts the indices of values that are NaT and stores them in list
        date_errors = valid_dates[valid_dates.isna()].index

        valid_dates=valid_dates.dropna()

        valid_dates = valid_dates.dt.strftime('%m/%d/%Y')

        if len(date_errors) > 0:
            st.write("Following values could not be convert to datetime:")
            st.write(data.loc[date_errors, 'TEST DATE'])

        col_fun = st.columns([1,1], gap='small')
        with col_fun[0]:
            st.write("*Select First Date Data*")
            #selectbox for date range 1
            start_date_range1 = st.selectbox("Select Start Date", sorted(valid_dates.unique()), key=f"start_date_1_unique_r1")
            end_date_range1 = st.selectbox("Select End Date", sorted(valid_dates.unique()), key=f"end_date_1_unique_r1")
        #selectbox for date range 2
        with col_fun[1]:
            st.write("*Select Second Date Data*")
            start_date_range2 = st.selectbox("Select Start Date", sorted(valid_dates.unique()), key=f"start_date_2_unique_r2")
            end_date_range2 = st.selectbox("Select End Date", sorted(valid_dates.unique()), key=f"end_date_2_unique_r2")

        #converting start and end dates to datatime
        start_date_range1 = pd.to_datetime(start_date_range1)
        end_date_range1 = pd.to_datetime(end_date_range1)
        start_date_range2 = pd.to_datetime(start_date_range2)
        end_date_range2 = pd.to_datetime(end_date_range2)

        #ensuring that the whole TEST DATE column is in datetime
        data['TEST DATE'] = pd.to_datetime(data['TEST DATE'], errors= 'coerce')

        # Filter data based on selected dates
        filtered_date_data_range1 = data[(data['TEST DATE'] >= start_date_range1) & (data['TEST DATE'] <= end_date_range1)]
        filtered_date_data_range2 = data[(data['TEST DATE'] >= start_date_range2) & (data['TEST DATE'] <= end_date_range2)]

        range_data_list = [filtered_date_data_range1, filtered_date_data_range2]

        concated_data = pd.concat(range_data_list)

        with col_fun[0]:
            if st.checkbox('Click to see Date Range 1 Data', key=f'function_r1_'):
                st.write(filtered_date_data_range1)
        with col_fun[1]:
            if st.checkbox('Click to see Date Range 2 Data', key=f'function_r2_'):
                st.write(filtered_date_data_range2)
        #getting pass/fail counts in dataframe    
        pass_count = (concated_data['TEST RESULT (PASS/FAIL)']== 'PASSED').sum()
        fail_count = (concated_data['TEST RESULT (PASS/FAIL)'] == "FAILED").sum()
    
        #creating combinded dataframe for Pass/Fail Counts
        passFail_df = pd.DataFrame({'Test Result':['PASSED', 'FAILED'], 'Count': [pass_count, fail_count]})
 
        #creates the Pass/Fail Counts bar chart
        fig_pass_fail = px.bar(passFail_df, x='Test Result', y='Count', text='Count', color='Test Result',
                            labels={'Test Result': 'Test Result', 'Count': 'Count'},
                            title='Pass/Fail Counts Result',
                            color_discrete_map={'PASSED': 'green', 'FAILED': 'red'})
        fig_pass_fail.update_layout(height=430, width=500)
        #displays pass.fail chart for certain date ranges
        st.plotly_chart(fig_pass_fail, use_container_width=True)
    #expander for Top 10 Fail reasons for certiandate ranges, follow same format to get date ranges as above
    with st.expander("Click to see the Top 10 Fail Reasons Chart for Certain Date Ranges"):
        #dropping any 'N/A' values in the TEST DATE column
        valid_dates = data['TEST DATE'].dropna()

        #converts values in TEST DATE column and see which are valid or not
        date_errors = []
        #converts each value in TEST DATE column to datetime 
        valid_dates = valid_dates.apply(lambda x: pd.to_datetime(x, errors = 'coerce',exact=False, cache=True, format=None ))
        #extracts the indices of values that are NaT and stores them in list
        date_errors = valid_dates[valid_dates.isna()].index
        valid_dates=valid_dates.dropna()

        valid_dates = valid_dates.dt.strftime('%m/%d/%Y')

        if len(date_errors) > 0:
            st.write("Following values could not be convert to datetime:")
            st.write(data.loc[date_errors, 'TEST DATE'])

        col_fun = st.columns([1,1], gap='small')
        with col_fun[0]:
            st.write("*Select First Date Data*")
            #selectbox for date range 1
            start_date_range1 = st.selectbox("Select Start Date", sorted(valid_dates.unique()), key=f"start_date_1_unique_top10")
            end_date_range1 = st.selectbox("Select End Date", sorted(valid_dates.unique()), key=f"end_date_1_unique_r1_top10")
        #selectbox for date range 2
        with col_fun[1]:
            st.write("*Select Second Date Data*")
            start_date_range2 = st.selectbox("Select Start Date", sorted(valid_dates.unique()), key=f"start_date_2_unique_r2_top10")
            end_date_range2 = st.selectbox("Select End Date", sorted(valid_dates.unique()), key=f"end_date_2_unique_r2_top10")

        #converting start and end dates to datatime
        start_date_range1 = pd.to_datetime(start_date_range1)
        end_date_range1 = pd.to_datetime(end_date_range1)
        start_date_range2 = pd.to_datetime(start_date_range2)
        end_date_range2 = pd.to_datetime(end_date_range2)

        #ensuring that the whole TEST DATE column is in datetime
        data['TEST DATE'] = pd.to_datetime(data['TEST DATE'], errors= 'coerce')

        # Filter data based on selected dates
        filtered_date_data_range1 = data[(data['TEST DATE'] >= start_date_range1) & (data['TEST DATE'] <= end_date_range1)]
        filtered_date_data_range2 = data[(data['TEST DATE'] >= start_date_range2) & (data['TEST DATE'] <= end_date_range2)]
        #combinding the range data list into bigger list
        range_data_list = [filtered_date_data_range1, filtered_date_data_range2]
        #concating dataframe 
        concated_data = pd.concat(range_data_list)

        with col_fun[0]:
            if st.checkbox('Click to see Date Range 1 Data', key=f'function_r1__top10'):
                st.write(filtered_date_data_range1)
        with col_fun[1]:
            if st.checkbox('Click to see Date Range 2 Data', key=f'function_r2__top10'):
                st.write(filtered_date_data_range2)
        #getting top 10 fail data for the fail chart
        fail_10 = fail_data(concated_data)
        #creating dataframe for the top 10 fail reasons
        fail_10_df = pd.DataFrame({'Categories': fail_10.index, 'Count': fail_10.values})
        #creating chart
        fig_fail = px.bar(fail_10_df, x='Categories', y='Count', text='Count',
                      labels={'Categories': 'Categories', 'Count': 'Count'},
                      title=f'Top 10 Fail Reasons for Dual USB {selected_year}',
                      category_orders={'Categories': fail_10.index})
        # Customize layout
        fig_fail.update_layout(xaxis=dict(tickangle=45, tickmode='array', tickvals=list(range(len(fail_10.index))),
                                    ticktext=fail_10.index))
        #displaying the top 10 fail reasons chart for specfic date ranges
        st.plotly_chart(fig_fail, use_container_width=True, height=400)

    #expander to see the Raw Data
    my_expander = st.expander(label='Expand to see the Raw Data')
    with my_expander:
        'Raw Data'
        st.write(data)
    #creatinga sidebar of download options
    with st.sidebar:
        st.subheader("Download Data Options")
        #selectbox of different download options
        downlaod_option = st.selectbox("Select Download Option", ["Download Raw Data","Download PASS/FAIL Graph",
                                            "Download First Pass Yield Graph", 'Download Top 10 Fail Reasons'])
        #checking if this download option is selected and data is not None
        if downlaod_option == "Download Raw Data" and data is not None:
            #converting data into csv
            raw_csv_data = data.to_csv(index=False)
            #downloading data with download_button in streamlit
            st.download_button(
                label="Download Raw Data",
                data=raw_csv_data,
                file_name=f"raw_data_{selected_year}.csv",
                mime="text/csv"
            )

        elif downlaod_option == "Download PASS/FAIL Graph": 
            image_stream = BytesIO() #intializes a BytesIO object 
            #write the figure into the BytesIO object using Plotly.io library
            pio.write_image(fig_pass_fail, image_stream, format='png')
            #downloads figure with download_button
            st.download_button(
                label = "Download PASS/FAIL Graph", 
                data = image_stream.getvalue(), 
                file_name =f"download_pass_fail_{selected_year}.png",
                mime="image/png")
            
        elif downlaod_option == "Download First Pass Yield Graph":
            image_stream1 = BytesIO()
            pio.write_image(fig_FPY, image_stream1, format='png')

            st.download_button(
                label = "Download First Pass Yield Graph", 
                data = image_stream1.getvalue(), 
                file_name =f"download_FirstPassYield_{selected_year}.png",
                mime="image/png")
        
        elif downlaod_option == "Download Top 10 Fail Reasons":
            image_stream2 = BytesIO()
            pio.write_image(fig_fail, image_stream2, format='png')

            st.download_button(
                label = "Download Top 10 Fail Reasons Graph", 
                data = image_stream2.getvalue(), 
                file_name =f"download_Top10FailReasons_{selected_year}.png",
                mime="image/png")
        st.info("Hover over any graphs/tables and click the download option, if a specfic option is not here.")
