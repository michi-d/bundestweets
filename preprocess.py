#!/usr/bin/env python

"""Pre-processing routine for the tweet dataset.
Must be run once on the dataset before NLP functions can be used.
"""


import argparse
import bundestweets.stats_helpers as stats_helpers
import bundestweets.nlp as my_nlp
import sqlite3


parser = argparse.ArgumentParser()
parser.add_argument("file", help="Input file to preprocess")
args = parser.parse_args()


def main():
    
    # load data
    data = stats_helpers.get_raw_data(db_file=args.file)
    
    # preprocess
    data, translation_set = my_nlp.preprocess_for_nlp(data)
    
    # open file
    conn = sqlite3.connect(args.file)
    cur = conn.cursor()

    # create new columns "text_stemmed" and "text_cleaned"
    try:
        cur.execute('ALTER TABLE tweets ADD text_stemmed TEXT;')
    except sqlite3.OperationalError:
        print('Column "text_stemmed" exists already.')
    try:
        cur.execute('ALTER TABLE tweets ADD text_cleaned TEXT;')
    except sqlite3.OperationalError:
        print('Column "text_cleaned" exists already.')
        
    # update columns "text_stemmed"
    recordList = list(zip(data.text_stemmed, data.id.astype('int')))
    sqlite_update_query = """UPDATE tweets set text_stemmed = ? where id = ?"""
    cur.executemany(sqlite_update_query, recordList)
    conn.commit()

    # update columns "text_cleaned"
    recordList = list(zip(data.text_cleaned, data.id.astype('int')))
    sqlite_update_query = """UPDATE tweets set text_cleaned = ? where id = ?"""
    cur.executemany(sqlite_update_query, recordList)
    conn.commit()

    cur.close()
    conn.close()

    
if __name__ == '__main__':
    
    main()
