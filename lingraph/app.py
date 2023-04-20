from __future__ import annotations

import os

from flask import (
    Flask,
    Request,
    Response,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from linear_api import (
    get_project_issue_diagram,
    get_project_name,
    get_projects_by_team,
    get_user_email,
)
from requests_oauthlib import OAuth2Session
from werkzeug.middleware.proxy_fix import ProxyFix

# flask setup
app = Flask(__name__)  # creates flask app
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1)  # fixes https behind proxy
app.config.from_prefixed_env()  # loads FLASK_SECRET_KEY

# oauth setup: client id and secret, urls, scopes
client_id = os.environ["LINGRAPH_CLIENT_ID"]
client_secret = os.environ["LINGRAPH_CLIENT_SECRET"]
authorization_base_url = "https://linear.app/oauth/authorize"
token_url = "https://api.linear.app/oauth/token"
revoke_url = "https://api.linear.app/oauth/revoke"
redirect_uri_path = "callback"  # relative to host url
scope = "read"  # linear API OAuth scope


def redirect_uri(req: Request) -> str:
    """
    Get the OAuth redirect URI, based on the host_url of a request.

    During local testing, it should be http://127.0.0.1:5000/callback

    When deployed, it should automatically adjust to wherever the app is
    hosted.

    Parameters
    ----------
    req
        A Flask Request object.

    Returns
    -------
    str
        The OAuth redirect URI.
    """
    base_url: str = req.host_url
    return base_url + redirect_uri_path


def ensure_auth() -> tuple[OAuth2Session, Response | None, bool]:
    """
    Helper function to handle auth.

    If the user is already logged in, we'll return a logged-in OAuth2Session
    that can be used to call REST API endpoints.

    If the user is not logged in, we'll return a redirect response to the
    auth url.

    Returns
    -------
    tuple[OAuth2Session, Response | None, bool]
        A tuple containing the OAuth2Session (which may be logged in or not), a
        redirect response to the auth url (if the user is not logged in), and a
        bool indicating whether or not the user is logged in.
    """
    if "oauth_token" in session:
        # the token is already in the Flask session
        # we can use it to make a logged-in OAuth2Session
        # we don't need to redirect the user to the auth url
        # the user is already logged in
        oauth_session = OAuth2Session(client_id, token=session["oauth_token"])
        redirect_response = None
        logged_in = True
    else:
        # the token is not in the Flask session
        # we will need to redirect the user to the auth url
        # in order to do that, we make a non-logged-in OAuth2Session
        oauth_session = OAuth2Session(
            client_id, scope=scope, redirect_uri=redirect_uri(request)
        )

        # we can use that OAuth2Session to get the auth url
        # this also returns the oauth state
        authorization_url, state = oauth_session.authorization_url(
            authorization_base_url,
            # prompt="consent",  # uncomment to force consent screen
        )

        # we need to save the oauth state in the Flask session
        # we will use it later to verify the response from the server
        session["oauth_state"] = state

        # we make a redirect response to the auth url
        redirect_response = redirect(authorization_url)

        # the user is not logged in
        logged_in = False
    return oauth_session, redirect_response, logged_in


@app.route("/")
def root():
    # check auth
    oauth_session, redirect_response, logged_in = ensure_auth()

    # get the user's email
    email = get_user_email(oauth_session) if logged_in else None

    # get the user's projects
    teams = get_projects_by_team(oauth_session) if logged_in else None

    # render the root page
    return render_template("root.html", logged_in=logged_in, email=email, teams=teams)


@app.route("/login", methods=["GET"])
def login():
    # check auth
    oauth_session, redirect_response, logged_in = ensure_auth()

    # we're probably not logged in, so we'll get a redirect response to the
    # auth url
    if redirect_response:
        return redirect_response

    # if we happen to already be logged in, just take us to the root page
    return redirect(url_for("root"))


@app.route("/callback", methods=["GET"])
def callback():
    # we need to verify the response from the server using the oauth state that
    # was made when we constructed the auth url; if this is missing, take us to
    # the root page
    if "oauth_state" not in session:
        return redirect(url_for("root"))

    # use the oauth state to make an in-progress OAuth2Session (no token yet)
    oauth_session = OAuth2Session(
        client_id, state=session["oauth_state"], redirect_uri=redirect_uri(request)
    )

    # use the in-progress OAuth2Session to fetch the oauth token
    token = oauth_session.fetch_token(
        token_url, client_secret=client_secret, authorization_response=request.url
    )

    # save the token to the Flask session
    session["oauth_token"] = token

    # take us to the root page
    return redirect(url_for("root"))


@app.route("/logout", methods=["GET"])
def logout():
    # check auth
    oauth_session, redirect_response, logged_in = ensure_auth()

    # if we're not logged in, we don't need to log out - just take us to the
    # root page
    if not logged_in:
        return redirect(url_for("root"))

    # revoke the oauth token
    response = oauth_session.post(revoke_url)

    # clear the token from the Flask session
    session.clear()

    # if the revokation worked, it should return 200 and we should just go to
    # the root page
    if response.status_code == 200:
        return redirect(url_for("root"))

    # otherwise, maybe the response has some error info, so let's print that
    # with a link back to the root page
    return (
        f"<pre>{response.json()}</pre>" f"<a href='{url_for('root')}'>return home</a>"
    )


@app.route("/project/<project_id>", methods=["GET"])
def project(project_id):
    # check auth
    oauth_session, redirect_response, logged_in = ensure_auth()

    # if we're not logged in, we don't need to log out - just take us to the
    # root page
    if not logged_in:
        return redirect(url_for("root"))

    # get the user's email
    email = get_user_email(oauth_session) if logged_in else None

    # get the project name
    project_name = get_project_name(oauth_session, project_id)

    # get the project issue graph
    graph = get_project_issue_diagram(oauth_session, project_id)

    # render the project page
    return render_template(
        "project.html",
        logged_in=logged_in,
        email=email,
        project_name=project_name,
        graph=graph,
    )


if __name__ == "__main__":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
    app.secret_key = os.urandom(24)
    app.run(debug=True)
