import os
import shutil
import pathlib
from setuptools import setup, find_packages


REPO_ROOT = pathlib.Path(__file__).absolute().parent

shutil.rmtree(REPO_ROOT / "build", ignore_errors=True)
shutil.rmtree(REPO_ROOT / "dist", ignore_errors=True)

os.chdir(REPO_ROOT)
README = (REPO_ROOT / "README.md").read_text()

setup(
    name="mcctl",
    packages=find_packages(where="src", exclude=["tests"]),
    version="0.2.2",
    description="Manage, configure, create multiple Minecraft servers in a docker-like fashion.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/DaTurret/mcctl",
    author="DaTurret",
    author_email="mattcott14@hotmail.com",
    license="gpl-3.0",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.8",
        "Environment :: Console",
        "Operating System :: POSIX :: Linux"
    ],
    include_package_data=True,
    package_dir={'': 'src'},
    install_requires=['mcstatus'],
    setup_requires=['wheel'],
    entry_points={
        "console_scripts": [
            "mcctl=mcctl.__main__:main",
        ]
    },
)
