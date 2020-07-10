import numpy as np

from base import BaseDecider


class SimpleAverage(BaseDecider):
    """
    Doc string here.
    """

    def __init__(self, classes = []):
        self.classes = classes

    def fit(self, y, transformer_id_to_transformers, classes = None, transformer_id_to_voters = None, X=None):
        self.classes = self.classes if len(self.classes) > 0 else np.unique(y)
        self.transformer_id_to_transformers = transformer_id_to_transformers
        self.transformer_id_to_voters = transformer_id_to_voters
        return self

    def predict(self, X, transformer_ids = None):
        vote_per_transformer_id = []
        for transformer_id in transformer_ids if transformer_ids else self.transformer_id_to_voters.keys():
            vote_per_bag_id = []
            for bag_id in range(len(self.transformer_id_to_transformers[transformer_id])):
                transformer = self.transformer_id_to_transformers[transformer_id][bag_id]
                X_transformed = transformer.transform(X)
                voter = self.transformer_id_to_voters[transformer_id][bag_id]
                vote = voter.vote(X_transformed)
                vote_per_bag_id.append(vote)
            vote_per_transformer_id.append(np.mean(vote_per_bag_id, axis = 0))
        vote_overall = np.mean(vote_per_transformer_id, axis = 0)
        return self.classes[np.argmax(vote_overall, axis=1)]