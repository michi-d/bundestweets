import pandas as pd
import altair as alt
import numpy as np
import streamlit as st
import time
from vega_datasets import data
import sqlite3
import bundestweets.helpers as helpers


@st.cache
def get_data():
    # get Bundestag members from Bundestag website and match them with Twitter accounts
    members_bundestag = helpers.get_data_twitter_members(do_fresh_download=False)
    members_bundestag = pd.DataFrame(members_bundestag).T

    conn = sqlite3.connect("bundestweets/data/tweets_data.db")
    sql_data = pd.read_sql("SELECT * FROM tweets", conn)
    conn.close()
    
    person = members_bundestag.loc[:, ['real_name', 'party', 'screen_name']]
    df = person.merge(sql_data, how='left', left_on='screen_name', right_on='username')

    mask = df.party.apply(lambda row: '*' not in row)
    df = df.loc[mask, :]
    
    return df

@st.cache
def get_stats(df):
    content_tweets = df.loc[~df.text.isna(), :]
    content_tweets.loc[:, 'date'] = pd.to_datetime(content_tweets.date, format='%Y-%m-%d-%H-%M-%S')
    
    stats = content_tweets.set_index('date').resample('m')['party'].value_counts()
    stats = stats.to_frame(name='tweets').reset_index(['party'])
    stats.index = stats.index.to_period('m').strftime('%Y-%m')
    stats.reset_index(inplace=True)
    
    return stats

def map_color(party):
    
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

    

my_data = get_data()
stats = get_stats(my_data)
    
plot_option = st.selectbox(
    'How many tweets are emitted from the Bundestag per month?',
     ['Absolute tweet count', 'Percentage of total tweets'])

if plot_option == 'Absolute tweet count':
    stack = 'zero'
elif plot_option == 'Percentage of total tweets':
    stack = 'normalize'
    
party_list = ['CDU/CSU', 'SPD', 'Bündnis 90/Die Grünen', 'FDP', 'Die Linke', 'AfD', 'fraktionslos'] 
    
chart = alt.Chart(stats).mark_area().encode(
    x="date:T",
    y=alt.Y("tweets:Q", stack=stack),
    color=alt.Color("party:N", scale=alt.Scale(
        domain=party_list,
        range=list(map(map_color, party_list))))
).properties(
    width=700,
    height=300
)

chart