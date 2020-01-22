// ============================================================
// Random Forest JS Component
// ============================================================

//
// Global Components
//
var tableResults = [];
var expVarToType = {};
var expectedLoadFactor = 500;
var cachedAbundancesObj = null;
var cachedTrainingIndexes = null;

//
// Initialization
//
initializeFields();
initializeComponent({
    hasCatVar: true,
    hasCatVarNoneOption: true
});
createSpecificListeners();

//
// Initializes fields based on the URL params
//
var initialExpVar = getParameterByName("expvar");
function initializeFields() {
    if (getParameterByName("mixingRatio") !== null) {
        $("#mixingRatio").val(getParameterByName("mixingRatio"));
    }

    if (getParameterByName("maxIterations") !== null) {
        $("#maxIterations").val(getParameterByName("maxIterations"));
    }

    if (getParameterByName("crossValidate") !== null) {
        $("#crossValidate").val(getParameterByName("crossValidate"));
        if ($("#crossValidate").val() === "full") {
            $("#trainingConfig").hide();
        } else {
            $("#trainingConfig").show();
        }
    }

    if (getParameterByName("crossValidateFolds") !== null) {
        $("#crossValidateFolds").val(getParameterByName("crossValidateFolds"));
    }

    if (getParameterByName("fixTraining") !== null) {
        $("#fixTraining").val(getParameterByName("fixTraining"));

        if ($("#fixTraining").val() === "yes") {
            $("#trainingProportion").prop("readonly", true);
        } else {
            $("#trainingProportion").prop("readonly", false);
        }
    }

    if (getParameterByName("trainingProportion") !== null) {
        $("#trainingProportion").val(getParameterByName("trainingProportion"));
    }

    if (getParameterByName("trainingIndexes") !== null) {
        cachedTrainingIndexes = JSON.parse(getParameterByName("trainingIndexes"));
    }

    if (getParameterByName("rocFor") !== null) {
        $("#rocFor").val(getParameterByName("rocFor"));
    }

    if (getParameterByName("ref") !== null) {
        $("#referral-alert").show();
        $("#referer-name").text(getParameterByName("ref"));
    }
}

//
// Component-Specific Sidebar Listeners
//
function createSpecificListeners() {
    $("#expvar").change(function() {
        updateAnalysis();
    });

    $("#mixingRatio").change(function() {
        updateAnalysis();
    });

    $("#crossValidate").change(function() {
        if ($("#crossValidate").val() === "full") {
            $("#trainingConfig").hide();
        } else {
            $("#trainingConfig").show();
        }
        updateAnalysis();
    });

    $("#crossValidateFolds").change(function() {
        updateAnalysis();
    });

    $("#maxIterations").change(function() {
        updateAnalysis();
    });

    $("#trainingProportion").change(function() {
        updateAnalysis();
    });

    $("#fixTraining").change(function() {
        if ($("#fixTraining").val() === "yes") {
            $("#trainingProportion").prop("readonly", true);
        } else {
            $("#trainingProportion").prop("readonly", false);
        }
        updateAnalysis();
    });

    $("#rocFor").change(function() {
        renderTrainingPlot();
        setGetParameters(getUpdateAnalysisData());
    });

    $("#blackout").click(function() {
        $("#blackout").hide();
    });

    $("#download-svg").click(function() {
        downloadCanvas("random_forest", "canvas");
    });

    $("#save-to-notebook").click(function() {
        saveCanvasToNotebook("Linear Regression (" + $("#expvar").val() + ")", "Taxonomic Level: " + $("#taxonomy option:selected").text() + "\n" + "L1 Regularization Ratio: " + $("#mixingRatio option:selected").text() + "\n", "canvas");
    });
}

//
// Analysis Specific Methods
//
function customLoading() {}


function getUpdateAnalysisData() {

    var level = taxonomyLevels[getTaxonomicLevel()];

    var taxonomyFilter = getSelectedTaxFilter();
    var taxonomyFilterRole = getSelectedTaxFilterRole();
    var taxonomyFilterVals = getSelectedTaxFilterVals();

    var sampleFilter = getSelectedSampleFilter();
    var sampleFilterRole = getSelectedSampleFilterRole();
    var sampleFilterVals = getSelectedSampleFilterVals();

    var expvar = $("#expvar").val();
    var trainingProportion = $("#trainingProportion").val();
    var fixTraining = $("#fixTraining").val();

    var data = {
        pid: $("#project").val(),
        taxonomyFilterCount: getLowCountThreshold(),
        taxonomyFilterPrevalence: getPrevalenceThreshold(),
        taxonomyFilter: taxonomyFilter,
        taxonomyFilterRole: taxonomyFilterRole,
        taxonomyFilterVals: taxonomyFilterVals,
        sampleFilter: sampleFilter,
        sampleFilterRole: sampleFilterRole,
        sampleFilterVals: sampleFilterVals,
        level: level,
        expvar: expvar,
        crossValidate: $("#crossValidate").val(),
        crossValidateFolds: $("#crossValidateFolds").val(),
        mixingRatio: $("#mixingRatio").val(),
        maxIterations: $("#maxIterations").val(),
        fixTraining: fixTraining,
        trainingProportion: trainingProportion,
        trainingIndexes: JSON.stringify(cachedTrainingIndexes != null ? cachedTrainingIndexes : []),
    };
    if (getParameterByName("ref") != null) {
        data["ref"] = getParameterByName("ref");
    }

    return data;
}


function updateAnalysis() {
    if (!loaded) {
        return;
    }
    showLoading(expectedLoadFactor);

    if (expvar === "None") {
        loadNoCatvar();
        return;
    }

    var data = getUpdateAnalysisData();

    $.ajax({
        type: "POST",
        url: getSharedPrefixIfNeeded() + "/linear_regression" + getSharedUserProjectSuffixIfNeeded(),
        data: data,
        success: function(result) {
            var abundancesObj = JSON.parse(result);
            cachedAbundancesObj = abundancesObj;

            if (cachedAbundancesObj["training_indexes"]) {
                cachedTrainingIndexes = cachedAbundancesObj["training_indexes"];
                data["trainingIndexes"] = cachedTrainingIndexes;
            } else {
                data["trainingIndexes"] = [];
            }
            // Hack to update the URL with the training indexes
            setGetParameters(data);

            loadSuccess();
            $("#train-mae").text(`${abundancesObj["train_mae"]} ± ${abundancesObj["train_mae_std"]}`);
            $("#train-mse").text(`${abundancesObj["train_mse"]} ± ${abundancesObj["train_mse_std"]}`);
            $("#cv-mae").text(`${abundancesObj["cv_mae"]} ± ${abundancesObj["cv_mae_std"]}`);
            $("#cv-mse").text(`${abundancesObj["cv_mse"]} ± ${abundancesObj["cv_mse_std"]}`);
            if (abundancesObj["test_mae"]) {
                $("#test-mae").text(`${abundancesObj["test_mae"]}`);
                $("#test-mse").text(`${abundancesObj["test_mse"]}`);
            } else {
                $("#test-mae").text("N/A");
                $("#test-mse").text("N/A");
            }
        },
        error: function(err) {
            loadError();
            console.log(err);
        }
    });

    setGetParameters(data);
}

function customCatVarCallback(result) {
    result.forEach(function(obj) {
        expVarToType[obj.name] = obj.type;
    });
    var allHeaders = ["None"].concat(result.map(function(obj) { return obj.name; }));

    //
    // Renders the experimental variable
    //
    $("#expvar").empty();
    allHeaders.forEach(function(obj) {
        if (expVarToType[obj] === "both" || expVarToType[obj] === "numeric") {
            $("#expvar").append(
                '<option value="' + obj + '">' + obj + "</option>"
            );
        }
    });
    if (initialExpVar) {
        $("#expvar").val(initialExpVar);
        initialExpVar = null;
    }
}
