import datetime as dt
import json

import pytest
from gql import gql
from pytest_mock import MockerFixture

from readme_rel.main import Release, Repository, _paginate_query, n_recent_releases
from tests import SAMPLE_DATA_DIR

TRUTH_QUERY_NO_NEXT = """
query {
  search(
    first: 50
    type: REPOSITORY
    query: "owner:sco1 is:public sort:updated"
    after: null
  ) {
    pageInfo {
      hasNextPage
      endCursor
    }
    nodes {
      ... on Repository {
        name
        url
        isArchived

        releases(orderBy: { field: CREATED_AT, direction: DESC }, first: 1) {
          totalCount
          nodes {
            tagName
            publishedAt
            url
          }
        }
      }
    }
  }
}
"""

TRUTH_QUERY_NEXT_PAGE = """
query {
  search(
    first: 50
    type: REPOSITORY
    query: "owner:sco1 is:public sort:updated"
    after: "abc123"
  ) {
    pageInfo {
      hasNextPage
      endCursor
    }
    nodes {
      ... on Repository {
        name
        url
        isArchived

        releases(orderBy: { field: CREATED_AT, direction: DESC }, first: 1) {
          totalCount
          nodes {
            tagName
            publishedAt
            url
          }
        }
      }
    }
  }
}
"""

QUERY_TEST_CASES = (
    (None, TRUTH_QUERY_NO_NEXT),
    ("abc123", TRUTH_QUERY_NEXT_PAGE),
)


@pytest.mark.parametrize(("after", "truth_query"), QUERY_TEST_CASES)
def test_paginate_query(after: str | None, truth_query: str) -> None:
    assert _paginate_query(after) == gql(truth_query)


def test_n_recent_release_no_token_raises(mocker: MockerFixture) -> None:
    mocker.patch("readme_rel.main.TOK", new="")

    with pytest.raises(RuntimeError, match="PAT"):
        n_recent_releases()


def test_n_recent_releases_empty_result(mocker: MockerFixture) -> None:
    mocker.patch("readme_rel.main.TOK", new="abc123")

    empty_query = SAMPLE_DATA_DIR / "empty_result.json"
    with empty_query.open("r") as f:
        empty_query_result = json.load(f)

    mocker.patch("readme_rel.main.CLIENT.execute", return_value=empty_query_result)

    assert n_recent_releases() == []


TRUTH_SINGLE_PAGE_REPOS = [
    Repository(
        name="matplotlib-window",
        url="https://github.com/sco1/matplotlib-window",
        n_releases=3,
        last_release=Release(
            tag_name="v1.1.0",
            published=dt.datetime.fromisoformat("2024-12-31T01:26:50Z"),
            url="https://github.com/sco1/matplotlib-window/releases/tag/v1.1.0",
        ),
    ),
    Repository(
        name="pre-commit-check-office-metadata",
        url="https://github.com/sco1/pre-commit-check-office-metadata",
        n_releases=1,
        last_release=Release(
            tag_name="v1.0.0",
            published=dt.datetime.fromisoformat("2024-10-08T14:56:40Z"),
            url="https://github.com/sco1/pre-commit-check-office-metadata/releases/tag/v1.0.0",
        ),
    ),
    Repository(
        name="zwom",
        url="https://github.com/sco1/zwom",
        n_releases=2,
        last_release=Release(
            tag_name="v0.3.0",
            published=dt.datetime.fromisoformat("2022-11-07T23:57:27Z"),
            url="https://github.com/sco1/zwom/releases/tag/v0.3.0",
        ),
    ),
]


def test_n_recent_release_single_page(mocker: MockerFixture) -> None:
    mocker.patch("readme_rel.main.TOK", new="abc123")

    single_page_query = SAMPLE_DATA_DIR / "page_2.json"
    with single_page_query.open("r") as f:
        single_page_query_result = json.load(f)

    mocker.patch("readme_rel.main.CLIENT.execute", return_value=single_page_query_result)

    assert n_recent_releases(3) == TRUTH_SINGLE_PAGE_REPOS


TRUTH_MULTI_PAGE_REPOS = [
    Repository(  # Page 1
        name="xbmini-py",
        url="https://github.com/sco1/xbmini-py",
        n_releases=5,
        last_release=Release(
            tag_name="v0.5.0",
            published=dt.datetime.fromisoformat("2025-01-06T20:44:16Z"),
            url="https://github.com/sco1/xbmini-py/releases/tag/v0.5.0",
        ),
    ),
    Repository(  # Page 2
        name="matplotlib-window",
        url="https://github.com/sco1/matplotlib-window",
        n_releases=3,
        last_release=Release(
            tag_name="v1.1.0",
            published=dt.datetime.fromisoformat("2024-12-31T01:26:50Z"),
            url="https://github.com/sco1/matplotlib-window/releases/tag/v1.1.0",
        ),
    ),
    Repository(  # Page 1
        name="pyflysight",
        url="https://github.com/sco1/pyflysight",
        n_releases=9,
        last_release=Release(
            tag_name="v0.9.0",
            published=dt.datetime.fromisoformat("2024-11-27T17:52:24Z"),
            url="https://github.com/sco1/pyflysight/releases/tag/v0.9.0",
        ),
    ),
]


def test_n_recent_release_multi_page(mocker: MockerFixture) -> None:
    mocker.patch("readme_rel.main.TOK", new="abc123")

    query_pages = [SAMPLE_DATA_DIR / p for p in ("page_1.json", "page_2.json")]
    query_results = []
    for p in query_pages:
        with p.open("r") as f:
            query_results.append(json.load(f))

    client_patch = mocker.patch("readme_rel.main.CLIENT.execute", side_effect=query_results)
    recent_releases = n_recent_releases(3)

    assert client_patch.call_count == 2
    assert recent_releases == TRUTH_MULTI_PAGE_REPOS


def test_n_recent_release_skips_archived(mocker: MockerFixture) -> None:
    mocker.patch("readme_rel.main.TOK", new="abc123")

    archived_query = SAMPLE_DATA_DIR / "archived_repo.json"
    with archived_query.open("r") as f:
        archived_query_result = json.load(f)

    mocker.patch("readme_rel.main.CLIENT.execute", return_value=archived_query_result)

    assert n_recent_releases(3) == []
