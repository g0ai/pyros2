from setuptools import setup, find_packages
from pathlib import Path

Path(Path.home() / "pyros2").mkdir(parents=True, exist_ok=True)

with open("requirements.txt") as f:
    requirements = f.readlines()

long_description = "In order to make use of all the ROS features \
    (pub/sub, recording and playback, autodiscovery, \
    remote machine communication, standarized topics, etc.), \
    pyros2 was developed using the zmq backend to work flawlessly out of the box."


setup(
    name="pyros2",
    version="0.1.0",
    author="Ibrahim Abdulhafiz",
    author_email="ibrahim@g0ai.com",
    url="https://github.com/G0ai/pyros2",
    description="A minimalistic pythonic module as an alternative to ROS.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    packages=find_packages(),
    package_dir={
        'pyros2': 'pyros2'
    },
    entry_points={"console_scripts": ["pyros2 = pyros2.main:main"]},
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
    keywords="pyros2 ros ros2 g0ai zmq",
    install_requires=requirements,
    zip_safe=False,
)
