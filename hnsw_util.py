#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright (C) 2018 Li Chang
import os

import hnswlib
from gensim.models.doc2vec import Doc2Vec
from gensim.models.word2vec import Word2Vec
from smart_open import smart_open

try:
    import cPickle as _pickle
except ImportError:
    import pickle as _pickle


class HnswIndexer(object):

    def __init__(self, model=None):
        self.index = None
        self.labels = None
        self.model = model

        if model:
            if isinstance(self.model, Doc2Vec):
                self.build_from_doc2vec()
            elif isinstance(self.model, Word2Vec):
                self.build_from_word2vec()
            else:
                raise ValueError("Only a Word2Vec or Doc2Vec instance can be used")

    def save(self, fname, protocol=2):
        fname_dict = fname + '.d'
        self.index.save_index(fname)
        d = {'f': self.model.vector_size, 'labels': self.labels}
        with smart_open(fname_dict, 'wb') as fout:
            _pickle.dump(d, fout, protocol=protocol)

    def load(self, fname):
        fname_dict = fname+'.d'
        if not (os.path.exists(fname) and os.path.exists(fname_dict)):
            raise IOError(
                "Can't find index files '%s' and '%s' - Unable to restore HnswIndexer state." % (fname, fname_dict))
        else:
            with smart_open(fname_dict) as f:
                d = _pickle.loads(f.read())
            self.index = hnswlib.Index(space='cosine', dim=200)
            self.index.load_index(fname)
            self.index.set_ef(10000)
            self.labels = d['labels']

    def build_from_word2vec(self):
        """Build an Annoy index using word vectors from a Word2Vec model"""

        self.model.init_sims()
        return self._build_from_model(self.model.wv.syn0norm, self.model.index2word
                                      , self.model.vector_size)

    def build_from_doc2vec(self):
        """Build an hnsw index using document vectors from a Doc2Vec model"""

        docvecs = self.model.docvecs
        docvecs.init_sims()
        labels = [docvecs.index_to_doctag(i) for i in range(0, docvecs.count)]
        return self._build_from_model(docvecs.doctag_syn0norm, labels, self.model.vector_size)

    def _build_from_model(self, vectors, labels, num_features):
        index = hnswlib.Index(space='cosine', dim=200)
        index.init_index(max_elements=25000000, ef_construction=2000, M=64)
        index.add_items(vectors)
        self.index = index
        self.labels = labels

    def set_ef(self, ef):
        self.index.set_ef(ef)

    def most_similar(self, vector, num_neighbors):
        """Find the top-N most similar items"""
        ids, distances = self.index.knn_query(vector, k=num_neighbors)
        
        return [(self.labels[ids[0][i]], 1 - distances[0][i] / 2) for i in range(len(ids[0]))]
