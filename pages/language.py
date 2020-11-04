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
    *Automatically detecting offensive tweets*
    
    Offensive and polarizing language is an increasing problem in online political communication. 
    Let's do the check on our elected representatives!
    
    In order for an algorithm to detect whether a tweet is offensive or not, it needs to understand 
    a lot of the subtleties of written language. To approach this problem, we used a technique called 
    **transfer learning**: We took a model which had been trained already on some other task in German language 
    and fine-tuned it on our task. Specifically, we used the so called **BERT language model** and re-trained it on 
    a different tweet dataset with labeled examples of offensive language. 
    This training dataset happened to be made publicly
    available for research purposes already (https://projects.fzai.h-da.de/iggsa/).
    In this way, we could solve this difficult task without having to teach a completely new model the 
    complex word relationships of (German) language from scratch. For more technical background, please
    also have a look at 
    [this paper](https://hpi.de/fileadmin/user_upload/fachgebiete/naumann/publications/2019/risch2019offensive.pdf).
    
    One word of caution before looking at the results: Our model achieved 90% precision on a hold-out test set. 
    This means that, while we are quite confident that any tweet labeled as offensive indeed contains 
    offensive language, of course, this is not 100% sure. Also, as a trade-off for achieving that high precision, 
    we compromised on sensitivity which is only 30%. This means, we expect to miss around 70% of all offensive
    tweets in our dataset. But better be safe than sorry!
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
    ### How many offensive tweets are posted in response to other delegates?
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