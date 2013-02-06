from setuptools import setup, find_packages
import sys, os
# This is a fix for nose sys.modules manipulation bug. Remove after nose fixed
try:
    import multiprocessing
except ImportError:
    pass

version = '0.1'

setup(name='jira',
      version=version,
      description="Jira command line tools",
      long_description="""\
Command line tools for Jira.""",
      classifiers=[], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='jira command line',
      author='Jeremy Stark',
      author_email='jlstark@gmail.com',
      url='',
      license='',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      test_suite='nose.collector',
      tests_require=[
          'nose',
      ],
      install_requires=[
          'BeautifulSoup',
          'numpy',
          'matplotlib',
          'zope.component',
          'ZODB3',
          'repoze.catalog',
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
