# ===========================================
#
# mian Analysis Data Mining/ML Library
# @author: tbj128
#
# ===========================================

#
# Imports
#

import numpy as np
import pandas as pd
import rpy2.robjects as robjects
import rpy2.rlike.container as rlc
from boruta import BorutaPy
from rpy2.robjects.packages import SignatureTranslatedAnonymousPackage
import rpy2.robjects.numpy2ri
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import random

rpy2.robjects.numpy2ri.activate()

from mian.model.otu_table import OTUTable

class Boruta(object):

    def run(self, user_request):
        table = OTUTable(user_request.user_id, user_request.pid)
        otu_table, headers, sample_labels = table.get_table_after_filtering_and_aggregation_and_low_count_exclusion(user_request)

        metadata_values = table.get_sample_metadata().get_metadata_column_table_order(sample_labels, user_request.catvar)
        taxonomy_map = table.get_otu_metadata().get_taxonomy_map()

        return self.analyse(user_request, otu_table, headers, metadata_values, taxonomy_map)

    def analyse(self, user_request, otu_table, headers, meta_vals, taxonomy_map):
        # Subsample the input to match the training proportion
        # We do this because we want to generate the microbial fingerprint on the training set and
        # later independently test on a test set
        #
        seed = int(user_request.get_custom_attr("seed")) if user_request.get_custom_attr("seed") is not "" else random.randint(0, 100000)
        training_proportion = float(user_request.get_custom_attr("trainingProportion"))
        pval = float(user_request.get_custom_attr("pval"))
        maxruns = int(user_request.get_custom_attr("maxruns"))

        if training_proportion < 1:
            otu_table, _, meta_vals, _ = train_test_split(otu_table, meta_vals, train_size=training_proportion, random_state=seed)

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
            otu_table = otu_table.toarray()

        rf = RandomForestClassifier(n_jobs=-1, class_weight='balanced')
        feat_selector = BorutaPy(rf, n_estimators='auto', alpha=pval, max_iter=maxruns)
        feat_selector.fit(otu_table, meta_vals)

        assignments = {
            "Selected Features": [],
            "Tentatively Selected": []
        }
        hints = {}
        for i, selected in enumerate(feat_selector.support_.tolist()):
            if selected:
                feature = headers[i]
                assignments["Selected Features"].append(feature)
                if int(user_request.level) == -1:
                    hints[feature] = otu_to_genus[feature]
        for i, selected in enumerate(feat_selector.support_weak_.tolist()):
            if selected:
                feature = headers[i]
                assignments["Tentatively Selected"].append(feature)
                if int(user_request.level) == -1:
                    hints[feature] = otu_to_genus[feature]

        abundancesObj = {"results": assignments, "hints": hints, "seed": seed}

        return abundancesObj
