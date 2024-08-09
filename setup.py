from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in jibu_inc/__init__.py
from jibu_inc import __version__ as version

setup(
	name="jibu_inc",
	version=version,
	description="Jibu Inc Custom Application",
	author="Chris",
	author_email="info@pointershub.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
