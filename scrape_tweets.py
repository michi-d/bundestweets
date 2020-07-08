#!/usr/bin/env python

import os
import sys
import argparse
from tqdm import tqdm
from bundestweets import helpers
import pandas as pd
import time
import argparse


parser = argparse.ArgumentParser()

parser.add_argument("--start_index", type=int,
                    help="start index")
parser.add_argument("--since_date", type=str,
                    help="start date")
parser.add_argument("--file", type=str,
                    help="database filename")

args = parser.parse_args()


def main():
    
    start_index = 0
    since_date = '2018-01-01'
    filename = 'tweets_data.db'
    
    if args.start_index:
        start_index = int(args.start_index)
    if args.since_date:
        since_date = str(args.since_date)
    if args.file:
        filename = str(args.file)
        
    print(f"Scraping tweets since {since_date}")
    print(f"Saving to database {filename}")
   
    # get members of Bundestag
    members_bundestag = helpers.get_data_twitter_members(do_fresh_download=False)
    members_bundestag = pd.DataFrame(members_bundestag).T
  
    # create tweet database
    outfile = os.path.join('data', filename)
    helpers.create_tweet_database(outfile)
    
    # loop through all members and get all tweets from the last 2 years
    print(f'Start scraping from index {start_index}, username: {members_bundestag.iloc[start_index].screen_name}...')
    pbar = tqdm(total=members_bundestag.shape[0])
    pbar.update(start_index)
    tweets = []
    for index, member in members_bundestag.iterrows():
        user_name = member.screen_name

        if not pd.isna(user_name):
            user_tweets = helpers.get_tweets(user_name, since_date=since_date)
            user_tweets = [helpers.tweet_to_dict(t) for t in user_tweets]

            helpers.extend_tweet_database(user_tweets)

            # avoid twitter API rate limit
            time.sleep(len(user_tweets)*0.25)

        pbar.update(1)
    pbar.close()

if __name__ == '__main__':
    main()