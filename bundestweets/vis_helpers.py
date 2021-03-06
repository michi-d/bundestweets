
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


@st.cache(show_spinner=False)
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


@st.cache(show_spinner=False)
def get_offensive_tweets(data, thr=0.9):
    """
    Filters for offensive tweets in the dataset.
    
    Args:
        data: Tweet dataset
        
    Returns 
        offensive_tweets: Offensive tweets dataset
    """
    
    offensive_mask = (data.offensive_proba > 0.9)
    offensive_tweets = data.loc[offensive_mask]
    return offensive_tweets


@st.cache(show_spinner=False)
def get_plot_data_offensive_per_party(offensive_tweets, data):
    """
    Generates bar chart for offensive tweets per party.
    
    Args:
        offensive_tweets: Offensive tweets dataset
        data: Tweet dataset
        
    Returns 
        plot_data_abso: Absolute numbers offensive tweets per party
        plot_data_perc: Relative numbers offensive tweets per party
    """
    
    plot_data_abso = offensive_tweets['party'].value_counts()
    plot_data_perc = offensive_tweets['party'].value_counts()/data['party'].value_counts()
    plot_data_abso = plot_data_abso.reset_index()
    plot_data_perc = plot_data_perc.reset_index()
    plot_data_abso.columns = ['party', 'count']
    plot_data_perc.columns = ['party', 'count']
    
    return plot_data_abso, plot_data_perc


@st.cache(show_spinner=False)
def get_plot_data_offensive_responding(offensive_tweets):
    """
    Get plot data for counting offensive tweets as responses to other delegates
    
    Args:
        offensive_tweets: Offensive tweet dataset
        
    Returns:
        plot_data: Plot data for chart
    """
    df_name_party = offensive_tweets[['screen_name', 'real_name', 'party']].drop_duplicates().sort_values(by='party')
    set_of_names = set(df_name_party['screen_name'])

    N_argument = offensive_tweets.loc[:, 'resp_to'].apply(lambda row: str(row) in set_of_names).sum()
    N_total = len(offensive_tweets)

    plot_data = {'Responding to other delegates': N_argument, 
                 'Other': N_total}
    plot_data = pd.Series(plot_data)
    plot_data = (plot_data/plot_data.sum()).reset_index()
    plot_data.columns = ['label', 'count']
    
    return plot_data


@st.cache(show_spinner=False)
def get_member_tweets_per_month(member_tweets):
    """Aggregate member tweets per month for timeline plot
    
    Args:
        member_tweets: DataFrame with all tweets of a given member
        
    Returns:
        plot_df: Member stats aggregated by month
    """
    
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
    
    # aggregate per month
    plot_df = member_tweets.set_index(['date']).groupby(
        [pd.Grouper(freq='m', level=0), 
         pd.Grouper(key='real_name')])\
        .aggregate({'id': 'count',
                    'favorites': 'sum',
                    'retweets': 'sum'})\
        .reindex(new_index, fill_value=0, level=0)\
        .reset_index()
        
                           #.melt(value_vars=['real_name'], ignore_index=False)
    #plot_df = plot_df.reset_index()
    plot_df.columns = ['date', 'real_name', 'count', 'favorites', 'retweets']
    
    return plot_df


@st.cache(show_spinner=False)
def get_tweets_last_week(data):
    """Get all tweets from last week. 
    
    Args: 
        data: Tweet dataset
        
    Returns:
        tweets_last_week: Last week's tweets
    """
    
    date_index = pd.DatetimeIndex(data.date)
    date_index_sorted = date_index.sort_values(ascending=False)
    
    mondays = date_index_sorted.weekday == 0
    last_monday = next((i for i, x in enumerate(mondays) if x), None)
    end_sunday = date_index_sorted[last_monday].date() - datetime.timedelta(days=1)
    start_monday = date_index_sorted[last_monday].date() - datetime.timedelta(days=7)
    mask_last_week = (date_index.date >= start_monday) & (date_index.date <= end_sunday)
    
    tweets_last_week = data[mask_last_week]
    
    return tweets_last_week


@st.cache(show_spinner=False)
def get_top10_member_stats(tweets_last_week):
    """Get member-based rankings for last week.
    
    Args:
        tweets_last_week: Last's week twitter data
        
    Returns:
        top10_active: Top 10 w.r.t. tweet count
        top10_retweets: Top 10 w.r.t. retweets
        top10_favorites: Top 10 w.r.t. likes
    """
    real_name_to_party = dict(zip(tweets_last_week['real_name'], tweets_last_week['party']))

    top10_active = tweets_last_week.groupby('real_name')['id'].count().sort_values(ascending=False)[:10]
    top10_active = pd.DataFrame(top10_active).reset_index()
    top10_active['party'] = top10_active['real_name'].apply(lambda row: real_name_to_party[row])
    top10_active.columns = ['real_name', 'value', 'party']

    top10_retweets = tweets_last_week.groupby('real_name')['retweets'].sum().sort_values(ascending=False)[:10]
    top10_retweets = pd.DataFrame(top10_retweets).reset_index()
    top10_retweets['party'] = top10_retweets['real_name'].apply(lambda row: real_name_to_party[row])
    top10_retweets.columns = ['real_name', 'value', 'party']

    top10_favorites = tweets_last_week.groupby('real_name')['favorites'].sum().sort_values(ascending=False)[:10]
    top10_favorites = pd.DataFrame(top10_favorites).reset_index()
    top10_favorites['party'] = top10_favorites['real_name'].apply(lambda row: real_name_to_party[row])
    top10_favorites.columns = ['real_name', 'value', 'party']

    return top10_active, top10_retweets, top10_favorites


def get_top3_tweets(tweets_last_week):
    """Get three most successful tweets
    
    Args:
        tweets_last_week: Last's week twitter data
        
    Returns:
        most_retweets: Top 3 w.r.t. tweet retweets
        most_likes: Top 3 w.r.t. likes    
    """

    most_retweets = tweets_last_week.sort_values(by='favorites', ascending=False)[:3]
    most_likes = tweets_last_week.sort_values(by='retweets', ascending=False)[:3]
    
    return most_retweets, most_likes