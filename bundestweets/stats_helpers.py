
"""Functions for statistical analysis of the tweet dataset
"""

__author__ = "Michael Drews"
__copyright__ = "Copyright 2020, Michael Drews"
__email__ = "michaelsdrews@gmail.com"

import pandas as pd
import numpy as np
import streamlit as st

import time
import sqlite3
import bundestweets.helpers as helpers


party_list = ['CDU/CSU', 'SPD', 'Bündnis 90/Die Grünen', 'FDP', 'Die Linke', 'AfD', 'fraktionslos'] 


def get_raw_data(do_fresh_download=False):
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
    conn = sqlite3.connect("bundestweets/data/tweets_data.db")
    sql_data = pd.read_sql("SELECT * FROM tweets", conn)
    conn.close()
    
    # merge members with corresponding tweets
    person = members_bundestag.loc[:, ['real_name', 'party', 'screen_name']]
    df = person.merge(sql_data, how='left', left_on='screen_name', right_on='username')

    mask = df.party.apply(lambda row: '*' not in row)
    df = df.loc[mask, :]
    
    return df