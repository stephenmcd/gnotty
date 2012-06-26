
from setuptools import setup, find_packages

from gnotty import __version__


setup(
    name="Gnotty",
    version=__version__,
    author="Stephen McDonald",
    author_email="stephen.mc@gmail.com",
    description="Gnotty ties the knot between the web and IRC. It is a web "
                "client and message archive for IRC.",
    long_description=open("README.rst").read(),
    license="BSD",
    url="http://gnotty.jupo.org/",
    zip_safe=False,
    include_package_data=True,
    packages=find_packages(),
    install_requires=[
        "gevent-socketio==0.3.5-beta",
        "python-irclib==0.4.6",
        "daemon==1.0",
        "sphinx-me",
    ],
    entry_points="""
        [console_scripts]
        gnottify=gnotty.server:run
    """,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ]
)
