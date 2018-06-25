from invoke import task

@task
def deploy(c):
    with c.cd('~/projects/city'):
        c.run("git pull")
        c.run("ls")
        with c.prefix(". /usr/local/bin/virtualenvwrapper.sh; workon city"):
            c.run("pip install -r requirements.txt")
        with c.cd("client"):
            c.run("npm run install")
            c.run("npm run build")
