from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(name='nsi.sam',
      version=version,
      description="",
      long_description="""\
""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Gabriel M. Monnerat',
      author_email='gabrielmonnerat@gmail.com',
      url='',
      license='',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
        "zope.interface",
        "simplejson",
        "cyclone",
        "twisted",
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
