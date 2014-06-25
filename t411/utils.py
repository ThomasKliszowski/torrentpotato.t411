import os

# -----------------------------------------------------------------------------

def get_version():
    path = os.path.join(os.path.dirname(__file__), '..', 'VERSION.txt')
    with open(path, 'r') as fp:
        version = fp.read()
    return version

def require_params(request, params):
    for param in params:
        if param not in request.args:
            raise Exception("You must pass this GET param: %s" % param)
    return request.args
