#!/usr/bin/env python

"""Script for integrating a local file into the Cloud MySQL server.
"""
import argparse
import bundestweets.helpers as helpers
import bundestweets.stats_helpers as stats_helpers
import os

parser = argparse.ArgumentParser()
parser.add_argument("file", help="Input file to preprocess")
args = parser.parse_args()


def main():
    
    # load local file (already pre-processed)
    new_tweets = stats_helpers.get_raw_data(local=True, db_file=args.file)
    
    # upload into cloud
    DB_PASS = os.environ.get('DB_PASS', '')
    helpers.cloud_upload_local_to_tweet_database(new_tweets, pw=DB_PASS)


if __name__ == '__main__':
    
    main()

