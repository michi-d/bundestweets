
"""Streamlit WebApp to visualize basic statistics
"""

__author__ = "Michael Drews"
__copyright__ = "Copyright 2020, Michael Drews"
__email__ = "michaelsdrews@gmail.com"


import pandas as pd
import altair as alt
import numpy as np
import streamlit as st
import time
import sqlite3 
import json
from holoviews import render
import argparse

import bundestweets.helpers as helpers
import bundestweets.vis_helpers as vis_helpers
import bundestweets.stats_helpers as stats_helpers
import bundestweets.row_operators as row_operators
import pages.start
import pages.dataset
import pages.compare
import pages.relations
import pages.language
import pages.content
import pages.topics
import pages.weekly

parser = argparse.ArgumentParser()
parser.add_argument('-l', '--local', default=False, action='store_true')
args = parser.parse_args()

PAGES = {
    "Start": pages.start,
    "Dataset": pages.dataset,
    "Weekly report": pages.weekly,
    "Compare members": pages.compare,
    "Content analysis": pages.content,
    "Offensive language": pages.language,
    "Relations": pages.relations,
    "Topics timeline": pages.topics,
#    "About": src.pages.about,
}

def main():
    """Main function of the App"""
    
    st.sidebar.title("Bundestweets")
        
    # get basic data
    my_data, content_tweets = vis_helpers.get_data(args.local, db_file='bundestweets/data/tweets_data.db')

    # get some basic statistics
    monthly_stats = vis_helpers.get_monthly_stats(content_tweets)
    how_many = vis_helpers.how_many_members(my_data)
    member_stats = vis_helpers.get_member_stats(content_tweets)
    
    # load NLP translation dictionary
    with open('bundestweets/data/translation_set.json', 'r') as fp:
        translation_set = json.load(fp)
        
    # transform tweet messages to sets of words (for topics page)
    wordsets = vis_helpers.get_tweets_as_wordsets(content_tweets)
    nmf_topics = vis_helpers.get_nmf_results()

    analysis = {
        "my_data": my_data,
        "content_tweets": content_tweets,
        "monthly_stats": monthly_stats,
        "how_many": how_many,
        "member_stats": member_stats,
        "translation_set": translation_set,
        "wordsets": wordsets,
        "topics": nmf_topics
    }
    
    # write navigation panel
    st.sidebar.title("Navigation")
    selection = st.sidebar.radio("Go to", list(PAGES.keys()))
    page = PAGES[selection]
    
    with st.spinner(f"Loading {selection} ..."):
        page.write(analysis)
        

    st.sidebar.title("About")
    st.sidebar.info(
        "This an open source project. Source code for the app "
        "and all analyses is publicly available on "
        "[GitHub](https://github.com/michi-d/bundestweets). "
    )
    st.sidebar.info(
    """
    This page is maintained by Michael Drews. 
    For questions, inquiries or concerns please contact me at
    [michaelsdrews@gmail.com](mailto:michaelsdrews@gmail.com).
    """
    )
    
if __name__ == "__main__":
    main()