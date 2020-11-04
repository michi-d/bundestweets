#!/usr/bin/env python

"""Dataset: General statistics"""

import pandas as pd
import altair as alt
import numpy as np
import streamlit as st
import json 

import bundestweets.helpers as helpers
import bundestweets.vis_helpers as vis_helpers
import bundestweets.stats_helpers as stats_helpers


def write(analysis):
    """Writes the Topics Page"""
    
    # get data
    my_data = analysis['my_data']
    wordsets = analysis['wordsets']
    
    st.write("""
    # Topic identification
    
    What do the delegates of the Bundestag tweet about? What topics are most intensely discussed on Twitter? And how does this develop over time?
    
    We used an unsupervised algorithm called **non-negative matrix factorization (NMF)** to find about this.
    NMF tries to find words which have a high probability of ocurring simultaneously in a document. As it turns out, this
    is very useful to identify topics in a text dataset because most topics stand out each by their own set of characteristic keywords.
    
    We applied NMF only on the hashtags in the tweets. We did this because hashtags are actually already quite condensed
    and informative keywords when it comes to political tweets. 
    
    
    In the drop-down menu below you can find the keywords of the topics that NMF identified. You can select topics and we
    will look up for you how often the corresponding keywords were mentioned over the past years.
    In addition, you can come up with your own set of keywords and see if you can find interesting patterns.
    """)
    
#    On the other hand it is useful to filter out tweets which don't really have a political message (e.g. birthday #greetings) because 
#    those messages tend to have less or less informative hashtags.
    #copy = vis_helpers.reload_nmf_results()
    #for k, v in copy.items():
    #    st.write(f"""Topic {k}: {" ".join(v)}""")
    
    input_field = st.text_input("", "")
    button_add = st.button("Add keywords (separated by white space)")
    if button_add:
        analysis['topics'][len(analysis['topics'])+1] = input_field.split()
        
    option_list = [" ".join(v) for v in analysis['topics'].values()]
    options = st.multiselect('Choose keywords ...', option_list,
                             default=[option_list[15], option_list[16]])
    
    ## Timeline plot
    topics = {i: options[i].split() for i in range(len(options))}
    plot_df = vis_helpers.get_topic_timeline_df(topics, wordsets, my_data)
        
    timechart = alt.Chart(plot_df).mark_line().encode(
        x=alt.X('Date:T', axis=alt.Axis(title='Date')),
        y=alt.X('Tweets:Q', axis=alt.Axis(title='Tweets')),
        color=alt.Color('Keywords', scale=alt.Scale(scheme='category10'), 
                        legend=alt.Legend(columns=2)) 
    ).properties(width=600, height=400).configure_legend(orient='bottom', labelLimit=0)

    st.altair_chart(timechart, use_container_width=True)



