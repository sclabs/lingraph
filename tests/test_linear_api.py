import os
from functools import partial

import pytest
import requests

from lingraph.linear_api import (
    get_project_issue_diagram,
    get_project_name,
    get_projects_by_team,
    get_user_email,
)

TEST_PROJECT_ID = "30a0f293-6732-4f47-8286-39d3771e1824"


class MockOAuth2Session:
    post = partial(
        requests.post, headers={"Authorization": os.environ["LINEAR_API_KEY"]}
    )


@pytest.fixture
def client():
    return MockOAuth2Session()


def test_get_user_email(client):
    email = get_user_email(client)
    assert email == "thomasgilgenast@gmail.com"


def test_get_projects_by_team(client):
    teams = get_projects_by_team(client)
    # there should be an SCL team
    assert "SCL" in teams.keys()
    # the SCL team should include a project called Test
    assert "Test" in [project.name for project in teams["SCL"].projects.values()]
    # its state should be planned
    assert teams["SCL"].projects[TEST_PROJECT_ID].state == "planned"


def test_get_project_name(client):
    project_name = get_project_name(client, TEST_PROJECT_ID)
    assert project_name == "Test"


def test_get_project_issue_diagram(client):
    diagram = get_project_issue_diagram(client, TEST_PROJECT_ID)
    assert (
        diagram
        == r"""flowchart LR
    SCL-11[fa:fa-circle-notch <a href='https://linear.app/sclabs/issue/SCL-11/test'>SCL-11</a>\ntest]:::Todo
    classDef Todo stroke:DarkGray,color:DarkGray
    classDef In_Progress stroke:DarkOrange,color:DarkOrange
    classDef Done stroke:DarkCyan,color:DarkCyan
"""  # noqa: E501
    )
