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

from farm.infer import Inferencer

def main():
    
    save_dir = "./bert_model/"
    model = Inferencer.load(save_dir)
    
    # get raw data
    data = stats_helpers.get_raw_data(local=True, db_file='./bundestweets/data/tweets_data.db')
    
    # format data for model
    data_formatted = [{'text': v} for v in data['text'].values]
    
    # run model over dataset
    chunk_size = 64
    N_chunks = int(np.ceil(len(data_formatted) / chunk_size))
    results = []
    for c_i in tqdm.tqdm(range(N_chunks)):
        chunk = data_formatted[c_i*chunk_size : (c_i+1)*chunk_size]
        results.extend(model.run_inference(dicts=chunk))
        if c_i == 1:
            break
            
    # get probabilities
    bert_proba = []
    for r in results:
        for r_ in r['predictions']:
            p = r_['probability']
            if r_['label'] == 'OTHER':
                p = 1.0 - p
            bert_proba.append([1-p, p])
    bert_proba = np.array(bert_proba)
            
    # save results
    np.save('bert_proba.npy', bert_proba)


if __name__ == '__main__':
    main()

