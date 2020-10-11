#!/usr/bin/env python

"""Dataset: General statistics"""

import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import datetime as datetime

import bundestweets.helpers as helpers
import bundestweets.vis_helpers as vis_helpers
import bundestweets.stats_helpers as stats_helpers
import bundestweets.nlp as my_nlp


def write(analysis):
    """Writes the Relations Page"""
    
    # get data
    my_data = analysis['my_data']
    translation_set = analysis['translation_set']
    
    st.write("""
    ## Language analysis
    
    How do the different parties differ from each other based on their tweets? Maybe you would expect them 
    to emphasize different political topics? Maybe also their choice of words is different from each other? 
    
    In order to address this questions, we trained an algorithm to predict the author's political party based on
    only the tweet content (without hashtags and after removing direct references to party names). If you read 400.000 
    tweets from the German Bundestag, would you be able to learn how to tell the party affiliation from a tweet? 
    Probably not in all cases. But you might recognize certain patterns, certain words, certain topics, which appear to
    be more connected to one party than to the other parties.
    
    Consider the following two examples:
    
    **Tweet A**:
    _Gute Wahl kann man da nur sagen! Herzlichen Glückwunsch zu dieser tollen Aufgabe!_
    
    **Tweet B**:
    _Recht auf #Homeoffie ? Dann auch Recht auf Betreuungsplatz außerhalb der Familie #KiTa. Sonst bleibt es bei der
    Retraditionalisierung die #Frauen zur Zeit erfahren. Auch meine Befürchtung. 
    Brauchen neuen #Gesellschaftsvertrag #CareRevolution_
    
    Could you guess the author's party here? Tweet A is very difficult. But for Tweet B, we could guess that the author 
    most likely belongs to one of the left-wing parties. This is exactly what our algorithm is trying to do. 
    We don't expect it succeed in all cases since the task is difficult. But it might discover words which are indicative for 
    certain political topics, like here for example gender equality and women's rights, and identify parties are more 
    likely to mention those words. Rather than solving the party classification task perfectly, we are more 
    interested in the features that the computer learns!
    
    Let's see what our algorithm discovers! You can select a subset of the tweet dataset based on time and run this 
    analysis online. We will arrange the most predictive words for each party in word clouds for you. The large words are 
    the most characteristic ones for each party. But also look at the smaller ones. It is quite interesting too look 
    at the full language profile for each of the parties.
    """)

    # set default start and end times
    start_datetime = datetime.datetime.strptime('2018/01/01', '%Y/%M/%d')
    end_datetime = datetime.datetime.today()
    
    # select date range widget
    st.write("""
    ### Choose time frame:
    """)
    start_date = st.date_input('Start date', start_datetime)
    end_date = st.date_input('End date', end_datetime)
    
    # convert back to datetime
    start_datetime = datetime.datetime(year=start_date.year, month=start_date.month, day=start_date.day)
    end_datetime = datetime.datetime(year=end_date.year, month=end_date.month, day=end_date.day)

    # subset on selected time span
    mask = ((my_data.date >= start_datetime) & (my_data.date <= end_datetime))
    data_subset = my_data.loc[mask, :]
    
    # show number of tweets selected
    if start_date < end_date:
        st.success(f'{len(data_subset)} tweets selected.')
    else:
        st.error('Error: End date must fall after start date.')
        
    # run analysis
    if st.button('Train the algorithm and show results!'):
        
        # get word importance scores per party
        party_word_importance, train_acc, test_acc = my_nlp.get_all_top_n_words(data_subset, translation_set, n=40, verbose=1)
        
        st.write(f"""Model accuracy: {test_acc*100:.2f}% / Chance level: {1/7*100:.2f}%
        """)

        # show word clouds
        for party in my_nlp.party2id.keys():
            wordcloud = vis_helpers.create_word_cloud(party_word_importance, party)
            
            fig = plt.figure(figsize=(10,5))
            plt.imshow(wordcloud, interpolation="bilinear")
            plt.axis("off")
            plt.title(f"{party}", fontsize=20)
            st.pyplot(fig)