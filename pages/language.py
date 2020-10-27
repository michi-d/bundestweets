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
    # Offensive language
    
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
    
    # Bar chart offensive tweets per party
    st.write('''
    ### How many offensive tweets were detected in the dataset for each party?
    ''')
    
    offensive_tweets = vis_helpers.get_offensive_tweets(my_data)
    plot_data_abso, plot_data_perc = vis_helpers.get_plot_data_offensive_per_party(offensive_tweets, my_data)
    
    plot_option_monthly = st.selectbox(
        'Select mode:',
         ['Absolute tweet count', 'Percentage of total tweets'])
    
    if plot_option_monthly == 'Absolute tweet count':
        plot_data = plot_data_abso
        format_ = 's'
        y_title = 'Number of offensive tweets'
    elif plot_option_monthly == 'Percentage of total tweets':
        plot_data = plot_data_perc
        format_ = '%'
        y_title = 'Proportion of offensive tweets (%)'
    
    chart = alt.Chart(plot_data).mark_bar().encode(
        y=alt.Y('count:Q', axis=alt.Axis(title=y_title, format=format_)),
        x=alt.X('party:N', axis=alt.Axis(title='Party')),
        color=alt.Color("party:N", scale=alt.Scale(domain=stats_helpers.party_list,
                                                   range=list(map(vis_helpers.map_color, stats_helpers.party_list))
                                                  ))
    ).properties(width=600, height=400)
    
    st.write(chart)

    # Responses to other delegates
    st.write('''
    ### How many offensive tweets are the result of an argument between delegates?
    ''')
    
    plot_data = vis_helpers.get_plot_data_offensive_responding(offensive_tweets)
    chart = alt.Chart(plot_data).mark_bar(size=20).encode(
            x=alt.X('count:Q', stack='zero', axis=alt.Axis(title='Fraction of offensive tweets', format='%'), 
                    scale=alt.Scale(domain=(0, 1))),
            color=alt.Color("label:N")
        ).properties(width=600, height=100)
    st.write(chart)
    
    # Show offensive tweets
    st.write('''
    ### List of offensive tweets:
    ###
    ''')
    choose_limit = st.selectbox(
        'Show last ...',
         [10, 20, 50, 100, 'all'], index=0)
    if choose_limit == 'all':
        limit = 1e9
    else:
        limit = int(choose_limit)
        
    for i, (id_, row) in enumerate(offensive_tweets.sort_values(by='date', ascending=False).iterrows()):
        st.write(f"""**{row.real_name}**, {row.party}, {row.date}:""")
        st.write(f"""{row.text}""")
        st.write(f"""{row.permalink}""")
        st.markdown("<hr>", unsafe_allow_html=True)
        if i == limit:
            break