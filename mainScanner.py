import sys
import os
import socket
import subprocess
import json
from datetime import datetime
import threading
import logging
from flask import Flask, render_template, request

# Ensure the 'multi' module is found
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

try:
    from multi.scanner_thread import split_processing
except ModuleNotFoundError:
    print(
        "Error: 'multi.scanner_thread' module not found. Ensure the 'multi' directory contains 'scanner_thread.py' and '__init__.py'.")
    sys.exit(1)

app = Flask(__name__)


@app.route('/')
def homepage():
    return render_template('index.html')


@app.route('/input', methods=["POST"])
def scan_ports():
    if request.method == "POST":
        try:
            remoteServer = request.form["host"]
            remoteServerIP = socket.gethostbyname(remoteServer)
            range_low = int(request.form["range_low"])
            range_high = int(request.form["range_high"])
        except (KeyError, ValueError, socket.gaierror) as e:
            return f"Invalid input: {str(e)}"
    else:
        return "Invalid request method"

    print(f"Scanning {remoteServerIP} from port {range_low} to {range_high}")

    def get_absolute_path(relative_path):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)

    try:
        with open(get_absolute_path('../config.json')) as config_file:
            config = json.load(config_file)
            CONST_NUM_THREADS = int(config['thread']['count'])
    except (IOError, ValueError):
        return "Error: Unable to read or parse config.json"

    ports = list(range(range_low, range_high))
    open_ports = []

    def scan_port(port):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex((remoteServerIP, port)) == 0:
                open_ports.append(f"Port {port}: Open")
                print(f"Port {port}: Open")

    split_processing(ports, CONST_NUM_THREADS, scan_port, range_low, range_high)

    return render_template('index.html', portnum=open_ports, host=remoteServerIP, range_low=range_low,
                           range_high=range_high)


if __name__ == '__main__':
    app.run(debug=True)
