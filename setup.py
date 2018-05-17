from setuptools import setup
from os.path import dirname, realpath
#from pip import main as pip

try:
    from git.repo.base import Repo
except ImportError:
    # install from pip on failure to import -- This is a dependency of the
    # install script itself.
#    if pip(["install", "gitpython"]):
        raise

vcs = Repo(dirname(realpath(__file__)))
#urls = [u for u in vcs.remote().urls]
#if len(urls) < 1:
#    raise NotImplementedError()
versionnum = len([c for c in vcs.iter_commits()])
versionstr = "0.0.%d" % versionnum

setup(
    name="ShoppingList",
    version=versionstr,
    author="D. Scott Boggs",
    author_email="scott@tams.tech",
    description="A ReSTful list API.",
    license="GPL-v3.0",
    keywords="shopping list api rest http flask",
    packages=["interface-api", "tests"],
    tests_require=["pytest"],
    install_requires=[
        "Flask",
        "flask-sqlalchemy",
    ],
    setup_requires=['pytest-runner']
)
