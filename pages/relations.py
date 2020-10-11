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

def write(analysis):
    """Writes the Relations Page"""
    
    # get data
    my_data = analysis['my_data']
    
    st.write("""
    ## Relations
    """)
    
    ## Chord diagram
    responses_count = vis_helpers.get_responses_count(my_data)
    chord_diagram = vis_helpers.generate_chord_diagram(responses_count)

    st.write(render(chord_diagram, backend='bokeh'))



