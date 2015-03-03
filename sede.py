"""!sede <command> executes the <command> on pouliradio"""
import json
import re
from urllib import quote
import sys
import requests
from bs4 import BeautifulSoup
import subprocess as sp

JSON = '/home/poul/.remotecmd.json'

def execute(command):
    """execs the given command on pouliradio"""
    try:
        with open(JSON) as infile:
            bindings = json.load(infile)
    except IOError:
        pass  # file not yet generated
    except ValueError:
        print 'WRONG JSON!'

    if command in bindings.keys():
        cmd = bindings[command]
        if cmd:
             print('pressed: %s' % command)
             sp.call(cmd, shell=True)

def on_message(msg, server):
    text = msg.get("text", "")
    match = re.findall(r"!sede (.*)", text)
    if not match: return

    command = match[0]
    return execute(command)
