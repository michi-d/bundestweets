"""NLP module:
Functions for content-based analysis.
"""

import nltk
nltk.download('punkt')
nltk.download('stopwords')

from nltk.corpus import stopwords
from nltk.tokenize import TweetTokenizer
from nltk.tokenize import word_tokenize
from bundestweets.cistem import stem
import re

from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.decomposition import NMF

from collections import defaultdict
import pandas as pd
import numpy as np
import os

party2id = {'CDU/CSU': 0,
            'Die Linke': 1,
            'FDP': 2,
            'SPD': 3,
            'Bündnis 90/Die Grünen': 4,
            'AfD': 5,
            'fraktionslos': 6}

id2party = {v: k for (k,v) in party2id.items()}


def clean_and_stem_tweet(text):
    """Cleans and stems the text of a tweet.
    
    Args:
        text: Input string
        
    Returns:
        text_stemmed: Stemmed version of the input
        text_cleaned: Cleaned version of the input (but not stemmed)
    """
    
    # download German stop words
    stop_words = set(stopwords.words("german"))
    
    # add party names to stop words (too inform)
    stop_words = stop_words.union({'CDU', 'CDU/CSU', 'CSU', 'SPD', 'Grüne', 'Grünen', 'LINKE', 'LINKEN'
                                   'linke', 'linken', 'AfD', 'afd', 'AFD', 'Afd', 'cdu', 'csu', 'cdu/csu',
                                   'grüne', 'grünen', 'Linke', 'Linken', 'FDP', 'fdp', 'GRÜNE', 'GRÜNEN'})
    
    ### clean text
    # remove whitespace
    RE_WSPACE = re.compile(r"\s+", re.IGNORECASE) 
    # remove html tags
    RE_TAGS = re.compile(r"<[^>]+>")
    # remove special characters
    RE_ASCII = re.compile(r"[^A-Za-zÀ-ž0-9#@*_ ]", re.IGNORECASE) 
    # remove special characters
    RE_SINGLECHAR = re.compile(r"\b[A-Za-zÀ-ž]\b", re.IGNORECASE)
    # remove mentions
    RE_MENTIONS = re.compile(r"(@[A-Za-z0-9À-ž*_]+)", re.IGNORECASE)
    # remove hashtags
    RE_HASHTAGS = re.compile(r"(#[A-Za-z0-9À-ž*_]+)", re.IGNORECASE)
    # remove URLs
    RE_URL = re.compile(r'\w+:\/{2}[\d\w-]+(\.[\d\w-]+)*(?:(?:\/[^\s/]*))*', re.IGNORECASE)

    text = re.sub(RE_URL, '', text)
    text = re.sub(RE_TAGS, " ", text)
    text = re.sub(RE_ASCII, " ", text)
    text = re.sub(RE_SINGLECHAR, " ", text)
    text = re.sub(RE_WSPACE, " ", text)
    text = re.sub(RE_MENTIONS, " ", text)
    text = re.sub(RE_HASHTAGS, " ", text)

    # tokenize
    tknzr = TweetTokenizer()
    text = tknzr.tokenize(text)

    # remove words which have only 1 or 3 characters (mostly acronyms)
    text_cleaned = [word for word in text if ((word not in stop_words) and 
                                               (len(word)>3))]
    # stem with cistem
    text_stemmed = " ".join([stem(word) for word in text_cleaned])
    
    text_cleaned = " ".join(text_cleaned)
    
    return text_stemmed, text_cleaned


def get_translation_set(data):
    """Given a dataset with columns "text_stemmed" and "text_cleaned",
    builds a dictionary for translation of stemmed word roots into the
    original words.
    
    Args:
        data: Pre-prossed data
    
    Returns:
        translation_set: Dictionary for translation
    """
    translation_set = defaultdict(lambda: defaultdict(int))
    for i, row in data.iterrows():
        for (k,v) in zip(row.text_stemmed.split(), row.text_cleaned.split()):
            translation_set[k][v] += 1
    return translation_set


def preprocess_for_nlp(data):
    """Pre-processes data for NLP functionality:
    Cleans text column and performs stemming and vectorization.
    Works IN PLACE on the data.
    
    Args:
        data: Tweet dataset
        
    Returns: 
        data: Pre-processed dataset
        translation_set: Dictionary mapping from word stems to originals
    """
    
    #data.date = pd.to_datetime(data.date, format='%Y-%m-%d-%H-%M-%S')

    # delete NaN entries (only a few)
    mask_na = data.id.isna()
    data = data.loc[~mask_na, :]

    # clean and stem text data
    data["text_stemmed"], data["text_cleaned"] = zip(
        *data["text"].map(lambda x: clean_and_stem_tweet(x) if isinstance(x, str) else x)
    )
    
    # generate dictionary from translation from word stems to originals
    translation_set = get_translation_set(data)

    return data, translation_set

    
def count_vectorize(x_train, x_test):
    '''Apply sklearn CountVectorizer to train and test data.
    '''
    
    vectorizer = CountVectorizer(max_features=30000, min_df=50, max_df=0.90, tokenizer=str.split, ngram_range=(1,1))

    # prevent data leakage: fit on train set, transform only on test set
    x_train = vectorizer.fit_transform(x_train)
    x_test  = vectorizer.transform(x_test)
    
    return x_train, x_test, vectorizer
    
    
def tfidf_vectorize(x_train, x_test):
    '''Apply sklearn TfidfVectorizer to train and test data.
    '''
    
    vectorizer = TfidfVectorizer(analyzer="word", max_df=0.90, min_df=50, norm="l2", tokenizer=str.split, lowercase=False,
                                ngram_range=(1,1))

    # prevent data leakage: fit on train set, transform only on test set
    x_train = vectorizer.fit_transform(x_train)
    x_test = vectorizer.transform(x_test)
    
    return x_train, x_test, vectorizer


def perform_party_regression_analysis(data, verbose=0):
    """Use logistic regression to perform party classification based on tweet content.
    
    Args:
        data: Pre-processed dataset
        
    Returns:
        model: Fitted model
        vectorizer: Fitted vectorizer
        train_acc: Train accuracy
        test_acc: Test accuracy
    """
    
    # generate label-encoded column for party affiliation
    data["party_id"] = data["party"].map(
        lambda x: party2id[x]
    )
    
    # split
    x_train, x_test, y_train, y_test = train_test_split(data['text_stemmed'], data['party_id'], test_size=0.05, random_state=42)

    # vectorize
    x_train, x_test, vectorizer = tfidf_vectorize(x_train, x_test)
    if verbose:
        print(f"Working with {x_train.shape[0]} samples.")
        print(f"Working with {x_train.shape[1]} features.")
    
    # fit model
    model = LogisticRegression(random_state=0, C=0.1)
    if verbose:
        print(f"Fitting model ...")
    model.fit(x_train, y_train)

    y_test_pred = model.predict(x_test)
    test_acc = accuracy_score(y_test, y_test_pred)
    
    y_train_pred = model.predict(x_train)
    train_acc = accuracy_score(y_train, y_train_pred)
    
    if verbose:
        print(f'Train acccuracy: {train_acc}')
        print(f'Test acccuracy: {test_acc}')

    return model, vectorizer, train_acc, test_acc


def get_top_n_words_from_model(model, vectorizer, category, n, translation_set, stemming=True):
    """Get most important word coefficients and their values for a given category.
    
    Args:
        model: Fitted logistic regression model
        vectorizer: Fitted vectorizer
        category: Category in question
        n: Number of words to retrieve
        translation_set: Dictionary for translation of word stems into originals
        stemming: (bool) whether features are word stems or originals
    
    Returns:
        words: List of most important words.
        importance: Importance factors
    """
    
    # sort model coefficients and get n most important words with score
    index = party2id[category]
    topN_ind = model.coef_[index,:].argsort()[-n:][::-1]
    importance = [model.coef_[index, i] for i in topN_ind]
    words = [vectorizer.get_feature_names()[i] for i in topN_ind]
    
    if stemming:
        # if words are stemmed take the most frequent original word
        words_ = []
        for w in words:
            try:
                chosen_word = pd.Series(translation_set[w]).idxmax()
            except KeyError:
                # if word is not in translation set, take the stem instead (could happen for new words)
                chosen_word = w
            words_.append(chosen_word)
        words = words_
    
    return importance, words


def get_all_top_n_words(data, translation_set, n=40, verbose=0):
    """Get top N words for each party from dataset.
    
    Args:
        data: Pre-processed tweet dataset
        translation_set: Dictionary for translation word stems into originals
        n: How many words to get
        
    Returns:
        party_word_importance: A dictionary containing a dictionary mapping words
            to importance values for each party.
        train_acc: Train accuracy
        test_acc: Test accuracy
    """
    
    model, vectorizer, train_acc, test_acc = perform_party_regression_analysis(data, verbose=verbose)
    
    party_word_importance = dict()
    for party in party2id.keys():
        importance, words = get_top_n_words_from_model(model, vectorizer, party, n, translation_set, stemming=True)
        word_importance = {k:v for (k,v) in zip(words, importance)}
        party_word_importance[party] = word_importance
    
    return party_word_importance, train_acc, test_acc


def get_NMF_topics(model, feature_names, n_top_words, verbose=0):
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


def nmf_tokenizer(s):
    """Tokenize strings by splitting, but use only words longer than 2 characters"""
    return [w for w in s.split() if len(w)>2]


def perform_NMF_analysis(data, n_components=20, verbose=0):
    """
    Args:
        data: Input dataset
        n_components: Components parameter for NMF
        verbose: Whether to print intermediate results or not
        
    Returns:
        topics: Dictionary mapping topic ID to top 5 tokens
        tweet_topics: Topic for each tweet
    """

    vectorizer = TfidfVectorizer(analyzer="word", max_df=0.90, min_df=50, norm="l2", tokenizer=nmf_tokenizer, lowercase=True, ngram_range=(1,1))
    x_train = vectorizer.fit_transform(data['hashtags'])
    if verbose:
        print(f'Input matrix shape: {x_train.shape}')

    # run NMF
    clf = NMF(n_components=n_components, random_state=1, 
              alpha=.1, l1_ratio=0.0, verbose=True, beta_loss="frobenius", solver="mu")
    W1  = clf.fit_transform(x_train)
    H1  = clf.components_

    # get topics 
    tf_feature_names = vectorizer.get_feature_names()
    topics = get_NMF_topics(clf, tf_feature_names, n_top_words=5, verbose=verbose)
    
    # get topic for each tweet
    tweet_topics = W1.argmax(1)
    
    return topics, tweet_topics


def intersect_topics(topics, wordsets):
    """Find intersections between topics and tweet messages.
    Matches are counted by the number of words in both sets.
    
    Args:
        topics: Dictionary mapping topic ID's to key words
        wordsets: pandas.Series of tweet messages formatted as sets of words
        
    Returns:
        intersections: numpy.array indicating number of word intersections 
            for each tweet and topic
    """
    
    intersections = np.zeros((len(wordsets), len(topics)))
    for ind in range(len(topics)):
        selector = set(topics[ind])
        selector = {e.lower() for e in selector}

        # get intersection between selector and each tweet
        len_intersection = wordsets.apply(lambda row: len(row.intersection(selector)))

        # save length of intersection with each topic
        intersections[:, ind] = len_intersection

    return intersections