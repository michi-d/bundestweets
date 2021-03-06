# Bundestweets

Source code for the **Bundestweets** project, a social media explorer for tweets from the German Bundestag (Parliament)(www.bundestweets.de).
 
## scrape_tweets.py

Simple command-line tool for scraping tweets from the German Bundestag.

The Twitter API has strict limits on the rate of requests, rendering it difficult to scrape an interesting and large enough dataset for NLP research. Other tools (e.g. https://github.com/bisguzar/twitter-scraper) provide workarounds which avoid interaction with the API by scraping the frontend. These approaches, however, are limited to tweets from within the last 6 or 7 months. 

The script **scrape_tweets.py** uses GetOldTweets3 to retrieve historical tweets without a date limit, and implements dynamic waiting times, based on the number of tweets received, to stay below the Twitter API rate limit.

The script is meant to be run in the background over extended time periods to establish a large database comprising all tweets from the German Bundestag over the last three years.

### Usage

To start scraping with default parameters run
    
`python scrape_tweets.py`

Options:

    --start_index INT    Index to start from when program was interrupted previously (total 734 members as of 2020)
    
    --since_date STR     Scrape all tweets from this day until now.  
    
    --file STR           Filename of the SQL database
    
    --do_fresh_download  Boolean, 1 or 0, indicating whether it is necessary to download list of members or not.

For example, to scrape all tweets since March 2020 to an SQL file *example.db* use

`python scrape_tweets.py --since_date 2020-03-01 --file example.db`

If the program had to be interrupted, e.g. at index 42, it can easily take up where it left off using

`python scrape_tweets.py --start_index 42`

The option **do_fresh_download** has to be set to 1 for the first execution of the program. 

`python scrape_tweets.py --do_fresh_download 1`

For later executions, a data file containing a list of members of the Bundestag will be available on disk.

### Installation

After downloading the repository run 

`pip install -r requirements.txt`
