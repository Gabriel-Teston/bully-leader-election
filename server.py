from flask import Flask, render_template, url_for, Request
from flask_cors import CORS, cross_origin
import requests
import os

import socket
import time
import threading
from multiprocessing import Lock
import random

TIMEOUT = 50
HOSTNAME = socket.gethostname()

instances = {
    alias: idx for idx, alias in enumerate(os.getenv('INSTANCES').split())
}

ID = instances[HOSTNAME]

higher = {
    alias: idx for alias, idx in instances.items() if idx > instances[HOSTNAME]
}

lower = {
    alias: idx for alias, idx in instances.items() if idx < instances[HOSTNAME]
}

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

app.leader = None
app.leader_lock = Lock()
app.election = False
app.election_lock = Lock()
app.inactive = False
app.inactive_lock = Lock()

def get_thread(url, timeout, return_dict, alias):
    return_dict[alias] = requests.get(url, timeout=timeout)

def start_new_election(timeout):
    requests_threads = {}
    requests_threads_returns = {alias:None for alias in higher.keys()}
    for alias, idx in higher:
        url = f'http://{alias}/start_election/{HOSTNAME}'
        requests_threads[alias] = threading.Thread(target=get_thread, args=(url, timeout, requests_threads_returns, alias))
    [t.start() for t in requests_threads.values()]

    [t.join() for t in requests_threads.values()]

    return requests_threads_returns

def broadcast_new_leader(timeout):
    requests_threads = {}
    requests_threads_returns = {alias:None for alias in higher.keys()}
    for alias, idx in lower:
        url = f'http://{alias}/new_leader/{HOSTNAME}'
        requests_threads[alias] = threading.Thread(target=get_thread, args=(url, timeout, requests_threads_returns, alias))
        requests_threads[alias] = threading.Thread(target=get)
    [t.start() for t in requests_threads.values()]

    [t.join() for t in requests_threads.values()]

    return requests_threads_returns

def election(timeout):
    if app.election_lock.acquire():
        # Start election
        response = start_new_election(timeout)

        app.election_lock.release()
    else:
        # Election already started
        return

    if not any(response):
        # I'm the leader
        broadcast_new_leader(timeout)
    else:
        # I'm DONE
        pass

def bully(timeout):
    while True:
        time.sleep(random.randint(5, 60))
        with app.leader_lock:
            url = f'http://{leader}/health_check'
            try:
                # Leader is dead
                requests.get(url, timeout=timeout)
            except:
                threading.Thread(target=election, args=(timeout,)).start()

threading.Thread(target=bully, args=(TIMEOUT,)).start()

@app.route("/")
def index():
    return render_template(
        'index.html', 
        hostname=HOSTNAME,
        higher=higher,
        lower=lower
        )

@app.route("/halt")
def halt():
    with app.inactive_lock:
        if app.inactive:
            threading.Thread(target=election, args=(timeout,)).start()
        app.inactive = [True, False][app.inactive]

@app.route("/health_check")
def health_check():
    return "OK"

@app.route("/new_leader/<leader>")
def new_leader(leader):
    with app.leader_lock:
        app.leader = leader

@app.route("/start_election/<caller>")
def start_election(caller):
    with app.inactive_lock:
        if not app.inactive:
            threading.Thread(target=election, args=(timeout,)).start()
            return "OK"
        else:
            Request.close()

    
