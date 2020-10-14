
"""Functions for statistical analysis of the tweet dataset
"""

__author__ = "Michael Drews"
__copyright__ = "Copyright 2020, Michael Drews"
__email__ = "michaelsdrews@gmail.com"

import pandas as pd
import numpy as np
import streamlit as st
import os

import time
import sqlite3
import bundestweets.helpers as helpers


party_list = ['CDU/CSU', 'SPD', 'Bündnis 90/Die Grünen', 'FDP', 'Die Linke', 'AfD', 'fraktionslos'] 

def get_raw_data(local=False, do_fresh_download=False, db_file='tweets_data.db'):
    '''Get basic dataset of all members and together with their tweets
    
    Args:
        do_fresh_download (bool): whether to scrape Bundestag website for current members or not

    Returns:
        df: pandas.DataFrame
    '''
    
    # get Bundestag members from Bundestag website
    members_bundestag = helpers.get_data_twitter_members(do_fresh_download=do_fresh_download)
    members_bundestag = pd.DataFrame(members_bundestag).T

    # retrieve tweet data from SQL file
    #dir_path = os.path.dirname(os.path.realpath(__file__))
    #file_path = os.path.join(dir_path, 'data', db_file)
        
    if local:
        # local database file
        conn = sqlite3.connect(db_file)
        df = pd.read_sql("SELECT * FROM tweets", conn)
        conn.close()
    else:
        # Cloud SQL
        df = helpers.cloud_get_dataset()
    
    # merge members with corresponding tweets
    person = members_bundestag.loc[:, ['real_name', 'party', 'screen_name']]

    username2realname = {k: v for (k,v) in zip(person.screen_name, person.real_name)}
    username2party = {k: v for (k,v) in zip(person.screen_name, person.party)}

    real_name = df.username.map(username2realname)
    party = df.username.map(username2party)

    df['real_name'] = real_name
    df['party'] = party

    # delete historical members
    mask = df.party.apply(lambda row: '*' not in row)
    df = df.loc[mask, :]

    # convert date to datetime
    df.date = pd.to_datetime(df.date, format='%Y-%m-%d-%H-%M-%S')
    
    # rename username to screen_name
    df.rename(columns={"username": "screen_name"}, inplace=True)
    
    return df
