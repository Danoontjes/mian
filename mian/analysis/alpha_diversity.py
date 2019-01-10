# ===========================================
# 
# mian Analysis Alpha/Beta Diversity Library
# @author: tbj128
#
# ===========================================

#
# Imports
#

#
# ======== R specific setup =========
#
import logging

import rpy2.robjects as robjects
import rpy2.rlike.container as rlc
from rpy2.robjects.packages import SignatureTranslatedAnonymousPackage

from mian.analysis.analysis_base import AnalysisBase
from mian.core.statistics import Statistics

from mian.model.otu_table import OTUTable

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AlphaDiversity(AnalysisBase):
    r = robjects.r

    #
    # ======== Main code begins =========
    #

    rcode = """
    
    alphaDiversity <- function(allOTUs, alphaType, alphaContext) {
        alphaDiv = diversity(allOTUs, index = alphaType)
        if (alphaContext == "evenness") {
            S <- specnumber(allOTUs)
            J <- alphaDiv/log(S)
            return(J)
        } else if (alphaContext == "speciesnumber") {
            S <- specnumber(allOTUs)
            return(S)
        } else {
            return(alphaDiv)
        }
    }
    
    """

    veganR = SignatureTranslatedAnonymousPackage(rcode, "veganR")

    def run(self, user_request):
        table = OTUTable(user_request.user_id, user_request.pid)

        # No OTUs should be excluded for diversity analysis
        otu_table, headers, sample_labels = table.get_table_after_filtering_and_aggregation(user_request)

        metadata_values = table.get_sample_metadata().get_metadata_column_table_order(sample_labels, user_request.catvar)
        sample_ids_to_metadata_map = table.get_sample_metadata().get_sample_id_to_metadata_map(user_request.catvar)

        return self.analyse(user_request, otu_table, headers, sample_labels, metadata_values, sample_ids_to_metadata_map)

    def analyse(self, user_request, otu_table, headers, sample_labels, metadata_values, sample_ids_to_metadata_map):
        logger.info("Starting Alpha Diversity analysis")

        # Creates an R-compatible dictionary of columns to vectors of column values WITHOUT headers
        allOTUs = []
        col = 0
        while col < len(otu_table[0]):
            colVals = []
            row = 0
            while row < len(otu_table):
                sampleID = sample_labels[row]
                if len(metadata_values) == 0 or sampleID in sample_ids_to_metadata_map:
                    colVals.append(otu_table[row][col])
                row += 1
            allOTUs.append((headers[col], robjects.FloatVector(colVals)))
            col += 1

        logger.info("After creating an R-compatible dictionary")

        od = rlc.OrdDict(allOTUs)
        dataf = robjects.DataFrame(od)

        alphaType = user_request.get_custom_attr("alphaType")
        alphaContext = user_request.get_custom_attr("alphaContext")
        statisticalTest = user_request.get_custom_attr("statisticalTest")

        logger.info("Before vegan alpha diversity")

        vals = self.veganR.alphaDiversity(dataf, alphaType, alphaContext)

        logger.info("After vegan alpha diversity")

        # Calculate the statistical p-value
        abundances = {}
        statsAbundances = {}
        i = 0
        while i < len(vals):
            obj = {}
            obj["s"] = str(sample_labels[i])
            obj["a"] = round(vals[i], 6)
            meta = metadata_values[i] if len(metadata_values) > 0 else "All"

            # Group the abundance values under the corresponding metadata values
            if meta in statsAbundances:
                statsAbundances[meta].append(vals[i])
                abundances[meta].append(obj)
            else:
                statsAbundances[meta] = [vals[i]]
                abundances[meta] = [obj]

            i += 1
        statistics = Statistics.getTtest(statsAbundances, statisticalTest)

        logger.info("After T-test")

        abundancesObj = {}
        abundancesObj["abundances"] = abundances
        abundancesObj["stats"] = statistics
        return abundancesObj
