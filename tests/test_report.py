from arche import Arche
from arche import SH_URL
from arche.report import Report
from arche.rules.result import Level, Outcome
from conftest import create_result
import pandas as pd
import pytest


@pytest.mark.parametrize(
    "messages, expected_details",
    [
        (
            [
                (
                    "rule name here",
                    {Level.INFO: [("summary", "very detailed message")]},
                ),
                (
                    "other result there",
                    {Level.INFO: [("summary", "other detailed message")]},
                ),
            ],
            [
                "<h2>Details</h2>",
                "rule name here (1 message(s)):",
                "very detailed message",
                "<br>",
                "other result there (1 message(s)):",
                "other detailed message",
                "<br>",
                "<h2>Plots</h2>",
            ],
        )
    ],
)
def test_display(mocker, get_df, capsys, messages, expected_details):
    mocked_display = mocker.patch("arche.report.display_html", autospec=True)

    r = Report()
    for m in messages:
        result = create_result(*m, stats=[get_df])
        r.save(result)
    r()

    generated_html = mocked_display.mock_calls[0][1][0]
    assert generated_html.count("Plotly.newPlot") == 2
    assert generated_html.count("rule name here - SKIPPED") == 2
    assert generated_html.count("other result there - SKIPPED") == 2


@pytest.mark.parametrize(
    "message, expected_details",
    [({Level.INFO: [("summary", "very detailed message")]}, "very detailed message")],
)
def test_write_rule_details(mocker, get_df, capsys, message, expected_details):
    mocked_display = mocker.patch("arche.report.display_html", autospec=True)
    outcome = create_result("rule name here", message)
    r = Report()
    r(outcome)
    generated_html = mocked_display.mock_calls[0][1][0]
    assert generated_html.count("very detailed message") == 1


def test_display_errors(mocker, get_job_items, get_schema):
    mocked_display = mocker.patch("arche.report.display_html", autospec=True)
    url = f"{SH_URL}/112358/13/21/item/1"
    schema = {"type": "object", "required": ["price"], "properties": {"price": {}}}
    g = Arche("source", schema=schema)
    g._source_items = get_job_items
    g.report_all()
    generated_html = mocked_display.mock_calls[0][1][0]
    mocked_display.assert_called_once()
    assert "JSON Schema Validation - FAILED" in mocked_display.mock_calls[0][1][0]
    assert generated_html.count('href="{}"'.format(url)) == 1
    assert generated_html.count("&#39;price&#39; is a required property") == 1


@pytest.mark.parametrize(
    "keys, limit, sample_mock, expected_sample",
    [
        (
            pd.Series(f"{SH_URL}/112358/13/21/item/0"),
            5,
            pd.Series(f"{SH_URL}/112358/13/21/item/5"),
            f"[0]({SH_URL}/112358/13/21/item/0)",
        ),
        (
            pd.Series([f"{SH_URL}/112358/13/21/item/{i}" for i in range(20)]),
            10,
            pd.Series(f"{SH_URL}/112358/13/21/item/5"),
            f"[5]({SH_URL}/112358/13/21/item/5)",
        ),
        (
            pd.Series("112358/13/21/0"),
            1,
            pd.Series("112358/13/21/0"),
            f"[0]({SH_URL}/112358/13/21/item/0)",
        ),
        (pd.Series([0, 1]), 1, pd.Series([0, 1]), "0, 1"),
    ],
)
def test_sample_keys(mocker, keys, limit, sample_mock, expected_sample):
    mocker.patch("pandas.Series.sample", return_value=sample_mock, autospec=True)
    assert Report.sample_keys(keys, limit) == expected_sample


def test_save():
    r = Report()
    dummy_result = create_result("dummy", {Level.INFO: [("outcome",)]})
    r.save(dummy_result)
    assert r.results == {dummy_result.name: dummy_result}


def test__order_rules(get_job_items):
    schema = {"type": "object", "required": ["price"], "properties": {"price": {}}}
    g = Arche("source", schema=schema)
    g._source_items = get_job_items
    g.report_all()
    results = g.report.results.values()

    ordered_results = Report._order_rules(results)
    actual_outcome = Outcome.PASSED
    results_expected_order = [
        Outcome.PASSED,
        Outcome.FAILED,
        Outcome.WARNING,
        Outcome.SKIPPED,
    ]
    for result in ordered_results:
        if result.outcome == actual_outcome:
            continue

        assert (
            result.outcome
            in results_expected_order[
                results_expected_order.index(actual_outcome) + 1:
            ]
        )
        actual_outcome = result.outcome
