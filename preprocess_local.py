#!/usr/bin/env python

"""Pre-processing routine for the tweet dataset.
Must be run once on the dataset before NLP functions can be used.
"""


import argparse
import bundestweets.stats_helpers as stats_helpers
import bundestweets.nlp as my_nlp
import sqlite3
import json
import bundestweets.bert as bert

parser = argparse.ArgumentParser()
parser.add_argument("file", help="Input file to preprocess")
args = parser.parse_args()


def main():
    
    # load data
    data = stats_helpers.get_raw_data(local=True, db_file=args.file)
    print(f'Pre-processing {len(data)} new tweets.')
    
    # preprocess
    print('Cleaning and stemming text data...')
    data, translation_set = my_nlp.preprocess_for_nlp(data)
    
    # save translation set
    #with open('bundestweets/data/translation_set.json', 'w+') as fp:
    #    json.dump(translation_set, fp)
        
    # run bert model for offensive language identification
    print('Running BERT model for offensive language identification...')
    bert_proba = bert.run_bert(data)
    data['offensive_proba'] = bert_proba[:, 1]
    
    # open database file and save preprocessed columns
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
    print("Uploading 'text_stemmed' column...")
    recordList = list(zip(data.text_stemmed, data.id.astype('int')))
    sqlite_update_query = """UPDATE tweets set text_stemmed = ? where id = ?"""
    cur.executemany(sqlite_update_query, recordList)
    conn.commit()

    # update columns "text_cleaned"
    print("Uploading 'text_cleaned' column...")
    recordList = list(zip(data.text_cleaned, data.id.astype('int')))
    sqlite_update_query = """UPDATE tweets set text_cleaned = ? where id = ?"""
    cur.executemany(sqlite_update_query, recordList)
    conn.commit()
    
    # generate column "offensive_proba"
    try:
        cur.execute('ALTER TABLE tweets ADD offensive_proba FLOAT CONSTRAINT d_offensive_zero DEFAULT 0;')
    except sqlite3.OperationalError:
        print('Column "offensive_proba" exists already.')
        
    # update columns "offensive_proba"
    print("Uploading 'offensive_proba' column...")
    recordList = list(zip(data.offensive_proba, data.id.astype('int')))
    sqlite_update_query = """UPDATE tweets set offensive_proba = ? where id = ?"""
    cur.executemany(sqlite_update_query, recordList)
    conn.commit()

    cur.close()
    conn.close()

    
if __name__ == '__main__':
    
    main()
