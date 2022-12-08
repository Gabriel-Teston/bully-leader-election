from flask import Flask, render_template, url_for, Request
from flask_cors import CORS, cross_origin
from flask_socketio import SocketIO, send, emit
import requests
import os

import socket
import time
import threading
from multiprocessing import Lock
import random
import logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

TIMEOUT = 20
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
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app)

app.leader = None
app.leader_lock = Lock()
app.election = False
app.election_lock = Lock()
app.inactive = True
app.inactive_lock = Lock()
app.connected = False
app.time_until_retry = 0

def get_thread(url, timeout, return_dict, alias):
    response requests.get(url, timeout=timeout)
    if response.status_code == 400:
        return
    return_dict[alias] = True

def start_new_election(timeout):
    print("Start new election")
    requests_threads = {}
    requests_threads_returns = {alias:None for alias in higher.keys()}
    for alias, idx in higher.items():
        url = f'http://{alias}/start_election/{HOSTNAME}'
        requests_threads[alias] = threading.Thread(target=get_thread, args=(url, timeout, requests_threads_returns, alias))
    [t.start() for t in requests_threads.values()]

    [t.join() for t in requests_threads.values()]

    return requests_threads_returns

def broadcast_new_leader(timeout):
    print("Broadcast new leader")
    requests_threads = {}
    requests_threads_returns = {alias:None for alias in higher.keys()}
    for alias, idx in lower.items():
        url = f'http://{alias}/new_leader/{HOSTNAME}'
        requests_threads[alias] = threading.Thread(target=get_thread, args=(url, timeout, requests_threads_returns, alias))
    [t.start() for t in requests_threads.values()]

    [t.join() for t in requests_threads.values()]

    return requests_threads_returns

def election(timeout):
    print("Election")
    if app.election_lock.acquire():
        # Start election
        response = start_new_election(timeout)

        app.election_lock.release()
    else:
        # Election already started
        return

    if not any(response):
        # I'm the leader
        print(f"I'm the leader ({HOSTNAME})")
        app.leader = HOSTNAME
        broadcast_new_leader(timeout)
    else:
        # I'm DONE
        pass

def bully(timeout):
    while True:
        if not app.inactive:
            app.time_until_retry = random.randint(5, 60)
            print(f"I'll wait {app.time_until_retry}s")

            while app.time_until_retry > 0:
                time.sleep(1)
                app.time_until_retry -= 1
            with app.leader_lock:
                url = f'http://{app.leader}/health_check'
                try:
                    if app.leader == None:
                        raise
                    response = requests.get(url, timeout=timeout)
                    if response.status_code == 400:
                        raise
                except:
                    # Leader is dead
                    print("Leader is dead")
                    threading.Thread(target=election, args=(timeout,)).start()

app.bully_thread = threading.Thread(target=bully, args=(TIMEOUT,))
app.bully_thread.start()

@app.route("/")
def index():
    return render_template(
        'index.html', 
        hostname=HOSTNAME,
        higher=higher,
        lower=lower,
        halt_url=url_for('halt')
        )

@app.route("/halt")
def halt():
    with app.inactive_lock:
        if app.inactive:
            threading.Thread(target=election, args=(timeout,)).start()
        app.inactive = [True, False][app.inactive]
    return str(app.inactive)

@app.route("/health_check")
def health_check():
    with app.inactive_lock:
        if not app.inactive:
            return "OK"
    return "", 400
            

@app.route("/new_leader/<leader>")
def new_leader(leader):
    print(f"/new_leader/{leader}")
    with app.leader_lock:
        app.leader = leader
    return app.leader

@app.route("/start_election/<caller>")
def start_election(caller):
    print(f"/start_election/{caller}")
    with app.inactive_lock:
        if not app.inactive:
            threading.Thread(target=election, args=(TIMEOUT,)).start()
            return "OK"
        else:
            return "", 400

@socketio.on('event')
def handle_message(event):
    print(event)
    while True:
        emit("leader", {"leader": app.leader, "time_until_retry": app.time_until_retry})
        time.sleep(5)

@socketio.on('connect')
def on_connect(event):
    with app.inactive_lock:
        app.inactive = False
    print(event)

@socketio.on('disconnect')
def disconnect_details():
    with app.inactive_lock:
        app.inactive = True
    print("Disconnected")