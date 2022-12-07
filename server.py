from flask import Flask, render_template, url_for
from flask_cors import CORS, cross_origin
import requests
import os

import socket
import time

HOSTNAME = socket.gethostname()

instances = {
    alias: idx for idx, alias in enumerate(os.getenv('INSTANCES').split())
}

higher = {
    alias: idx for alias, idx in instances.items() if idx > instances[HOSTNAME]
}

lower = {
    alias: idx for alias, idx in instances.items() if idx < instances[HOSTNAME]
}

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route("/")
def index():
    return render_template(
        'index.html', 
        hostname=HOSTNAME,
        higher=higher,
        lower=lower
        )