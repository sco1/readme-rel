import datetime as dt

from readme_rel.main import Release, Repository

SAMPLE_RELEASE_NODE = {
    "tagName": "v0.5.0",
    "publishedAt": "2025-01-06T20:44:16Z",
    "url": "https://github.com/sco1/xbmini-py/releases/tag/v0.5.0",
}


def test_release_from_raw() -> None:
    truth_release = Release(
        tag_name="v0.5.0",
        published=dt.datetime.fromisoformat("2025-01-06T20:44:16Z"),
        url="https://github.com/sco1/xbmini-py/releases/tag/v0.5.0",
    )

    assert Release.from_node(SAMPLE_RELEASE_NODE) == truth_release


SAMPLE_REPO_NODE = {
    "name": "xbmini-py",
    "url": "https://github.com/sco1/xbmini-py",
    "isArchived": False,
    "releases": {
        "totalCount": 5,
        "nodes": [
            {
                "tagName": "v0.5.0",
                "publishedAt": "2025-01-06T20:44:16Z",
                "url": "https://github.com/sco1/xbmini-py/releases/tag/v0.5.0",
            }
        ],
    },
}


def test_repo_from_raw() -> None:
    release = Release(
        tag_name="v0.5.0",
        published=dt.datetime.fromisoformat("2025-01-06T20:44:16Z"),
        url="https://github.com/sco1/xbmini-py/releases/tag/v0.5.0",
    )

    truth_repo = Repository(
        name="xbmini-py",
        url="https://github.com/sco1/xbmini-py",
        n_releases=5,
        last_release=release,
    )

    assert Repository.from_node(SAMPLE_REPO_NODE) == truth_repo
