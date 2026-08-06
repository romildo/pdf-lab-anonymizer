# tests/test_page_selector.py

import pytest

from pdf_lab_anonymizer.engine import parse_page_selector


def test_open_ended_range_on_single_page_document_is_empty():
    assert parse_page_selector("2-", 1) == set()


def test_open_ended_range_on_multi_page_document():
    assert parse_page_selector("2-", 5) == {1, 2, 3, 4}


def test_explicit_range_is_clamped_to_document_length():
    assert parse_page_selector("1-3", 2) == {0, 1}


def test_reversed_explicit_range_is_invalid():
    with pytest.raises(ValueError):
        parse_page_selector("5-3", 10)


def test_open_ended_range_starting_after_document_is_empty():
    assert parse_page_selector("5-", 3) == set()


def test_all_selector():
    assert parse_page_selector("all", 3) == {0, 1, 2}


def test_comma_separated_selector():
    assert parse_page_selector("1,3-4", 4) == {0, 2, 3}
