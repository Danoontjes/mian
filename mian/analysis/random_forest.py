# ===========================================
#
# mian Analysis Data Mining/ML Library
# @author: tbj128
#
# ===========================================

#
# Imports
#

from mian.model.otu_table import OTUTable
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
import numpy as np

class RandomForest(object):

    def run(self, user_request):
        table = OTUTable(user_request.user_id, user_request.pid)
        otu_table = table.get_table_after_filtering_and_aggregation(user_request.taxonomy_filter,
                                                                    user_request.taxonomy_filter_role,
                                                                    user_request.taxonomy_filter_vals,
                                                                    user_request.sample_filter,
                                                                    user_request.sample_filter_role,
                                                                    user_request.sample_filter_vals,
                                                                    user_request.level)

        metadata_vals = table.get_sample_metadata().get_metadata_column_table_order(otu_table, user_request.catvar)

        return self.analyse(user_request, otu_table, metadata_vals)

    def analyse(self, user_request, otu_table, metadata_vals):
        le = LabelEncoder()
        le.fit(metadata_vals)
        Y = le.transform(metadata_vals)

        X = np.array(otu_table[1:len(otu_table)])
        X = np.delete(X, 0, 1) # Deletes first sample ID column
        names = otu_table[0][1:]

        num_trees = int(user_request.get_custom_attr("numTrees"))
        max_depth = int(user_request.get_custom_attr("maxDepth")) if user_request.get_custom_attr("maxDepth") != "" else None

        rf = RandomForestRegressor(n_estimators=num_trees, max_depth=max_depth)
        fit = rf.fit(X, Y)

        rounded_importances = map(lambda x: round(x, 4), rf.feature_importances_)
        taxonomy_importance = sorted(zip(names, rounded_importances), reverse=True, key=lambda x: x[1])

        abundances_obj = {
            "results": taxonomy_importance,
            "cmd": str(fit),
        }

        return abundances_obj
