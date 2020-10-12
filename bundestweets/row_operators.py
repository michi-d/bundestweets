"""
Collections of row-wise routines for tranformation and information extraction from pandas.DataFrames.
"""

def get_hashtags_as_list(row):
    """
    Get hashtags of a tweet as list.
    
    Args:
        row: row of the base DataFrame
        
    Returns:
        hashtags_list: list of str of hashtags
    """
    hashtags_list = row.hashtags.split(' ')
    #hashtags_list = [e[1:] for e in hashtags_list]
    return hashtags_list

def get_mentions_list(row, strip_at_sign=False):
    """
    Get mentions of a tweet as list.
    
    Args:
        row: row of the base DataFrame
        
        strip_at_sign (optional): whether to strip the '@' sign or not
    
    Returns:
        mentions_list: list of str of mentions
    """
    mentions_list = row.mentions.split(' ')
    if strip_at_sign:
        mentions_list = [e[1:] for e in mentions_list]
    return mentions_list

def get_mentioned_parliament_members(row, parliament_account_names):
    """
    Same of get_mentions_list. Yields only mentions of an existing account. 
    
    Args:
        row: row of the base DataFrame
        parliament_account_names (set): set of account names in the parliament
        
    Returns: 
        mentioned_members: list of str of mentions
    """
    assert type(parliament_account_names) == set
    
    mentions_set = set(get_mentions_list(row, strip_at_sign=True))
    mentioned_members = mentions_set.intersection(parliament_account_names)
    if len(mentioned_members) > 0:
        return list(mentioned_members)
    else:
        return None
    
def get_tweet_as_word_set(row):
    """Return tweet text as a set of words.
    
    Args:
        row: Row of the base DataFrame
        
    Returns:
        wordset: Tweet text as a set of words
    """
    wordset = set(row.text.lower().split())
    return wordset