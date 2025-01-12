# ===========================================
#
# mian Analysis Data Mining/ML Library
# @author: tbj128
#
# ===========================================

#
# Imports
#
import pandas as pd
from sklearn.feature_selection import RFE
from sklearn.linear_model import SGDClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import normalize

from mian.model.otu_table import OTUTable
import numpy as np
import random


class ElasticNetSelectionClassification(object):

    def run(self, user_request):
        table = OTUTable(user_request.user_id, user_request.pid)
        otu_table, headers, sample_labels = table.get_table_after_filtering_and_aggregation_and_low_count_exclusion(user_request)

        metadata_vals = table.get_sample_metadata().get_metadata_column_table_order(sample_labels, user_request.catvar)
        taxonomy_map = table.get_otu_metadata().get_taxonomy_map()

        return self.analyse(user_request, otu_table, headers, metadata_vals, taxonomy_map)

    def analyse(self, user_request, otu_table, headers, metadata_vals, taxonomy_map):
        seed = int(user_request.get_custom_attr("seed")) if user_request.get_custom_attr("seed") is not "" else random.randint(0, 100000)
        training_proportion = float(user_request.get_custom_attr("trainingProportion"))
        mixing_ratio = float(user_request.get_custom_attr("mixingRatio"))
        loss_function = user_request.get_custom_attr("lossFunction")
        max_iterations = int(user_request.get_custom_attr("maxIterations"))
        keep = -1 if user_request.get_custom_attr("keep") == "" else int(user_request.get_custom_attr("keep"))

        otu_to_genus = {}
        if int(user_request.level) == -1:
            # We want to display a short hint for the OTU using the genus (column 5)
            for header in headers:
                if header in taxonomy_map and len(taxonomy_map[header]) > 5:
                    otu_to_genus[header] = taxonomy_map[header][5]
                else:
                    otu_to_genus[header] = ""

        if int(user_request.level) == -1:
            # OTU tables are returned as a CSR matrix
            X = pd.DataFrame.sparse.from_spmatrix(otu_table, columns=headers, index=range(otu_table.shape[0]))
        else:
            X = otu_table

        Y = np.array(metadata_vals)

        if training_proportion < 1:
            X, _, Y, _ = train_test_split(X, Y, train_size=training_proportion, random_state=seed)

        columns = np.array(headers)

        # https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0188475
        classifier = SGDClassifier(loss=loss_function, l1_ratio=mixing_ratio, max_iter=max_iterations)
        if keep == -1:
            selector = RFE(classifier, n_features_to_select=len(columns), step=1)
        else:
            selector = RFE(classifier, n_features_to_select=keep, step=1)

        selector = selector.fit(X, Y)

        columns = columns[selector.support_]

        feature_map = {}
        hints = {}
        if len(selector.classes_) <= 2:
            coef = pd.Series(selector.estimator_.coef_[0], index=columns)
            if keep == -1:
                features = columns[coef != 0]
                weights = coef[coef != 0].abs().sort_values(ascending=False).values
            else:
                features = coef.abs().sort_values(ascending=False).index
                weights = coef.abs().sort_values(ascending=False).values

            if int(user_request.level) == -1:
                for f in features:
                    hints[f] = otu_to_genus[f]

            key = selector.classes_[0]
            if len(selector.classes_) == 2:
                key += " vs " + selector.classes_[1]
            feature_map[key] = {
                "features": features.tolist(),
                "weights": weights.tolist()
            }
        else:
            for i in range(len(selector.classes_)):
                coef = pd.Series(selector.estimator_.coef_[i], index = columns)
                if keep == -1:
                    features = columns[coef != 0]
                    weights = coef[coef != 0].values
                else:
                    features = coef.abs().sort_values(ascending=False).index
                    weights = coef.abs().sort_values(ascending=False).values

                if int(user_request.level) == -1:
                    for f in features:
                        hints[f] = otu_to_genus[f]

                feature_map[selector.classes_[i]] = {
                    "features": features.tolist(),
                    "weights": weights.tolist()
                }

        abundances_obj = {}
        abundances_obj["feature_map"] = feature_map
        abundances_obj["hints"] = hints
        abundances_obj["seed"] = seed

        return abundances_obj
