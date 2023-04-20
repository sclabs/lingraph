lingraph
========

An OAuth2 Flask app to visualize linear issues as a graph

Local quickstart
----------------

    git clone https://github.com/sclabs/lingraph
    cd lingraph
    python3 -m venv venv
    source venv/bin/activate
    pip install -e '.[dev]'
    export LINGRAPH_CLIENT_ID=...  # see below
    export LINGRAPH_CLIENT_SECRET=...
    python lingraph/app.py

Navigate to http://127.0.0.1:5000/ to complete the login flow.

Creating the Linear OAuth app
-----------------------------

1. Go to https://linear.app/settings/api/applications/new
2. Fill in the form, making sure to include http://127.0.0.1:5000/callback and
   http://localhost:5000/callback in the Callback URLs.
3. Save the Client ID and Client Secret to env vars called `LINGRAPH_CLIENT_ID`
   and `LINGRAPH_CLIENT_SECRET`, respectively.

Docker image
------------

The docker image is based on [tiangolo/meinheld-gunicorn-flask](https://hub.docker.com/r/tiangolo/meinheld-gunicorn-flask).

The Docker image is built and published to Docker Hub as
`thomasgilgenast/lingraph:latest` on every commit to main by GitHub Actions.

You can also build the image locally with

    docker build . -t lingraph

And to run the image locally at http://127.0.0.1:5000

    docker run -d -p 5000:80 \
        -e FLASK_SECRET_KEY=... \
        -e LINGRAPH_CLIENT_ID=... \
        -e LINGRAPH_CLIENT_SECRET=... \
        -e OAUTHLIB_INSECURE_TRANSPORT=1
        lingraph

Note that you need to set `OAUTHLIB_INSECURE_TRANSPORT=1` for local testing with
no HTTPS.

Compiling dependencies
----------------------

    pip-compile --annotation-style=line
