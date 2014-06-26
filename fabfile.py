from __future__ import with_statement

from fabric.api import run, sudo, cd, local, env, prefix, put
from fabric.contrib import files
from fabric.decorators import task

from datetime import datetime
import os.path as op

# -----------------------------------------------------------------------------

NB_RELEASES = 10

WEBSITE_URL = "http://torrentpotato-t411.thomaskliszowski.fr"
PROJECT_NAME = "torrentpotato.t411"
REPO_GIT = "https://github.com/ThomasKliszowski/torrentpotato.t411.git"

local_base_dir = op.join(op.dirname(__file__))

# -----------------------------------------------------------------------------

def host(env, host_string, branch, environment):
    env.host_string = host_string
    env.user = 'fabric'

    env.base_dir = "/var/www/%s" % PROJECT_NAME
    env.repos_dir = op.join(env.base_dir, "src")

    env.deployed_branch = branch
    env.supervisor_tasks = ['%s-gunicorn-%s' % (PROJECT_NAME, environment)]
    env.gunicorn_pid = '/tmp/%s-gunicorn-%s.pid' % (PROJECT_NAME, environment)
    env.deploy_dir = op.join(env.base_dir, environment)
    env.current_path = op.join(env.deploy_dir, "current")
    env.previous_path = op.join(env.deploy_dir, "previous")

@task
def prod():
    host(env,
        host_string="thomaskliszowski.fr",
        branch="master",
        environment="prod"
    )

@task
def preprod():
    host(env,
        host_string="thomaskliszowski.fr",
        branch=get_current_branch(),
        environment="preprod"
    )

# -----------------------------------------------------------------------------

@task
def deploy():
    tag = datetime.now().strftime("%Y%m%d%H%M%S")

    with cd(env.repos_dir):
        run("git fetch")
        run("git checkout %s" % env.deployed_branch)
        run("git reset origin/%s --hard" % env.deployed_branch)
        run("git fetch --tags")
        run("git pull")
        
        release_path = op.join(env.deploy_dir, "releases", tag)
        run('mkdir %s' % release_path)
        run("git archive HEAD | tar x -C '%s'" % release_path)

    with virtualenv():
        sudo("pip install -r %s" % op.join(env.repos_dir, "requirements.txt"))
    
    # switch simlinks
    if files.exists(env.current_path):
        target = run("readlink %s" % env.current_path)
        run("ln -sfn %s %s" % (target, env.previous_path))
    run("ln -sfn %s %s" % (release_path, env.current_path))
    
    wash_releases()
    reload_supervisor()

@task
def rollback():
    if files.exists(env.previous_path):
        target = run("readlink %s" % env.previous_path)
        run("ln -sfn %s %s" % (target, env.current_path))
    
    reload_supervisor()

@task
def update_server():
    # Set prod and preprod folders
    for folder in ['prod/releases', 'preprod/releases']:
        if not files.exists(op.join(env.base_dir, folder)):
            run("mkdir -p %s" % op.join(env.base_dir, folder))

    for environment in ['prod', 'preprod']:
        # Set venv/
        if not files.exists(op.join(env.base_dir, environment, 'venv')):
            run("virtualenv %s" % op.join(env.base_dir, environment, 'venv'))

    # Set src/
    if not files.exists(op.join(env.base_dir, 'src')):
        run("git clone %s %s" % (REPO_GIT, op.join(env.base_dir, 'src')))

    # Push supervisor
    conf_file = "%s.conf" % PROJECT_NAME
    put(op.join(local_base_dir, "etc", "supervisor", conf_file), "/tmp/%s" % conf_file)
    sudo("mv /tmp/%(file)s /etc/supervisor/conf.d/%(file)s" % {'file':conf_file})

    # Push nginx conf
    put(op.join(local_base_dir, "etc", "nginx", PROJECT_NAME), "/tmp/%s-nginx-conf" % PROJECT_NAME)
    sudo("mv /tmp/%(name)s-nginx-conf /etc/nginx/sites-available/%(name)s" % {'name':PROJECT_NAME})
    sudo("ln -sf /etc/nginx/sites-available/%(name)s /etc/nginx/sites-enabled/%(name)s" % {'name':PROJECT_NAME})

    sudo("supervisorctl update")
    reload_gunicorn()
    reload_supervisor()
    reload_nginx()

# -----------------------------------------------------------------------------

def virtualenv():
    return prefix('source %(deploy_dir)s/venv/bin/activate' % env)

def get_current_branch():
    branches = local("git branch", capture=True)
    local_branch = [b for b in branches.split('\n') if b.startswith('*')][0]
    return local_branch.split()[1]

def wash_releases():
    releases_path = op.join(env.deploy_dir, "releases")
    with cd(releases_path):
        releases = run("ls").split("\t")
        releases.sort()
        while len(releases) > NB_RELEASES:
            run("rm -rf %s" % releases[0])
            releases.pop(0)

def reload_supervisor():
    for supervisor_task in env.supervisor_tasks:
        sudo("supervisorctl restart %s" % supervisor_task)

def reload_gunicorn():
    if files.exists(env.gunicorn_pid):
        sudo("kill -HUP `cat %s`" % env.gunicorn_pid)

def reload_nginx():
    sudo("/etc/init.d/nginx reload")
