import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="statinf",
    version="1.3.0",
    author="Florian Felice",
    author_email="florian.felice@outlook.com",
    description="A library for statistics and causal inference",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://www.florianfelice.com/statinf",
    packages=setuptools.find_packages(),
    install_requires=[
          "pandas>=0.24.1",
          "numpy>=1.16.3",
          "scipy>=1.2.1",
          "jax>=0.2.10",
          "jaxlib>=0.1.61",
          "pycof>=1.0.19",
          "matplotlib>=3.1.1"
      ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)