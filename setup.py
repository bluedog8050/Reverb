import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="NeoReverb-Bluedog8050", # Replace with your own username
    version="0.5.0",
    author="Derek Peterson",
    author_email="deniableassetsgm@gmail.com",
    description="A Play by Post helper bot For Discord, tooled for running my Shadowrun 5th edition game.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/bluedog8050/NeoReverb",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='3.6',
)