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
    
    
    st.write("""
    ## Dataset
    
    Our data set contains around ~450.000 tweets, posted by all members of the Bundestag which have a Twitter account
    since the year 2018.
    
    Have a look at some general statistics from our Bundestweet dataset!
    """)
    
    
    ## Stacked area plot: monthly stats
    st.write('''
    ### How many tweets are emitted from the Bundestag per month?
    ''')
    plot_option_monthly = st.selectbox(
        'Select mode:',
         ['Absolute tweet count', 'Percentage of total tweets'])

    if plot_option_monthly == 'Absolute tweet count':
        stack_monthly = 'zero'
        format_monthly = 's'
        y_title_monthly = 'count'
    elif plot_option_monthly == 'Percentage of total tweets':
        stack_monthly = 'normalize'
        format_monthly = '%'
        y_title_monthly = 'fraction'


    chart_monthly_stats = alt.Chart(monthly_stats).mark_area().encode(
        x="date:T",
        y=alt.Y("count:Q", stack=stack_monthly, axis=alt.Axis(title=y_title_monthly, format=format_monthly)),
        color=alt.Color("party:N", 
                        scale=alt.Scale(domain=stats_helpers.party_list, 
                                        range=list(map(vis_helpers.map_color, stats_helpers.party_list))
                                       ))
    ).properties(width=600, height=300)

    st.write(chart_monthly_stats)

    ## Stacked bar plot: How many members on Twitter / in Bundestag?
    st.write('''
    ### How many representatives do the parties have?
    ''')
    
    plot_option_how_many = st.selectbox(
        'Select mode:',
         ['Absolute numbers', 'Percentage'])

    if plot_option_how_many == 'Absolute numbers':
        stack_how_many = 'zero'
        title_how_many = ''
        format_how_many = 's'
    elif plot_option_how_many == 'Percentage':
        stack_how_many = 'normalize'
        title_how_many = ''
        format_how_many = '%'

    chart_how_many = alt.Chart(how_many).mark_bar().encode(
        y=alt.Y('where:N', axis=alt.Axis(title='')),
        x=alt.X('sum(count):Q', stack=stack_how_many, axis=alt.Axis(title=title_how_many, format=format_how_many)),
        color=alt.Color("party:N", scale=alt.Scale(domain=stats_helpers.party_list,
                                                   range=list(map(vis_helpers.map_color, stats_helpers.party_list))
                                                  ))
    ).properties(width=600, height=120)

    st.write(chart_how_many)

    ## Bar plot: Activity ranking
    st.write('''
    ### Which delegates are most active on Twitter?
    ''')
    top_head = st.selectbox(
        'Select top ...',
         [10, 20, 30, 40, 50])

    perc_chart_member_tweets = alt.Chart(member_stats.head(top_head)).mark_bar(size=20).encode(
        #y=alt.Y('party:N', axis=alt.Axis(title='')),
        x=alt.X('sum(fraction):Q', stack='zero', axis=alt.Axis(title='fraction of all tweets', format='%'), 
                scale=alt.Scale(domain=(0, 1))),
        color=alt.Color("party:N", legend=None, scale=alt.Scale(domain=stats_helpers.party_list,
                                                   range=list(map(vis_helpers.map_color, stats_helpers.party_list))
                                                  ))
    ).properties(width=600, height=80)

    st.write(perc_chart_member_tweets)


    barchart_member_stats = alt.Chart(member_stats.head(top_head)).mark_bar().encode(
        y=alt.Y('name:N', axis=alt.Axis(title=''), sort='-x'),
        x=alt.X('count:Q', stack='zero', axis=alt.Axis(title='Tweet count', format='s')),
        color=alt.Color("party:N", scale=alt.Scale(domain=stats_helpers.party_list,
                                                   range=list(map(vis_helpers.map_color, stats_helpers.party_list))
                                                  ))
    ).properties(width=600)

    st.write(barchart_member_stats)

    ## Chord diagram
    #responses_count = vis_helpers.get_responses_count(my_data)
    #chord_diagram = vis_helpers.generate_chord_diagram(responses_count)

    #st.write(render(chord_diagram, backend='bokeh'))


