#!/usr/bin/env python

"""Dataset: General statistics"""

import pandas as pd
import altair as alt
import numpy as np
import streamlit as st
import time
import sqlite3 
import datetime

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
    
    
    st.write("""
    # Compare
    
    *Compare the Twitter activity of different members of the Bundestag.*
    """)
    
    # get mappings between names, parties and indexes
    df_name_party = my_data[['screen_name', 'real_name', 'party']].drop_duplicates().sort_values(by='party')
    set_of_names = set(df_name_party['real_name'])
    realname_to_party = dict(zip(df_name_party['real_name'], df_name_party['party']))
    name_to_realname = dict(zip(df_name_party['screen_name'], df_name_party['real_name']))

    # select name
    options = [f"{name} ({party})" for name, party in realname_to_party.items()]
    options = sorted(options)
    select_name = st.multiselect('Twitter profile:', options, 
                                 ['Esken, Saskia (SPD)', 
                                  'Brandner, Stephan (AfD)', 
                                  'Lauterbach, Prof. Dr. Karl (SPD)'])
    
    # get member tweets
    selected_names = [name.split('(')[0][:-1] for name in select_name]
    mask_members = np.zeros(len(my_data), dtype=np.bool)
    for name in selected_names:
        mask_members = mask_members | (my_data.real_name == name)
    member_tweets = my_data.loc[mask_members]

    #turn_around_name = " ".join(selected_name.split(',')[::-1])
    #st.write(f'### {turn_around_name}')
    #st.markdown(f'Total tweets: {len(member_tweets)}')
    #st.markdown(f'Total retweets: {len(member_tweets)}')
    
    # Show tweets per month
    st.write('### Tweets per month')
    
    plot_df = vis_helpers.get_member_tweets_per_month(member_tweets)
    
    timechart = alt.Chart(plot_df).mark_line().encode(
        x=alt.X('date:T', axis=alt.Axis(title='Date')),
        y=alt.X('count:Q', axis=alt.Axis(title='Tweets')),
        color=alt.Color('real_name', scale=alt.Scale(scheme='category10'), 
                        legend=alt.Legend(columns=2)) 
    ).properties(width=600, height=300).configure_legend(orient='bottom', labelLimit=0)
    
    st.altair_chart(timechart, use_container_width=True)
    
    # Show likes per month
    st.write('### Likes received per month')
    
    plot_df = vis_helpers.get_member_tweets_per_month(member_tweets)
    
    timechart = alt.Chart(plot_df).mark_line().encode(
        x=alt.X('date:T', axis=alt.Axis(title='Date')),
        y=alt.X('favorites:Q', axis=alt.Axis(title='Likes')),
        color=alt.Color('real_name', scale=alt.Scale(scheme='category10'), 
                        legend=alt.Legend(columns=2)) 
    ).properties(width=600, height=300).configure_legend(orient='bottom', labelLimit=0)
    
    st.altair_chart(timechart, use_container_width=True)

    # Show retweets per month
    st.write('### Retweeted per month')
    
    plot_df = vis_helpers.get_member_tweets_per_month(member_tweets)
    
    timechart = alt.Chart(plot_df).mark_line().encode(
        x=alt.X('date:T', axis=alt.Axis(title='Date')),
        y=alt.X('retweets:Q', axis=alt.Axis(title='Retweets')),
        color=alt.Color('real_name', scale=alt.Scale(scheme='category10'), 
                        legend=alt.Legend(columns=2)) 
    ).properties(width=600, height=300).configure_legend(orient='bottom', labelLimit=0)
    
    st.altair_chart(timechart, use_container_width=True)


    # Show last tweets
    st.write('''
    ## Most recent tweets
    ##
    ''')
    choose_limit = st.selectbox(
        'Show last ...',
         [10, 20, 50, 100, 500, 1000], index=0)
    limit = int(choose_limit)
        
    for i, (id_, row) in enumerate(member_tweets.sort_values(by='date', ascending=False).iterrows()):
        st.write(f"""**{row.real_name}**, {row.party}, {row.date}:""")
        st.write(f"""{row.text}""")
        st.write(f"""{row.permalink}""")
        st.markdown("<hr>", unsafe_allow_html=True)
        if i == limit:
            break