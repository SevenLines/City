from invoke import task

@task
def deploy(c):
    with c.cd('~/projects/city'):
        c.run("git pull")
        with c.prefix(". /usr/local/bin/virtualenvwrapper.sh; workon city"):
            c.run("pip install -r requirements.txt")
        with c.cd("client"):
            c.run("ls")
            c.run("npm install")
            c.run("npm run build")
        c.run("touch uwsgi.ini")
