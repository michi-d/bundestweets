#!/usr/bin/env python

"""Dataset: General statistics"""

import pandas as pd
import altair as alt
import numpy as np
import streamlit as st
import time
import sqlite3 
from holoviews import render
import datetime

import bundestweets.helpers as helpers
import bundestweets.vis_helpers as vis_helpers
import bundestweets.stats_helpers as staxts_helpers

# get basic data
#my_data, content_tweets = vis_helpers.get_data()

def write(analysis):
    """Writes the Relations Page"""
    
    # get data
    my_data = analysis['my_data']
    
    st.write("""
    # Relations
    
    How often do the delegates interact and respond to each other on Twitter?
    Select a time frame and generate a visualization showing the connections
    which are formed by tweets which are posted in response to other tweets by members of the
    Bundestag. The lines are coloured by the author of the tweets.
    """)
    
    # set default start and end times
    start_datetime = datetime.datetime.strptime('2018/05/01', '%Y/%M/%d')
    end_datetime = datetime.datetime.today()
    
    # select date range widget
    st.write("""
    ### Choose time frame:
    """)
    start_date = st.date_input('Start date', start_datetime)
    end_date = st.date_input('End date', end_datetime)
    
    # convert back to datetime
    start_datetime = datetime.datetime(year=start_date.year, month=start_date.month, day=start_date.day)
    end_datetime = datetime.datetime(year=end_date.year, month=end_date.month, day=end_date.day)

    # subset on selected time span
    mask = ((my_data.date >= start_datetime) & (my_data.date <= end_datetime))
    data_subset = my_data.loc[mask, :]
    
    # Drop down menu for threhold value
    thr_count = st.selectbox('Display only connections with more replies than ...', 
                          (3, 5, 10, 15), index=2)

    ## Get response tweets
    responses_count = vis_helpers.get_responses_count(data_subset)
    
    # show number of tweets selected
    if start_date < end_date:
        st.success(f'{len(responses_count)} tweets selected.')
    else:
        st.error('Error: End date must fall after start date.')
        
    ## Chord diagram
    chord_diagram = vis_helpers.generate_chord_diagram(responses_count, thr_count=int(thr_count))

    st.write(render(chord_diagram, backend='bokeh'))

    st.write("""
    ### How does this look like if we group by party and count the responses?
    """)
    ## Party-wise statistics
    for party in vis_helpers.party_cmap.keys():
        st.write(f"""### {party}""")
        chart = vis_helpers.generate_barplot_responding_to(responses_count, party=party)
        st.write(chart)


