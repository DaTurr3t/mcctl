import pathlib
from setuptools import setup
import os

os.chdir(os.path.dirname(__file__))

repoRoot = pathlib.Path(__file__).absolute().parents[1]
README = (repoRoot / "README.md").read_text()

setup(
    name="mcctl",
    packages=["mcctl"],
    version="0.1.0",
    description="Manage, configure, create multiple Minecraft servers in a docker-like fashion.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/DaTurret/mcctl",
    author="DaTurret",
    author_email="mattcott14@hotmail.com",
    license="gpl-3.0",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: GNU General Public License v3.0",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.8",
        "Environment :: Console",
        "Operating System :: POSIX :: Linux"
    ],
    include_package_data=True,
    setup_requires=['wheel'],
    entry_points={
        "console_scripts": [
            "mcctl=mcctl.__main__:main",
        ]
    },
)
