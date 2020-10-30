#!/usr/bin/env python

"""Dataset: General statistics"""

import pandas as pd
import altair as alt
import numpy as np
import streamlit as st
import time
import sqlite3 
from holoviews import render

import bundestweets.helpers as helpers
import bundestweets.vis_helpers as vis_helpers
import bundestweets.stats_helpers as stats_helpers


# get basic data
#my_data, content_tweets = vis_helpers.get_data()

# get some basic statistics
#monthly_stats = vis_helpers.get_monthly_stats(content_tweets)
#how_many = vis_helpers.how_many_members(my_data)
#member_stats = vis_helpers.get_member_stats(content_tweets)


def write(analysis):
    """Writes the start Page"""
    
    # get data
    my_data = analysis['my_data']
    content_tweets = analysis['content_tweets']
    monthly_stats = analysis['monthly_stats']
    how_many = analysis['how_many']
    member_stats = analysis['member_stats']
    
    tweets_last_week = vis_helpers.get_tweets_last_week(analysis['my_data'])
    top10_active, top10_retweets, top10_favorites = vis_helpers.get_top10_member_stats(tweets_last_week)
    day_begin = tweets_last_week.date.min().strftime('%d.%b')
    day_end = tweets_last_week.date.max().strftime('%d.%b')
    
    st.write(f"""
    # Weekly report
    *Last week on Twitter ({day_begin} - {day_end})*
    """)
    

    ## Member stats
    st.write('''
    ### Member rankings
    ''')
    plot_ranking = st.selectbox(
        'Select:',
         ['Most active', 
          'Most retweeted tweets',
          'Most liked tweets'])
    if plot_ranking == 'Most active':
        plot_df = top10_active
        titleX = 'Number of tweets written'
    elif plot_ranking == 'Most retweeted tweets':
        plot_df = top10_retweets
        titleX = 'Number of retweets received'
    elif plot_ranking == 'Most liked tweets':
        plot_df = top10_favorites
        titleX = 'Number of likes received'
        
    barchart_ranking = alt.Chart(plot_df).mark_bar().encode(
        y=alt.Y('real_name:N', axis=alt.Axis(title='Member'), sort='-x'),
        x=alt.X('value:Q', stack='zero', axis=alt.Axis(title=titleX, format='s')),
        color=alt.Color("party:N", scale=alt.Scale(domain=stats_helpers.party_list,
                                                   range=list(map(vis_helpers.map_color, stats_helpers.party_list))
                                                  ))
    ).properties(width=600)

    st.altair_chart(barchart_ranking, use_container_width=True)

    
    