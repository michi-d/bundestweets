    #!/usr/bin/env python

"""Home page shown when the user enters the application"""

import streamlit as st

def write(analysis):
    """Writes the start Page"""
    
    st.write("""
    ## **Bundestweets**
    *An interactive social media explorer for tweets from the German Bundestag*
    """)
    st.image('./pages/bundestweets.png', width=600)
    st.write("""
    Political communication is becoming increasingly digital and social media are becoming the main channels for 
    exerting influence on public opinion. The fact that opinions are being reverberated and amplified in digital 
    space is being recognized and exploited by a growing number of political actors of all sorts.
    For an individual, however, it is sometimes hard to maintain an overview and keep track with these developments. 
    
    The **Bundestweets** project is an interactive tool for monitoring and exploring the Twitter activity
    of all members of the German Bundestag. It is based on a dataset comprising all tweets posted by the
    current delegates since the beginning of 2018. The dataset contains so far about ~500.000 tweets and 
    is being continuosly updated. So far, we analyzed content, language and the Twitter relationships 
    of the delegates among each other. New suggestions, ideas, critics and questions are always a welcome, 
    so please feel free to contact:
    
    [michaelsdrews@gmail.com](mailto:michaelsdrews@gmail.com)
    
    """)
    #html = f"<a href='http://www.google.de'><img src='./pages/bundestweets.png'></a>"
    #st.markdown(html, unsafe_allow_html=True)