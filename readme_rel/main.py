from __future__ import annotations

import datetime as dt
import operator
import os
from collections import abc
from dataclasses import dataclass

from gql import Client, GraphQLRequest, gql
from gql.transport.httpx import HTTPXTransport
from httpx import Timeout

TOK = os.environ.get("PUBLIC_PAT", "")

# This search query should yield all of my public repositories, sorted by last updated
# For each repository, provide:
#    * Name
#    * URL
#    * Is archived?
#    * Releases (may be empty)
#        * Last release
#            * Tag
#            * Publish date
#            * URL
#        * Total number of releases
# This query is limited to 50 results at a time, so pagination information is also provided
BASE_QUERY = """
query {
  search(
    first: 50
    type: REPOSITORY
    query: "owner:sco1 is:public sort:updated"
    after: %AFTER%
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

TIMEOUT = Timeout(5, read=15)  # Extend the read timeout a bit, keep the rest at default
TRANSPORT = HTTPXTransport(
    url="https://api.github.com/graphql",
    headers={"Authorization": f"bearer {TOK}"},
    timeout=TIMEOUT,
)
CLIENT = Client(transport=TRANSPORT, fetch_schema_from_transport=True)


@dataclass(slots=True, frozen=True)
class Release:  # noqa: D101
    tag_name: str
    published: dt.datetime
    url: str

    @classmethod
    def from_node(cls, node: dict) -> Release:
        """
        Build a `Release` instance from the provided node.

        The node is assumed to contain the following keys:
            * `"tagName"`
            * `"publishedAt"`
            * `"url"`
        """
        return cls(
            tag_name=node["tagName"],
            published=dt.datetime.fromisoformat(node["publishedAt"]),
            url=node["url"],
        )


@dataclass(slots=True, frozen=True)
class Repository:  # noqa: D101
    name: str
    url: str
    n_releases: int
    last_release: Release

    @classmethod
    def from_node(cls, node: dict) -> Repository:
        """
        Build a `Repository` instance from the provided node.

        The node is assumed to contain the following keys:
            * `"name"`
            * `"url"`
            * `"releases"` (of a form expected by `Release.from_node`)
        """
        return cls(
            name=node["name"],
            url=node["url"],
            n_releases=node["releases"]["totalCount"],
            last_release=Release.from_node(node["releases"]["nodes"][0]),
        )


def _paginate_query(after: str | None = None) -> GraphQLRequest:
    """
    Update `BASE_QUERY` with the provided pagination cursor.

    Alternatively, if `None` is passed, the cursor is specified as `"null"` to obtain the first page
    of results.

    NOTE: It is assumed that `BASE_QUERY` contains an `%AFTER%` placeholder indicating where the
    cursor should be inserted.
    """
    if after is None:
        insert = "null"
    else:
        # If a cursor is provided it needs to be wrapped in quotes
        insert = f'"{after}"'

    query = BASE_QUERY.replace("%AFTER%", insert)
    return gql(query)


def n_recent_releases(n: int = 5) -> list[Repository]:
    """
    Query the GitHub GraphQL API for my `n` most recent repositories with a published release.

    For the purposes of this tool, only public, non-archived repositories are considered.

    NOTE: Use of this function requires that a GitHub Personal Access Token be set to the
    `"PUBLIC_PAT"` environment variable in order to authenticate with GitHub's GraphQL API. This
    token only needs the base public repository access, no account or other repository access is
    necessary.
    """
    if not TOK:
        raise RuntimeError("A PAT could not be found in the environment, please set 'PUBLIC_PAT'")

    repositories = []

    has_page = True
    after: str | None = None
    while has_page:
        query = _paginate_query(after=after)
        result = CLIENT.execute(query)

        has_page = result["search"]["pageInfo"]["hasNextPage"]
        after = result["search"]["pageInfo"]["endCursor"]

        for repo in result["search"]["nodes"]:
            if repo["isArchived"]:
                continue

            release_nodes = repo["releases"]["nodes"]
            if not release_nodes:
                continue

            repositories.append(Repository.from_node(repo))

    repositories.sort(key=operator.attrgetter("last_release.published"), reverse=True)
    return repositories[:n]


def render_repos(repos: abc.Iterable[Repository]) -> str:
    """Format the provided repos into a bulleted list of their component information."""
    repo_strings = []
    for r in repos:
        repo_url = f"[`{r.name}`]({r.url})"
        tree_url = f"[Tree]({r.url}/tree/{r.last_release.tag_name})"
        changelog_url = f"[Changelog]({r.last_release.url})"
        publish_str = r.last_release.published.strftime(r"%Y-%m-%d")

        # fmt: off
        repo_strings.append(f"* {publish_str}: {repo_url} `{r.last_release.tag_name}` ({changelog_url}, {tree_url})  ")  # noqa: E501
        # fmt: on

    return "\n".join(repo_strings)
