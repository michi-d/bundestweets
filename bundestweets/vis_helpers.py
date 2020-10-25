
"""Some helper functions for visualization / WebApp
"""

__author__ = "Michael Drews"
__copyright__ = "Copyright 2020, Michael Drews"
__email__ = "michaelsdrews@gmail.com"

import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
import datetime as datetime
import json

import time
import sqlite3
import bundestweets.helpers as helpers
import bundestweets.stats_helpers as stats_helpers
import bundestweets.row_operators as row_operators
from bundestweets.nlp import intersect_topics

import holoviews as hv
from holoviews import opts as hv_opts
from holoviews import dim as hv_dim
hv.extension('bokeh')

from wordcloud import WordCloud
from matplotlib.colors import to_rgba
from matplotlib.colors import LinearSegmentedColormap

party_cmap = {
    'CDU/CSU': 'black', 
    'SPD': 'red',
    'FDP': 'gold',
    'Die Linke': 'orchid',
    'Bündnis 90/Die Grünen': 'limegreen', 
    'AfD': 'steelblue',
    'fraktionslos': 'gray',
}


@st.cache
def get_data(local=False, db_file='bundestweets/data/tweets_data.db'):
    """Get all data from SQL file and filter for relevent tweets
    
    Returns:
        df: DataFrame with raw data
        content_tweets: only tweets with text
    """
    
    
    # get all tweet data
    df = stats_helpers.get_raw_data(local=local, db_file=db_file)
    
    # get non-empty tweets (only with text content)
    content_tweets = df.loc[~df.text.isna(), :]
    #content_tweets.loc[:, 'date'] = pd.to_datetime(content_tweets.date, format='%Y-%m-%d-%H-%M-%S')
    
    return df, content_tweets


def map_color(party):
    """Color mapping for political parties
    
    Args:
        party (str): Which party
        
    Returns:
        color (str): Which color
    """
    return party_cmap[party]


@st.cache(show_spinner=False)
def get_monthly_stats(content_tweets):
    """Get monthly tweet count per party
    
    Args:
        content_tweets: Non-empty tweets dataset
        
    Returns:
        content_tweets: DataFrame 
        stats: DataFrame with columns (date, party, count)
    """
    # resample per month and count per party
    stats = content_tweets.set_index('date').resample('m')['party'].value_counts()
    stats = stats.to_frame(name='count').reset_index(['party'])
    stats.index = stats.index.to_period('m').strftime('%Y-%m')
    stats.reset_index(inplace=True)
    
    return stats


@st.cache(show_spinner=False)
def how_many_members(df):
    """Count representatives in Twitter or Parliament per Party
    
    Args:
        df: Basic dataset
        
    Returns:
        count: DataFrame with columns (where, party, count)
        
    """
    # Get twitter accounts / count per party
    twitter_accounts = df.loc[:, ['screen_name', 'party']].drop_duplicates().party.value_counts()
    
    # Get seats in parliament / count per party
    #bundestag_seats = df.loc[:, ['real_name', 'party']].drop_duplicates().party.value_counts()
    members_bundestag = helpers.get_data_twitter_members(do_fresh_download=False)
    members_bundestag = pd.DataFrame(members_bundestag).T
    mask = members_bundestag.party.apply(lambda row: '*' not in row) # delete historical members
    members_bundestag = members_bundestag.loc[mask, :]
    bundestag_seats = members_bundestag.loc[:, ['real_name', 'party']].drop_duplicates().party.value_counts()

    count = pd.concat([twitter_accounts, bundestag_seats], keys=['Twitter', 'Bundestag'])
    count = count.to_frame().reset_index()
    count.columns = ['where', 'party', 'count']
    
    return count

@st.cache(show_spinner=False)
def get_member_stats(content_tweets):
    """Get some statistics on an individual level
    
    Args:
        content_tweets: Non-empty tweets dataset
        
    Returns:
        member_stats: DataFrame with columns ('name', 'party', 'count')
    """
    # count tweets per member
    member_stats = content_tweets.groupby(['real_name', 'party']).id.count().to_frame().reset_index()
    member_stats.columns = ['name', 'party', 'count']
    
    # calculate tweet count as fraction of total tweets
    member_stats.loc[:, 'fraction'] = (member_stats.loc[:, 'count']/member_stats.loc[:, 'count'].sum())
    
    member_stats = member_stats.sort_values(by='count', ascending=False)
    
    return member_stats


@st.cache(show_spinner=False)
def get_responses_count(data):
    """
    
    Args:
        data: Tweets dataset
    """
    
    # get mappings between names, parties and indexes
    df_name_party = data[['screen_name', 'real_name', 'party']].drop_duplicates().sort_values(by='party')
    set_of_names = set(df_name_party['screen_name'])

    name_to_party = dict(zip(df_name_party['screen_name'], df_name_party['party']))
    name_to_realname = dict(zip(df_name_party['screen_name'], df_name_party['real_name']))

    # give integer indexes to each name
    name_to_index = dict(zip(df_name_party['screen_name'], range(len(df_name_party))))
    index_to_name = {v:k for (k,v) in name_to_index.items()}
    
    # get only those tweets which are responses to other parliaments nembers
    masked_names = data.loc[:, 'resp_to'].apply(lambda row: row if (str(row) in set_of_names) else False)
    responding_tweets = data.loc[masked_names != False, :]

    # count responses between people
    responses_count = responding_tweets.groupby(['screen_name'])['resp_to'].value_counts()
    responses_count.name = 'count'
    responses_count = responses_count.reset_index()

    # filter out self-responses
    responses_count = responses_count.loc[responses_count.loc[:, 'screen_name'] != responses_count.loc[:, 'resp_to'], :]
    
    # generate new parameter columns for the plotting function
    responses_count['party'] = responses_count['screen_name'].apply(lambda row: name_to_party[row])
    responses_count['real_name'] = responses_count['screen_name'].apply(lambda row: name_to_realname[row])
    responses_count['index'] = responses_count['screen_name'].apply(lambda row: name_to_index[row])
    responses_count['target'] = responses_count['resp_to'].apply(lambda row: name_to_index[row])
    responses_count['target_party'] = responses_count['resp_to'].apply(lambda row: name_to_party[row])
    responses_count = responses_count.sort_values(by='party')
    
    return responses_count


@st.cache(show_spinner=False)
def generate_chord_diagram(responses_count, thr_count=5):
    
    # generate dataframes as required for the plotting function
    plot_data = responses_count.loc[responses_count['count']>0, ['index', 'target', 'count']]
    plot_data.columns = ['source', 'target', 'value']
    plot_data.index = np.arange(len(plot_data))
    
    nodes = responses_count.loc[responses_count['count']>0, ['index', 'screen_name', 'party']].\
                            drop_duplicates().set_index('index').sort_index(level=0)
    nodes = hv.Dataset(nodes, 'index')
    nodes.data.head()

    # generate colormap for single accounts according to party affiliations
    person_party_cmap = dict(zip(responses_count['index'], responses_count['party'].apply(lambda row: party_cmap[row])))
    
    # generate plot
    chord = hv.Chord((plot_data, nodes)).select(value=(thr_count, None))
    chord.opts(
        hv_opts.Chord(cmap=party_cmap, 
                   edge_cmap=person_party_cmap, 
                   edge_color=hv_dim('source'), 
                   labels='screen_name', 
                   node_color=hv_dim('party'), 
                   edge_hover_line_color='cyan',
                   node_hover_fill_color='cyan',
                   height=700,
                   width=700))
    
    return chord


@st.cache(show_spinner=False)
def create_word_cloud(party_word_importance, party):
    """Creates a word cloud image for one party
    
    Args:
        party_word_importance: Dictionary containing the word scores for all parties
        party: Selected party
        
    Returns:
        wordcloud: Wordcloud
    """

    word_freq = party_word_importance[party]

    color = to_rgba(party_cmap[party])
    cdict = {'red':   [(0.0,  0.0, color[0]*0.5),
                       (1.0,  color[0]*1.0, 0.0)],
             'green': [(0.0,  0.0, color[1]*0.5),
                       (1.0,  color[1]*1.0, 0.0)],
             'blue':  [(0.0,  0.0, color[2]*0.5),
                       (1.0,  color[2]*1.0, 0.0)]}
    newcmp = LinearSegmentedColormap('newCmap', segmentdata=cdict, N=256)


    wordcloud = WordCloud(background_color="white", random_state=0,
                          width=800, height=400, max_words=35, max_font_size=60, relative_scaling=0.5,
                          prefer_horizontal=1.0, colormap=newcmp)
    wordcloud = wordcloud.generate_from_frequencies(frequencies=word_freq)
    
    return wordcloud


@st.cache(show_spinner=False)
def get_tweets_as_wordsets(data):
    """Transforms tweets messages to set of words (for topic page).
    
    Args:
        data: Tweet database
        
    Returns:
        wordsets: Tweets as sets of words
    """
    wordsets = data.apply(row_operators.get_tweet_as_word_set, axis=1)
    return wordsets


@st.cache(show_spinner=False)
def get_topic_timeline_df(topics, wordsets, data):
    """Prepares data for the timeline plot (Topics vs. time).
    
    Args:
        topics: Dictionary mapping topic ID's to key words
        wordsets: pandas.Series of tweet messages formatted as sets of words
        data: Tweet Dataset
        
    Returns:
        plot_df: Dataframe formatted for plotting
    """
    
    # intersect topics with all twitter messages
    intersections = intersect_topics(topics, wordsets)
    my_topics = pd.DataFrame(intersections, index=data.date)

    # get new time axis (monthly resolution)
    start_datetime = datetime.datetime.strptime('2018/01/01', '%Y/%M/%d')
    end_datetime = datetime.datetime.today()

    start_datetime = datetime.datetime(
        year=start_datetime.year, 
        month=start_datetime.month,
        day=start_datetime.day,
    )
    end_datetime = datetime.datetime(
        year=end_datetime.year, 
        month=end_datetime.month,
        day=end_datetime.day,
    )
    new_index = pd.date_range(start_datetime, end_datetime, freq='M')
    
    # resample topic data with new time index and re-format to long format
    plot_df = my_topics.resample('m').sum().reindex(new_index, fill_value=0).melt(value_vars=range(len(topics)), ignore_index=False)
    plot_df = plot_df.reset_index()
    plot_df.columns = ['Date', 'Keywords', 'Tweets']
    plot_df['Keywords'] = plot_df['Keywords'].apply(lambda k: " ".join(topics[k]))
    
    return plot_df


@st.cache(allow_output_mutation=True, show_spinner=False)
def get_nmf_results():
    """Load NMF results from json file."""

    with open('./bundestweets/data/nmf_topics.json', 'r') as fp:
        nmf_topics = json.load(fp)
        
    nmf_topics = {int(k): v for (k,v) in nmf_topics.items()}
    return nmf_topics


def reload_nmf_results():
    """Load NMF results from json file."""

    with open('./bundestweets/data/nmf_topics.json', 'r') as fp:
        nmf_topics = json.load(fp)
        
    nmf_topics = {int(k): v for (k,v) in nmf_topics.items()}
    return nmf_topics


def generate_barplot_responding_to(responses_count, party='CDU/CSU'):
    """
    Given the grouped the responses count DataFrame between single members,
    group by parties and generate party-wise statistics.
    
    Args:
        responses_count: output of get_responses_count
    
    Returns:
        chart: Bar chart summarizing party-wise response statistics
    """
    
    party_responses_to = responses_count[['party', 'target_party', 'count']].groupby(['party', 'target_party']).sum()
    plot_data = party_responses_to.loc[party].reset_index()

    chart = alt.Chart(plot_data).mark_bar().encode(
        y=alt.Y('count:Q', axis=alt.Axis(title='Tweets')),
        x=alt.X('target_party:N', axis=alt.Axis(title='Responding to')),
        color=alt.Color("target_party:N", scale=alt.Scale(domain=stats_helpers.party_list,
                                                   range=list(map(map_color, stats_helpers.party_list))
                                                  ))
    ).properties(width=400, height=400)
    
    return chart


