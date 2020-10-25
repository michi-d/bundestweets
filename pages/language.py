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
import bundestweets.stats_helpers as stats_helpers

# get basic data
#my_data, content_tweets = vis_helpers.get_data()

def write(analysis):
    """Writes the Relations Page"""
    
    # get data
    my_data = analysis['my_data']
    
    st.write("""
    ## Offensive language
    
    Offensive and polarizing language is becoming increasingly a problem in online political communication. 
    How do our elected representatives do with respect to this issue?
    
    We used modern deep neural networks to detect offensive language in tweets. Specifically, 
    we used a pre-trained language model called *BERT* and retrained it on a publicly available
    offensive tweet data set (https://projects.fzai.h-da.de/iggsa/).
    
    Before interpreting the results of our analysis it is important to know the limitations of our approach:
    Classification is often a trade-off between precision and sensitivity. While we want always very precise as
    well as very sensitive models, it is hard to achieve both at the same time. We demanded of our model to achieve at
    least 90% precision on a hold-out test dataset. As a trade-off, we accepted a sensitivity of around 30%. 
    That means, while we are relatively confident for each tweet which is labeled as offensive (although not perfectly sure) 
    that it indeed contains offensive language, we miss around 70% of all offensive tweets. 
    
    For more background on our method, please also have a look at the paper:\n
    Risch J, Stoll A, Ziegele M, Krestel R. **hpiDEDIS at GermEval 2019: Offensive Language Identification using a German BERT model**. *InKONVENS 2019*.

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
                          (3, 5, 10, 15), index=1)

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


