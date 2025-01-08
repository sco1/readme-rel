import datetime as dt

from readme_rel.main import Release, Repository, render_repos

SAMPLE_REPOS = [
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

# fmt: off
TRUTH_RENDERED = """\
* 2025-01-06: [`xbmini-py`](https://github.com/sco1/xbmini-py) `v0.5.0` ([Changelog](https://github.com/sco1/xbmini-py/releases/tag/v0.5.0), [Tree](https://github.com/sco1/xbmini-py/tree/v0.5.0))  
* 2024-12-31: [`matplotlib-window`](https://github.com/sco1/matplotlib-window) `v1.1.0` ([Changelog](https://github.com/sco1/matplotlib-window/releases/tag/v1.1.0), [Tree](https://github.com/sco1/matplotlib-window/tree/v1.1.0))  
* 2024-11-27: [`pyflysight`](https://github.com/sco1/pyflysight) `v0.9.0` ([Changelog](https://github.com/sco1/pyflysight/releases/tag/v0.9.0), [Tree](https://github.com/sco1/pyflysight/tree/v0.9.0))  """
# fmt: on


def test_render_repos() -> None:
    assert render_repos(SAMPLE_REPOS) == TRUTH_RENDERED
