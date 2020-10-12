#!/usr/bin/env python

"""
Run NMF analysis on dataset and save results
"""

import bundestweets.stats_helpers as stats_helpers
import bundestweets.nlp as my_nlp

import json
import argparse


# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("file", help="Input file to preprocess")
args = parser.parse_args()


def get_NMF_top_words(model, feature_names, n_top_words, verbose=0):
    """Return the top words for each topic.
    
    Args:
        model: Fitted NMF model
        feature_names: Names for each feature column
        n_top_words: Specifies how many words to return per topic
        verbose: Print results or not
        
    Returns:
        top_words: Dictionary with the top words for each topic
    """
    top_words = dict()
    for topic_idx, topic in enumerate(model.components_):
        words = [feature_names[i] for i in topic.argsort()[:-n_top_words - 1:-1]]
        top_words[topic_idx] = words
        
        if verbose:
            message = "Topic #%d: " % topic_idx
            message += " ".join(words)
            print(message)
            
    return top_words


def main():
    """Runs Non-negative Matrix Factorization (NMF) on the hashtag column of the dataset.
    """
    
    # get data
    data = stats_helpers.get_raw_data(db_file=args.file)
    
    # run NMF analysis
    topics, _ = my_nlp.perform_NMF_analysis(data, verbose=1)

    # save results
    with open('bundestweets/data/nmf_topics.json', 'w+') as fp:
        json.dump(topics, fp)


if __name__ == '__main__':
    main()
