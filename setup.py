import os
import shutil
import pathlib
from setuptools import setup, find_packages
from src.mcctl import __version__


REPO_ROOT = pathlib.Path(__file__).absolute().parent

shutil.rmtree(REPO_ROOT / "build", ignore_errors=True)
shutil.rmtree(REPO_ROOT / "dist", ignore_errors=True)

os.chdir(REPO_ROOT)
README = (REPO_ROOT / "README.md").read_text()

setup(
    name="mcctl",
    packages=find_packages(where="src", exclude=["test*"]),
    version=__version__,
    description="Manage, configure, and create multiple Minecraft servers easily with a command-line interface.",
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
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Environment :: Console",
        "Operating System :: POSIX :: Linux"
    ],
    python_requires='>=3.8',
    include_package_data=True,
    package_dir={'': 'src'},
    install_requires=[
        'mcstatus<7.0.0,>=6.0.1',
        'requests<3.0.0,>=2.25.0',
        'pystemd'
    ],
    setup_requires=['wheel'],
    entry_points={
        "console_scripts": [
            "mcctl=mcctl.__main__:main",
        ]
    },
)
