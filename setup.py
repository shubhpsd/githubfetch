from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="githubfetch",
    version="1.0.3",
    author="Shubham Prasad",
    author_email="shubhampsd@tuta.io",
    description="Terminal-based GitHub profile viewer",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/shubhpsd/githubfetch",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    install_requires=[
        "requests",
        "pillow",
        "imgcat",
    ],
    entry_points={
        "console_scripts": [
            "githubfetch=githubfetch:main",
        ],
    },
)