from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.readlines()

long_description = "Minimalistic ros-compatible python bridge."

setup(
    name="ros0",
    version="1.0.0",
    author="Ibrahim Abdulhafiz",
    author_email="ibrahim@g0ai.com",
    url="https://github.com/G0ai/ros0",
    description="Minimalistic ros-compatible python bridge.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    packages=find_packages(),
    package_dir={
        'ros0': 'ros0'
    },
    entry_points={"console_scripts": ["ros0 = ros0.main:main"]},
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
    keywords="ros0 g0ai zmq",
    install_requires=requirements,
    zip_safe=False,
)