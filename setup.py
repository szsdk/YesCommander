from setuptools import setup

setup(
    name="yescommander",
    version="0.1",
    author="szsdk",
    packages=["yescommander"],
    scripts=["scripts/yc"],
    install_requires=["py-term", "tcolorpy"],
)
