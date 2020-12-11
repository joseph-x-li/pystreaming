import setuptools

with open("README.md", 'r') as fh:
    long_description = fh.read()

with open("requirements.txt", 'r') as fh:
    install_requires = fh.read()

setuptools.setup(
    name="pystreaming",
    version=open("VERSION.txt").read().strip(),
    author="Joseph Li",
    author_email="jxli@andrew.cmu.edu",
    description="Video + Audio streaming done with ZMQ",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/joseph-x-li/pystreaming",
    packages=setuptools.find_packages(),
    install_requires=install_requires,
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)