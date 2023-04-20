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
  projects(first: 250, filter: {state: {in: ["planned", "started"]}}) {
    nodes {
      id
      name
      state
      teams(first: 10) {
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
    """A project in Linear, which has a state."""

    id: str
    name: str
    state: str


@dataclass
class Team:
    """A team in Linear, which contains a set of projects."""

    key: str
    name: str
    projects: dict[str, Project]
    """A mapping from project id to Project for all projects in this team."""


def get_user_email(session: OAuth2Session) -> str:
    """
    Get the email address of the user who authorized the OAuth session.
    """
    response = session.post(LINEAR_API_URL, json={"query": USER_EMAIL_QUERY})
    return cast(str, response.json()["data"]["viewer"]["email"])


def get_projects_by_team(session: OAuth2Session) -> dict[str, Team]:
    """
    Get a mapping from team keys to Teams, which include a set of projects.

    Note that we are reversing the relationship between projects and teams
    between our query (which returns projects, and then for each project a list
    of teams) and what we're returning here (a list of teams, each of which has
    a set of projects). This is because this works better with the pagination
    and query complexity (we have > 100 projects but probably < 10 teams per
    project).
    """
    response = session.post(LINEAR_API_URL, json={"query": PROJECTS_BY_TEAM_QUERY})
    teams = {}
    for project in response.json()["data"]["projects"]["nodes"]:
        # pop teams out of project since teams is not a field in Project
        project_teams = project.pop("teams")
        for team in project_teams["nodes"]:
            if team["key"] not in teams:
                teams[team["key"]] = Team(projects={}, **team)
            teams[team["key"]].projects[project["id"]] = Project(**project)
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
        diagram += f'    {id}["{content}"]:::{status}\n'

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
