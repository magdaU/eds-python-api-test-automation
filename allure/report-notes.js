// Explains empty Categories widgets in the generated Allure report, so that an empty widget does not read as
// "something is missing". Added to the report by scripts/inject_report_notes.py, never loaded by `allure serve`.
//
// A note appears only when the report's own data confirms it: no failed, broken or skipped test (summary.json) for the
// Overview widget, and no category in any recorded run (categories-trend.json) for the trend. If a request fails
// or a widget is not empty, nothing is changed.
(function () {
  "use strict";

  var OVERVIEW_NOTE =
    "No test failed, broke or was skipped in this run, so there is nothing to categorize. This is expected, not missing data.";
  var TREND_NOTE =
    "No test failed, broke or was skipped in any recorded run, so there is nothing to categorize. " +
    "The trend fills as soon as one does.";
  var MARK = "data-report-note";

  var facts = { noCategorizedTests: false, noCategoriesInHistory: false };

  function getJson(path) {
    return fetch(path).then(function (response) {
      if (!response.ok) throw new Error(path + " " + response.status);
      return response.json();
    });
  }

  function loadFacts() {
    return Promise.all([getJson("widgets/summary.json"), getJson("widgets/categories-trend.json")]).then(function (data) {
      var statistic = data[0].statistic;
      facts.noCategorizedTests = statistic.failed + statistic.broken + statistic.skipped === 0;
      facts.noCategoriesInHistory = data[1].every(function (build) {
        return Object.keys(build.data || {}).length === 0;
      });
    });
  }

  function annotate() {
    if (facts.noCategorizedTests) {
      document.querySelectorAll('.widget[data-id="categories"]').forEach(function (widget) {
        var subtitle = widget.querySelector(".widget__subtitle");
        var title = widget.querySelector(".widget__title");
        if (title && subtitle && /^0\b/.test(subtitle.textContent.trim()) && !widget.querySelector("[" + MARK + "]")) {
          var note = document.createElement("div");
          note.className = "widget__noitems";
          note.setAttribute(MARK, "");
          note.textContent = OVERVIEW_NOTE;
          title.insertAdjacentElement("afterend", note);
        }
      });
    }
    if (facts.noCategoriesInHistory) {
      document.querySelectorAll('.widget[data-id="categories-trend"]').forEach(function (widget) {
        if (widget.querySelector("[" + MARK + "]")) return;
        // with a single build Allure prints "There is nothing to show"; with several it draws an empty chart instead
        var empty = widget.querySelector(".widget__noitems");
        var chart = widget.querySelector(".categories-trend__chart");
        if (empty) {
          empty.setAttribute(MARK, "");
          empty.textContent = TREND_NOTE;
        } else if (chart) {
          var note = document.createElement("div");
          note.className = "widget__noitems";
          note.setAttribute(MARK, "");
          note.textContent = TREND_NOTE;
          chart.insertAdjacentElement("afterend", note);
        }
      });
    }
  }

  loadFacts()
    .then(function () {
      annotate();
      // the report renders its pages client-side and re-renders on navigation, so watch for the widgets
      new MutationObserver(annotate).observe(document.body, { childList: true, subtree: true });
    })
    .catch(function () {
      /* without the report data there is nothing to confirm, so leave the report as Allure rendered it */
    });
})();
