from __future__ import annotations

import datetime as dt
import operator
import os
from dataclasses import dataclass

from gql import Client, gql
from gql.transport.httpx import HTTPXTransport
from graphql import DocumentNode
from httpx import Timeout

TOK = os.environ.get("PUBLIC_PAT", "")
if not TOK:
    raise RuntimeError("A PAT could not be found in the environment, please set 'PUBLIC_PAT'")


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

TIMEOUT = Timeout(5, read=10)
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


def _paginate_query(after: str | None = None) -> DocumentNode:
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


def n_recent_releases(n: int = 5) -> list[Release]:
    """
    Query the GitHub GraphQL API for my `n` most recent repositories with a published release.

    For the purposes of this tool, only public, non-archived repositories are considered.
    """
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


if __name__ == "__main__":
    n_recent_releases()
