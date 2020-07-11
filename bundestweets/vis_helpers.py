
"""Some helper functions for visualization / WebApp
"""

__author__ = "Michael Drews"
__copyright__ = "Copyright 2020, Michael Drews"
__email__ = "michaelsdrews@gmail.com"

import streamlit as st
import pandas as pd
import altair as alt
import numpy as np

import time
import sqlite3
import bundestweets.helpers as helpers
import bundestweets.stats_helpers as stats_helpers


@st.cache
def get_data():
    '''Get all data from SQL file and filter for relevent tweets
    
    Returns:
        df: DataFrame with raw data
        content_tweets: only tweets with text
    '''
    # get all tweet date
    df = stats_helpers.get_raw_data()
    
    # get non-empty tweets (only with text content)
    content_tweets = df.loc[~df.text.isna(), :]
    content_tweets.loc[:, 'date'] = pd.to_datetime(content_tweets.date, format='%Y-%m-%d-%H-%M-%S')
    
    return df, content_tweets


def map_color(party):
    '''Color mapping for political parties
    
    Args:
        party (str): Which party
        
    Returns:
        color (str): Which color
    '''
    if party == 'SPD':
        color = 'red'
    elif party == "CDU/CSU":
        color = 'black'
    elif party == 'Die Linke':
        color = 'orchid'
    elif party == 'Bündnis 90/Die Grünen':
        color = 'limegreen'  
    elif party == 'AfD':
        color = 'steelblue'
    elif party == 'fraktionslos':
        color = 'gray'
    elif party == 'FDP':
        color = 'gold'
        
    return color


@st.cache
def get_monthly_stats(content_tweets):
    '''Get monthly tweet count per party
    
    Args:
        content_tweets: Non-empty tweets dataset
        
    Returns:
        content_tweets: DataFrame 
        stats: DataFrame with columns (date, party, count)
    '''
    # resample per month and count per party
    stats = content_tweets.set_index('date').resample('m')['party'].value_counts()
    stats = stats.to_frame(name='count').reset_index(['party'])
    stats.index = stats.index.to_period('m').strftime('%Y-%m')
    stats.reset_index(inplace=True)
    
    return stats


@st.cache
def how_many_members(df):
    '''Count representatives in Twitter or Parliament per Party
    
    Args:
        df: Basic dataset
        
    Returns:
        count: DataFrame with columns (where, party, count)
        
    '''
    # Get twitter accounts / count per party
    twitter_accounts = df.loc[:, ['screen_name', 'party']].drop_duplicates().party.value_counts()
    
    # Get seats in parliament / count per party
    bundestag_seats = df.loc[:, ['real_name', 'party']].drop_duplicates().party.value_counts()
    
    count = pd.concat([twitter_accounts, bundestag_seats], keys=['Twitter', 'Bundestag'])
    count = count.to_frame().reset_index()
    count.columns = ['where', 'party', 'count']
    
    return count

@st.cache
def get_member_stats(content_tweets):
    '''Get some statistics on an individual level
    
    Args:
        content_tweets: Non-empty tweets dataset
        
    Returns:
        member_stats: DataFrame with columns ('name', 'party', 'count')
    '''
    # count tweets per member
    member_stats = content_tweets.groupby(['real_name', 'party']).id.count().to_frame().reset_index()
    member_stats.columns = ['name', 'party', 'count']
    
    # calculate tweet count as fraction of total tweets
    member_stats.loc[:, 'fraction'] = (member_stats.loc[:, 'count']/member_stats.loc[:, 'count'].sum())
    
    member_stats = member_stats.sort_values(by='count', ascending=False)
    
    return member_stats