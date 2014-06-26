from t411.app import app
from t411.api import *

from werkzeug.contrib.fixers import ProxyFix
import os

# -----------------------------------------------------------------------------

app.debug = not os.environ.get('PROD')
if not app.debug:
    app.wsgi_app = ProxyFix(app.wsgi_app)

if __name__ == '__main__':
    app.run()
