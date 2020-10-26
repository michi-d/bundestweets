#!/usr/bin/env python

"""
   scrape_tweets:
   -------------------------------------------------------------------------------------------
   Simple command-line helper tool to generate the basic tweet database.
   First, gets a list of all members from the German Bundestag. Then loops through all members 
   and dowloads all tweets since a given start date.

Usage:
    python scrape_tweets.py

Options:
    --start_index INT    Index to start from when program was interrupted previously (total 734 members as of 2020)
    --since_date STR     Scrape all tweets from this day until now (e.g., '2018-01-01').
    --file STR           Filename of the SQL database
    --do_fresh_download  Boolean, 1 or 0, indicating whether it is necessary to download list of members or not.
"""


import os
import sys
import argparse
from tqdm import tqdm
from bundestweets import helpers
import pandas as pd
import time
import argparse


parser = argparse.ArgumentParser()
parser.add_argument("--start_index", type=int, default=0,
                    help="Start index (734 member of the Bundestag).")
parser.add_argument("--since_date", type=str, default='2018-01-01',
                    help="Scrape tweets from this date until now.")
parser.add_argument("--file", type=str, default='tweets_data.db',
                    help="Filename of the SQL database.")
parser.add_argument("--do_fresh_download", type=int, default=0,
                    help="Indicates whether it is necessary to download list of members or not.")
args = parser.parse_args()

def main():
    '''Main loop 
    '''
    
    start_index = int(args.start_index)
    since_date = str(args.since_date)
    filename = str(args.file)
    do_fresh_download = bool(args.do_fresh_download)
    
    print(f"Scraping tweets since {since_date}")
    print(f"Saving to database {filename}")
   
    # get members of Bundestag and match them to twitter accounts
    members_bundestag = helpers.get_data_twitter_members(do_fresh_download=do_fresh_download)
    members_bundestag = pd.DataFrame(members_bundestag).T
  
    # create tweet database
    helpers.create_tweet_database(filename)
    
    # loop through all members and get all tweets since "since_date"
    print(f'Start scraping from index {start_index}, username: {members_bundestag.iloc[start_index].screen_name}...')
    
    pbar = tqdm(total=members_bundestag.shape[0])
    tweets = []
    for index, member in members_bundestag.iterrows():
        user_name = member.screen_name
        
        if int(index) >= start_index: # jump to start_index
            
            if not pd.isna(user_name):
                try:
                    # OLD code using GetOldTweets3 (not working since Sept 2020)
                    #user_tweets = helpers.get_tweets(user_name, since_date=since_date)
                    #user_tweets = [helpers.tweet_to_dict(t) for t in user_tweets]
                    
                    # NEW code using snscrape and tweepy (necessary since Sept 2020)
                    user_tweets = helpers.get_tweets_snscrape(user_name, since_date=since_date)
                    user_tweets = helpers.complete_tweets_snscrape(user_tweets, wait_time=300.0)

                    helpers.extend_tweet_database(user_tweets, filename=filename)

                    # avoid twitter API rate limit
                    #time.sleep(len(user_tweets)*0.25)
                    #time.sleep(len(user_tweets)*4.0)

                except:
                    e = sys.exc_info()[0]
                    print(e)
                    print(f'Error occurred at index {index}')
                    sys.exit()

        pbar.update(1)
    pbar.close()

    
if __name__ == '__main__':
    main()
