$(document).ready(function() {
  // Initialization
  createListeners();

  updateAnalysis();
  
  function createListeners() {
    $("#project").change(function () {
      $.when(updateCatVar()).done(function(a1) {
        updateAnalysis();
      });
    });

    $("#filter-sample").change(function() {
      var filterVal = $("#filter-sample").val();
      if (filterVal === "none" || filterVal === "mian-sample-id") {
        updateAnalysis();
      }
    });

    $("#filter-otu").change(function() {
      var filterVal = $("#filter-otu").val();
      if (filterVal === "none") {
        updateAnalysis();
      }
    });

    $("#taxonomy-specific").change(function () {
      updateAnalysis();
    });

    $("#filter-sample-specific").change(function () {
      updateAnalysis();
    });

    $("#taxonomy").change(function () {
      updateAnalysis();
    });

    $("#catvar").change(function () {
      updateAnalysis();
    });

    $("#keepthreshold").change(function () {
      updateAnalysis();
    });

    $("#pval").change(function () {
      updateAnalysis();
    });

    $("#maxruns").change(function () {
      updateAnalysis();
    });
  }

  function renderBorutaTable(abundancesObj) {
    $("#stats-container").hide();

    if ($.isEmptyObject(abundancesObj)) {
      return;
    }

    var $statsHeader = $("#stats-headers");
    var $statsRows = $("#stats-rows");
    $statsHeader.empty();
    $statsRows.empty();

    var stats = abundancesObj["results"];

    var keys = [];
    $.each( stats, function( key, value ) {
      $statsHeader.append("<th>" + key + " (" + value.length + ")</th>");
      keys.push(key);
    });

    while (true) {
      var empty = true;
      var newRow = "<tr>";
      for (var k = 0; k < keys.length; k++) {
        if (stats[keys[k]].length == 0) {
          newRow += "<td></td>";
        } else {
          var head = stats[keys[k]].shift();
          newRow += "<td>" + head + "</td>";
          empty = false;
        }
      }
      if (empty) {
        break;
      } else {
        $('#stats-rows').append(newRow);
      }
    }

    $("#stats-container").fadeIn(250);
  }


  function updateAnalysis() {
    showLoading();

    var level = taxonomyLevels[getTaxonomicLevel()];

    var taxonomyFilter = getSelectedTaxFilter();
    var taxonomyFilterVals = getSelectedTaxFilterVals();

    var sampleFilter = getSelectedSampleFilter();
    var sampleFilterVals = getSelectedSampleFilterVals();

    var catvar = $("#catvar").val();
    var keepthreshold = $("#keepthreshold").val();
    var pval = $("#pval").val();
    var maxruns = $("#maxruns").val();

    var data = {
      "pid": $("#project").val(),
      "taxonomyFilter": taxonomyFilter,
      "taxonomyFilterVals": taxonomyFilterVals,
      "sampleFilter": sampleFilter,
      "sampleFilterVals": sampleFilterVals,
      "level": level,
      "catvar": catvar,
      "keepthreshold": keepthreshold,
      "pval": pval,
      "maxruns": maxruns
    };

    $.ajax({
      type: "POST",
      url: "boruta",
      data: data,
      success: function(result) {
        hideLoading();
        var abundancesObj = JSON.parse(result);
        renderBorutaTable(abundancesObj);
      },
      error: function(err) {
        console.log(err)
      }
    });
  }
});