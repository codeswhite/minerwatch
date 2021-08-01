import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="minerwatch",
    version="0.4.0",
    description="Get telegram notifications about disconnections and other performance losses in your ethermine.org pool",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
    install_requires=[
        'requests',
    ],
    entry_points={
        'console_scripts': [
            'minerwatch = minerwatch:main',
        ],
    },
    author="Max G",
    author_email="max3227@gmail.com",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages()
)
