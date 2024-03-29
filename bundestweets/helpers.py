
"""Some helper functions for the bundestweets project."""

__author__ = "Michael Drews"
__copyright__ = "Copyright 2020, Michael Drews"
__email__ = "michaelsdrews@gmail.com"

import GetOldTweets3 as got
import tweepy
import bs4
import datetime
import time
import os
import re
import unidecode
import json
import pandas as pd
import sqlite3
import tqdm
import pymysql

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

import snscrape.modules.twitter as sntwitter


def get_tweets(username, since_date='2018-01-01', until_date='now'):
    '''Get all tweets from a user in a given time interval.

    Args:
        username (str): Username
        since_date (str): The start date of the interval
        until_date (str): The end date

    Returns:
        tweets: List of GetOldTweets3.models.Tweet.Tweet objects
    '''

    if until_date == 'now':
        until_date = datetime.datetime.now().strftime('%Y-%m-%d')

    # Creation of query object
    tweetCriteria = got.manager.TweetCriteria().setUsername(username) \
        .setSince(since_date).setUntil(until_date).setTopTweets(False)

    # Creation of list that contains all tweets
    tweets = got.manager.TweetManager.getTweets(tweetCriteria)

    return tweets


def tweet_to_dict(tweet):
    '''Transforms a GetOldTweets3-Tweet object to dictionary

    Args:
        tweet: GetOldTweets3.models.Tweet.Tweet object

    Returns:
        tweet_dict: Dictionary representation of the Tweet object
    '''

    tweet_dict = {
        'id': tweet.id,
        'permalink': tweet.permalink,
        'username': tweet.username,
        'to': tweet.to,
        'text': tweet.text,
        'date': tweet.date.strftime('%Y-%m-%d-%H-%M-%S'),
        'retweets': tweet.retweets,
        'favorites': tweet.favorites,
        'mentions': tweet.mentions,
        'hashtags': tweet.hashtags,
        'geo': tweet.geo
    }

    return tweet_dict


def get_API():
    '''Gets the Twitter API and authenticates with the App "getMdBList".

    Returns:
        api: Twitter API
    '''

    # read acess key from external file
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(dir_path, 'app_data')
    with open(file_path, "r") as f:
        consumer_key = f.readline().splitlines()[0]
        consumer_secret = f.readline().splitlines()[0]

    auth = tweepy.AppAuthHandler(consumer_key, consumer_secret)
    api = tweepy.API(auth, wait_on_rate_limit_notify=True)

    return api


def get_tweets_snscrape(username, since_date='2018-01-01', until_date='now'):
    '''Get all tweets from a user in a given time interval.
    (Using snscrape module necessary since Sept 2020)
    
    Args:
        username (str): Username
        since_date (str): The start date of the interval
        until_date (str): The end date
    
    Returns:
        tweets: List of GetOldTweets3.models.Tweet.Tweet objects
    '''
    
    if until_date == 'now':
        until_date = datetime.datetime.now().strftime('%Y-%m-%d')
        
    tweet_list = []
    query = sntwitter.TwitterSearchScraper(f'from:{username} since:{since_date} until:{until_date}')
    for i, tweet in enumerate(query.get_items()):
        tweet_list.append(tweet)
        
    return tweet_list


def complete_tweets_snscrape(tweet_list, wait_time=10.0):
    """Get missing data via Tweepy API and formats tweets in the old output format.
    (Using snscrape module necessary since Sept 2020)
    
    Args:
        tweet_list: List of tweets from snscrape
        wait_time: How long to wait if rate limit is reached.
        
    Returns:
        dict_list: List tweets in dictionary format
    """
    
    # get tweepy API
    api = get_API()
    
    dict_list = []
    #for tweet in tweet_list:
    i = 0
    while i < len(tweet_list):
        try:
            tweet = tweet_list[i]
            id_ = tweet.id
            tweetFetched = api.get_status(id_)

            mentions = " ".join(re.findall(r'@\w+', tweet.content))
            hashtags = " ".join(re.findall(r'#\w+', tweet.content))

            tweet_dict = {
                'id': id_,
                'permalink': tweet.url,
                'username': tweet.username,
                'to': tweetFetched.in_reply_to_screen_name,
                'text': tweet.content,
                'date': tweet.date.strftime('%Y-%m-%d-%H-%M-%S'),
                'retweets': tweetFetched.retweet_count,
                'favorites': tweetFetched.favorite_count,
                'mentions': mentions,
                'hashtags': hashtags,
                'geo': tweetFetched.geo
            }
            
            dict_list.append(tweet_dict)
            i += 1
            
        except tweepy.error.RateLimitError:
            print(f'Twitter API Rate Limit reached. Waiting for {wait_time} seconds ...')
            time.sleep(wait_time)
            pass
        
    return dict_list


def retrieve_accounts_bundestag(api):
    '''Retrieves the members of the Twitter list "MdB (Bundestag)" by "wahl_beobachter"
    https://twitter.com/i/lists/912241909002833921

    Returns:
        members: List of members
    '''

    return list(tweepy.Cursor(api.list_members, list_id=912241909002833921).items())


def scrape_bundestag_website():
    '''Scrapes the Bundestag website and retrieves the HTML code of a list view of all members.

    Returns:
        soup: Beautiful Soup object with the HTML source code for the list view
    '''

    URL = "https://www.bundestag.de/abgeordnete"

    driver = webdriver.Safari()
    driver.maximize_window()
    driver.get(URL)

    # ensure list view button is clickable
    try:
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="mod525246"]/div[2]/header/div[2]/div/form/a')))
    except TimeoutException:
        print('Page timed out after 10 secs.')

    # click list view button
    python_button = driver.find_elements_by_xpath('//*[@id="mod525246"]/div[2]/header/div[2]/div/form/a')[0]
    python_button.click()

    # ensure everything is properly loaded
    time.sleep(2.5)

    # parse HTML
    soup = bs4.BeautifulSoup(driver.page_source, 'html5lib')
    driver.quit()

    return soup


def soup_to_members(soup):
    '''Retrieves the Bundestag members and their parties from the HTML page source code.

    Args:
        soup: BeautifulSoup object of the Bundestag website

    Returns:
        names: List of names of the Bundestag members
        party: List of party affiliations
    '''

    # go to corresponding div in the HTML page source code of the list view
    table = soup.find('div', attrs={'class': 'bt-2col col-xs-12'})

    # loop through all divs, get name and party for each person
    divs_person = table.find_all('div', attrs={'class': 'bt-teaser-person'})

    names = []
    party = []
    for div in divs_person:
        n = div.div.h3.text.strip()
        p = div.div.p.text.strip()

        # ausgeschieden / quitted
        if '*' in p:
            p = p.splitlines()[0] + ' *'
        # verstorben / deceased
        if '**' in p:
            p = p.splitlines()[0] + ' **'
        # Mandat abgelehnt / mandate rejected
        if '***' in p:
            p = p.splitlines()[0] + ' ***'

        names.append(n)
        party.append(p)

    return names, party


def deEmojify(text):
    '''Remove Emojis from a text.
    Source: https://stackoverflow.com/questions/33404752/removing-emojis-from-a-string-in-python

    Args:
        text: input string

    Returns:
        Emoji-free string
    '''

    regrex_pattern = re.compile(pattern="["
                                        u"\U0001F600-\U0001F64F"  # emoticons
                                        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                        u"\U0001F680-\U0001F6FF"  # transport & map symbols
                                        u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                                        "]+", flags=re.UNICODE)

    return regrex_pattern.sub(r'', text)


def tokenize_real_names(real_names):
    '''Splits real names into first and last names and standardizes them for comparison with twitter names.

    Args:
        real_names (list): List of real names formatted as LAST NAME, FIRST NAME

    Returns:
        all_names (list): List of tuples in format (first name, last name)
    '''

    all_first_names = []
    all_last_names = []
    for name in real_names:
        last_name, first_name = name.split(', ')

        # limit last name until first space
        last_name = last_name.split()[0].lower()
        last_name = unidecode.unidecode(last_name)

        # remove titles from first name
        first_name = first_name.replace('Dr', '').replace('Prof', '').replace('.', '').replace(' von', '')
        first_name = unidecode.unidecode(first_name)

        # limit first name until first space
        first_name = first_name.strip().split()[0].lower()

        all_first_names.append(first_name)
        all_last_names.append(last_name)

    # create name pairs and sort by first name
    # all_names = sorted(zip(all_first_names, all_last_names), key=lambda pair: pair[0])
    all_names = list(zip(all_first_names, all_last_names))

    return all_names


def standardize_twitter_names(twitter_names):
    '''Standardizes twitter names for comparison with real names.

    Args:
        twitter_names (list): List of twitter names

    Returns:
        standard_names (list): List of standardized names
    '''

    standard_names = []
    for name in twitter_names:
        name = name.replace('Dr', '').replace('Prof', '').replace('.', '').replace(' von', ''). \
            replace('MdB', '').replace('(', '').replace(')', '').replace(',', '').strip()
        name = deEmojify(name)
        name = unidecode.unidecode(name).lower()

        standard_names.append(name)

    return standard_names


def greedy_record_linkage_bundestag(names_bundestag, party_bundestag, accounts_bundestag):
    '''Compares all Twitter names to all real names and matches them. Assembles a dictionary containing
    all Twitter account information for each member of the Bundestag.

    Args:
        names_bundestag (list): List of real names formatted as LAST NAME, FIRST NAME
        party_bundestag (list): List of party affiliations
        accounts_bundestag (list): List of tweepy.models.User objects, Twitter user information

    Returns:
        members_bundestag (dict): Dictionary with a unique integer key for each person
    '''

    # extract first and last names from real names
    all_names = tokenize_real_names(names_bundestag)

    # extract names from twitter profiles
    twitter_names = list(map(lambda user: user.name, accounts_bundestag))

    # standardize twitter profile names
    twitter_names = standardize_twitter_names(twitter_names)

    # start greedy matching algorithm
    members_bundestag = dict()
    # iterate over all real names and look for matching twitter profile names
    for i_name, name in enumerate(all_names):
        member_info = {
            'real_name': names_bundestag[i_name],
            'party': party_bundestag[i_name]
        }
        first_name = all_names[i_name][0]
        last_name = all_names[i_name][1]

        # try to find twitter profile name for this person
        found = False
        i_acc = 0
        while not found:
            tw_name = twitter_names[i_acc]
            if (first_name in tw_name) and (last_name in tw_name):
                found = True
                member_info.update(accounts_bundestag[i_acc]._json)
            else:
                i_acc += 1
            if i_acc == len(accounts_bundestag):
                break

        members_bundestag[i_name] = member_info

    return members_bundestag


def get_data_twitter_members(do_fresh_download = True):
    '''Downloads or loads from file the Twitter account data for each member

    Args:
        do_fresh_download (bool): Whether or not to scrape the data from the internet

    Returns:
        members_bundestag (dict): Twitter account data for each member
    '''
    
    dir_path = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(dir_path, 'data', 'twitter_members.json')
    
    if not do_fresh_download:
        if not os.path.isfile(file_path):
            print("File does not exist, trying to download data...")
            do_fresh_download = True
        else:
            with open(file_path, 'r') as file:
                members_bundestag = json.load(file)
    
    if do_fresh_download:
        # get members and affiliations from the Bundestag
        soup = scrape_bundestag_website()
        names_bundestag, party_bundestag = soup_to_members(soup)

        # initialize Twitter API
        api = get_API()

        # get list of Bundestag members with Twitter accounts from https://twitter.com/i/lists/912241909002833921
        accounts_bundestag = retrieve_accounts_bundestag(api)

        # match Twitter accounts to real persons / link party affiliation
        members_bundestag = greedy_record_linkage_bundestag(names_bundestag, party_bundestag, accounts_bundestag)
        
        with open(file_path, 'w') as file:
            json.dump(members_bundestag, file)
        
    return members_bundestag


def create_tweet_database(filename="tweets_data.db"):
    '''Creates a SQL database for tweets

    Args:
        filename: Path to file for the database
    '''

    #dir_path = os.path.dirname(os.path.realpath(__file__))
    #file_path = os.path.join(dir_path, 'data', filename)

    conn = sqlite3.connect(filename)

    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS tweets ('
                'id INT PRIMARY KEY,'
                'permalink TEXT,'
                'username TEXT,'
                'resp_to TEXT,'
                'text TEXT,'
                'date TEXT,'
                'retweets INT,'
                'favorites INT,'
                'mentions TEXT,'
                'hashtags TEXT)')

    conn.close()


def extend_tweet_database(data, filename="tweets_data.db"):
    '''Extends the SQL Tweet database using new data.

    Args:
        data (list): List of new tweets to add
        filename: Path to file of the database file
    '''

    #dir_path = os.path.dirname(os.path.realpath(__file__))
    #file_path = os.path.join(dir_path, 'data', filename)

    conn = sqlite3.connect(filename)
    cur = conn.cursor()

    for tweet in data:
        cur.execute("""INSERT OR IGNORE INTO tweets(
                            id, 
                            permalink, 
                            username, 
                            resp_to, 
                            text, 
                            date, 
                            retweets, 
                            favorites, 
                            mentions, 
                            hashtags) 

                   VALUES (?,?,?,?,?,?,?,?,?,?);""", (
            tweet['id'],
            str(tweet['permalink']),
            str(tweet['username']),
            str(tweet['to']),
            str(tweet['text']),
            str(tweet['date']),
            tweet['retweets'],
            tweet['favorites'],
            str(tweet['mentions']),
            str(tweet['hashtags'])))

    conn.commit()
    conn.close()


def cloud_create_tweet_database(pw=None):
    """Creates tweet database on Google Cloud.
    Proxy must be running in the background.
    """
    # get password
    if not pw:
        password = input("Enter password:")
    else:
        password = pw
        
    # connect to MySQL server
    connection = pymysql.connect(host='127.0.0.1',
                                 user='root',
                                 password=password,
                                 db='tweets')
    cursor = connection.cursor()
    
    # create table
    cursor.execute('CREATE TABLE IF NOT EXISTS tweets ('
                   'id BIGINT PRIMARY KEY,'
                   'permalink TEXT,'
                   'username TEXT,'
                   'resp_to TEXT,'
                   'text TEXT,'
                   'text_stemmed TEXT,'
                   'text_cleaned TEXT,'
                   'date TEXT,'
                   'retweets INT,'
                   'favorites INT,'
                   'mentions TEXT,'
                   'hashtags TEXT,'
                   'offensive_proba FLOAT)')
    
    # describe
    cursor.execute('DESCRIBE tweets;')
    print('Output of: "DESCRIBE tweets;""')
    print(cursor.fetchall())
    
    # close connection
    cursor.close()
    connection.close()
    
    
def cloud_upload_local_to_tweet_database(data, pw=None):
    """Uploads a local PREPROCESSED dataset to the cloud.
    
    Args:
        data: Dataframe with preprocessed tweet dataset
    """
    # get password
    if not pw:
        password = input("Enter password:")
    else:
        password = pw
        
    # connect to MySQL server
    connection = pymysql.connect(host='127.0.0.1',
                                 user='root',
                                 password=password,
                                 db='tweets')
    cursor = connection.cursor()
    
    # upload each row of the dataset
    for i, tweet in tqdm.tqdm(data.iterrows()):
        cursor.execute("""INSERT IGNORE INTO tweets(
                        id, 
                        permalink, 
                        username, 
                        resp_to, 
                        text, 
                        text_stemmed, 
                        text_cleaned, 
                        date, 
                        retweets, 
                        favorites, 
                        mentions, 
                        hashtags,
                        offensive_proba) 

                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s);""", (

            str(tweet['id']),
            str(tweet['permalink']),
            str(tweet['screen_name']),
            str(tweet['resp_to']),
            str(tweet['text']),
            str(tweet['text_stemmed']),
            str(tweet['text_cleaned']),
            str(datetime.datetime.strftime(tweet.date, '%Y-%m-%d-%H-%M-%S')),
            tweet['retweets'],
            tweet['favorites'],
            str(tweet['mentions']),
            str(tweet['hashtags']),
            tweet['offensive_proba']))

        
    # commit changes
    connection.commit()
    
    # close connection
    cursor.close()
    connection.close()
    
    
def cloud_get_dataset():
    """Gets the dataset from Google MySQL
    
    Returns:
        data: DataFrame with tweet dataset
    """
    
    DB_HOST = os.environ.get('DB_HOST', '127.0.0.1')
    DB_NAME = os.environ.get('DB_NAME', '')
    DB_USER = os.environ.get('DB_USER', '')
    DB_PASS = os.environ.get('DB_PASS', '')
    
    print([DB_HOST, DB_NAME, DB_USER, DB_PASS])
        
    conn = pymysql.connect(host=DB_HOST,
                           user=DB_USER,
                           password=DB_PASS,
                           db=DB_NAME)
    
    with conn.cursor() as cursor:
        result = cursor.execute('SELECT * FROM tweets;')
        data = cursor.fetchall()
        data = pd.DataFrame(data)
            
    conn.close()
    
    data.columns = ['id', 'permalink', 'username', 'resp_to', 'text', 'text_stemmed', 
                    'text_cleaned', 'date', 'retweets', 'favorites', 'mentions', 
                    'hashtags', 'offensive_proba']
    
    return data