from setuptools import setup

setup(
    name="yescommander",
    version="0.1",
    author="szsdk",
    packages=["yescommander"],
    scripts=["scripts/yc"],
    install_requires=["prompt_toolkit", "pyperclip"],
    tests_requires=["pytest"],
    data_files=[("example", ["yescommander/example/yc_rc.py"])],
    include_package_data=True,
)
