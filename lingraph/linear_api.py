from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import cast

from requests_oauthlib import OAuth2Session

LINEAR_API_URL = "https://api.linear.app/graphql"

USER_EMAIL_QUERY = """
query{
  viewer {
    email
  }
}
"""

PROJECTS_BY_TEAM_QUERY = """
query {
  projects {
    nodes {
      id
      name
      teams {
        nodes {
          key
          name
        }
      }
    }
  }
}
"""

PROJECT_NAME_QUERY = """
query {
  project(id: "%s") {
    name
  }
}
"""

PROJECT_ISSUE_DIAGRAM_QUERY = """
query {
  project(id: "%s") {
    issues(filter: {state: {name: {in: ["Todo", "In Progress", "Done"]}}}) {
      nodes {
        identifier
        title
        url
        state {
          name
        }
        parent {
          identifier
        }
        relations(first: 10) {
          nodes {
            type
            issue {
              identifier
            }
            relatedIssue {
              identifier
            }
          }
        }
        inverseRelations(first: 10) {
          nodes {
            type
            issue {
              identifier
            }
            relatedIssue {
              identifier
            }
          }
        }
      }
    }
  }
}
"""

STATUS_ICONS = {
    "Todo": "fa:fa-circle-notch",
    "In_Progress": "fa:fa-play-circle",
    "Done": "fa:fa-check-circle",
}
"""Map of issue status to fa icon"""

STATUS_STYLES = {
    "Todo": "stroke:DarkGray,color:DarkGray",
    "In_Progress": "stroke:DarkOrange,color:DarkOrange",
    "Done": "stroke:DarkCyan,color:DarkCyan",
}
"""Map of issue status to style"""


@dataclass(eq=True, frozen=True)
class Project:
    id: str
    name: str


@dataclass
class Team:
    """
    A team in Linear, which contains a set of projects.
    """

    key: str
    name: str
    projects: set[Project]


def get_user_email(session: OAuth2Session) -> str:
    """
    Get the email address of the user who authorized the OAuth session.
    """
    response = session.post(LINEAR_API_URL, json={"query": USER_EMAIL_QUERY})
    return cast(str, response.json()["data"]["viewer"]["email"])


def get_projects_by_team(session: OAuth2Session) -> dict[str, Team]:
    """
    Get a mapping from team keys to Teams, which include a set of projects.
    """
    response = session.post(LINEAR_API_URL, json={"query": PROJECTS_BY_TEAM_QUERY})
    teams = {}
    for project in response.json()["data"]["projects"]["nodes"]:
        for team in project["teams"]["nodes"]:
            if team["key"] not in teams:
                teams[team["key"]] = Team(team["key"], team["name"], set())
            teams[team["key"]].projects.add(Project(project["id"], project["name"]))
    return teams


def get_project_name(session: OAuth2Session, project_id: str) -> str:
    response = session.post(
        LINEAR_API_URL, json={"query": PROJECT_NAME_QUERY % project_id}
    )
    return cast(str, response.json()["data"]["project"]["name"])


def get_project_issue_diagram(session: OAuth2Session, project_id: str) -> str:
    response = session.post(
        LINEAR_API_URL, json={"query": PROJECT_ISSUE_DIAGRAM_QUERY % project_id}
    )

    # a set to collect blocking links
    # we will represent blocking links as (source, target) tuples
    blocking_links = set()

    # start assembling the mermaid diagram
    diagram = "flowchart LR\n"

    # add the issues
    for issue in response.json()["data"]["project"]["issues"]["nodes"]:
        # get information out of the issue
        id = issue["identifier"]
        title = issue["title"]
        url = issue["url"]
        status = issue["state"]["name"].replace(" ", "_")

        # look up status icon
        icon = STATUS_ICONS[status]

        # make link to issue
        id_link = f"<a href='{url}'>{id}</a>"

        # assemble content for the node
        content = f"{icon} {id_link}\\n{title}"

        # add the node to the diagram
        diagram += f"    {id}[{content}]:::{status}\n"

        # make the node link to the issue
        # diagram += f'    click {id} "{url}" "{title}" _blank\n'

        # if the issue has a parent, add a link to it
        if issue["parent"]:
            parent_id = issue["parent"]["identifier"]
            diagram += f"    {id} --> {parent_id}\n"

        # check for blocking links
        for relation in itertools.chain(
            issue["relations"]["nodes"], issue["inverseRelations"]["nodes"]
        ):
            if relation["type"] == "blocks":
                blocking_links.add(
                    (
                        relation["issue"]["identifier"],
                        relation["relatedIssue"]["identifier"],
                    )
                )
    # print the blocking links
    for source, target in blocking_links:
        diagram += f"    {source} -.-x|blocks| {target}\n"

    # define a style for each status
    for status, style in STATUS_STYLES.items():
        diagram += f"    classDef {status} {style}\n"

    return diagram
