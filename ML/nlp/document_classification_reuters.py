#!/usr/bin/env python

"""Train a document classifier."""

from nltk.corpus import reuters
from collections import defaultdict
import numpy as np
from sklearn.ensemble import RandomForestClassifier


def get_termfrequency_vector(word2wid, wordlist):
    """
    Calculate the term frequency vector.

    Parameters
    ----------
    word2wid : dict
        Map a word to a unique ID (0, ..., |vocabulary|)
    wordlist : list of str

    Returns
    -------
    termfrequency vector : list of ints
        List has the same length as vocabulary
    """
    document_tf_vector = [0 for term in range(len(word2wid))]
    for w in wordlist:
        if w not in word2wid:
            continue
        document_tf_vector[word2wid[w]] += 1
    return document_tf_vector


def get_x(document_id, word2wid):
    """
    Get the feature vector of a document.

    Parameters
    ----------
    document_id : int
    word2wid : dict

    Returns
    -------
    list of int
    """
    word_list = list(reuters.words(document_id))
    document_tf_vec = get_termfrequency_vector(word2wid, word_list)
    return document_tf_vec


def get_y(document_id, id2cats, cat2catid):
    """
    Get the label vector of a document.

    Parameters
    ----------
    document_id : int
    id2cats : list of str
    cat2catid : dict (str => int)

    Returns
    -------
    list of int
        Each element is either 0 or 1
    """
    y = [0 for i in range(len(cat2catid))]
    for cat in id2cats[document_id]:
        y[cat2catid[cat]] = 1
    return y


def main(categories, document_ids):
    """
    Train a classifier for a dataset.

    Parameters
    ----------
    categories : list of str
    document_ids : list of str
    """
    print("categories: {}".format(categories))
    print("number of categories: {}".format(len(categories)))
    cat2catid = {}
    for catid, cat in enumerate(sorted(categories)):
        cat2catid[cat] = catid

    documents = document_ids
    test = [d for d in documents if d.startswith('test/')]
    train = [d for d in documents if d.startswith('training/')]
    print("train documents: {}".format(len(train)))
    print("test documents: {}".format(len(test)))

    # make it easy to map data to label
    # gather simple statistics
    id2cats = defaultdict(list)
    cat2count = {}
    for cat in categories:
        for fid in reuters.fileids(cat):
            id2cats[fid].append(cat)
            if cat not in cat2count:
                cat2count[cat] = {'train': 0, 'test': 0, 'words': []}
            if fid in train:
                cat2count[cat]['train'] += 1
            else:
                cat2count[cat]['test'] += 1
            cat2count[cat]['words'].append(len(reuters.words(fid)))

    # Analyze data distribution to classes
    i = 1
    most_frequent_words = sorted(cat2count.items(),
                                 key=lambda n: n[1]['train'],
                                 reverse=True)
    for el in most_frequent_words:
        cat = el[0]
        print("\t{:>2}: {:<20}: {:>4}\t{:>4}\t{:0.1f}"
              .format(i, cat,
                      cat2count[cat]['train'],
                      cat2count[cat]['test'],
                      np.array(cat2count[cat]['words']).mean()))
        i += 1

    # Build corpus
    corpus = []
    for document_id in train:
        corpus += list(reuters.words(document_id))

    word2count = defaultdict(int)
    for word in corpus:
        word2count[word] += 1

    most_freq = sorted(word2count.items(), key=lambda n: n[1], reverse=True)
    for i, el in enumerate(most_freq[:10]):
        print("{}. frequent word is {} ({} occurences)"
              .format(i, el[0], el[1]))

    # Create vocabulary
    min_occurences = 5
    max_occurences = 12672
    vocabulary = [word[0]
                  for word in word2count.items()
                  if word[1] >= min_occurences and word[1] <= max_occurences]

    # Analyze the vocabulary
    print("vocabulary size = {}".format(len(vocabulary)))

    word2wid = {}
    vocabulary = list(vocabulary)
    for wid, word in enumerate(vocabulary):
        word2wid[word] = wid
    print("Created word2wid")

    # corpus_termfrequency_vector = get_termfrequency_vector(word2wid, corpus)

    # Calculate feature vectors
    xs = {'train': [], 'test': []}
    ys = {'train': [], 'test': []}
    for set_name, set_document_ids in [('test', test), ('train', train)]:
        print("Start with {}".format(set_name))
        for document_id in set_document_ids:
            x = get_x(document_id, word2wid)
            xs[set_name].append(x)
            y = get_y(document_id, id2cats, cat2catid)
            ys[set_name].append(y)
        xs[set_name] = np.array(xs[set_name])
        ys[set_name] = np.array(ys[set_name])

    classifier = RandomForestClassifier()
    print("Start fitting the RandomForestClassifier")
    classifier.fit(xs['train'], ys['train'])
    score = classifier.score(xs['test'], ys['test'])
    print(score)

if __name__ == '__main__':
    main(reuters.categories(), reuters.fileids())