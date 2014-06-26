import sys
import os
import os.path as op

THIS_DIR = op.dirname(__file__)
sys.path.insert(0, op.join(THIS_DIR, ".."))

bind = "unix:/tmp/torrentpotato.t411-gunicorn-prod.sock"
workers = os.sysconf("SC_NPROCESSORS_ONLN") * 2 + 1
worker_class = "gevent"
timeout = 3600 * 4
pidfile = '/tmp/torrentpotato.t411-gunicorn-prod.pid'
