    #!/usr/bin/env python

"""Home page shown when the user enters the application"""

import streamlit as st

def write(analysis):
    """Writes the start Page"""
    
    N_tweets = len(analysis['my_data'])
    st.write("""
    # **Bundestweets**
    *An interactive social media explorer for tweets from the German Bundestag*
    """)
    st.image('./pages/bundestweets.png', width=600)
    st.write("""
    Political communication is becoming increasingly digital and social media are becoming the main channels for 
    exerting influence on public opinion. The fact that opinions are being reverberated and amplified in digital 
    space is being recognized and exploited by a growing number of political actors of all sorts.
    For an individual, however, it is sometimes hard to maintain an overview and keep track with these developments.
    """)
    st.write(f"""
    The **Bundestweets** web app is an interactive tool for monitoring and exploring the Twitter activity
    of all members of the German Bundestag. It is based on a dataset comprising all tweets posted by the
    current delegates since the beginning of 2018. So far, we have collected **{N_tweets} tweets** and the dataset
    is **updated on a daily basis**. Apart from providing weekly and general statistics, the goal of this project
    is also to explore how **machine learning** can help reveal interesting patterns in political tweet data.
    We applied different techniques to analyze tweet content, identify most relevant topics, identify offensive 
    language and more. 
    All analyses presented here are re-computed everyday and therefore always based on the most recent dataset.
    
    Since this project is work in progress, suggestions, ideas, criticism and questions are always welcome, so please
    feel free to contact:
    
    [michaelsdrews@gmail.com](mailto:michaelsdrews@gmail.com)
    
    """)
    #html = f"<a href='http://www.google.de'><img src='./pages/bundestweets.png'></a>"
    #st.markdown(html, unsafe_allow_html=True)