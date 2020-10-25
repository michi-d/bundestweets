#!/usr/bin/env python

"""Run BERT model for offensive language identification.
"""

import bundestweets.stats_helpers as stats_helpers
import bundestweets.nlp as my_nlp
import pandas as pd
import numpy as np
import os
import json
import tqdm
import argparse
import datetime

import bundestweets.bert as bert


parser = argparse.ArgumentParser()
parser.add_argument("file", help="Input file to preprocess")
args = parser.parse_args()


def main():
    
    # get raw data
    data = stats_helpers.get_raw_data(local=True, db_file=args.file)
    
    # run model on data
    bert_proba = bert.run_bert(data)
    
    # save results
    datestr = datetime.datetime.now().strftime(format='%Y-%m-%d_%H:%M')
    np.save(f'bert_proba_{datestr}.npy', bert_proba)


if __name__ == '__main__':
    main()

