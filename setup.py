from setuptools import setup


setup(
    name="btrfs-quota",
    version="0.1.0",
    packages=[""],
    description="BtrFS quota management helper",
    platforms=["POSIX"],
    author="Dmitrry Orlov",
    author_email="me@mosquito.su",
    keywords=["btrfs", "tools", "tool", "quota", "qgroup"],
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Topic :: Internet",
        "Topic :: Software Development",
        "Topic :: Software Development :: Libraries",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Operating System :: MacOS",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
    python_requires=">3.5.*",
    install_requires=[
        "humanize", "texttable"
    ],
    entry_points={
        "console_scripts": [
            "btrfs-quota = btrfs_quota:main",
        ],
    },
)
