from distutils.core import setup
import os.path
import subprocess

from setuptools import setup

__version__ = '0.0.1'

setup(name='morpheus-sos-plugin',
      version=__version__,
      description='Sosreport plugin to gather data about Morpheus and components',
      long_description="""Sosreport is a collection of scripts that gathers system and configuration information.
                   This package contains the Morpheus plugin for sosreport to send to support when diagnosing issues.""",
      author="Nick Celebic",
      author_email="nick@celebic.net",
      url='https://github.com/tryfan/morpheus-sos-plugin',
      packages=['sos.plugins', 'sos'],
      keywords="sosreport morpheus",
      license='MIT',
      classifiers=[
          "Development Status :: 1 - Planning",
          "Environment :: Plugins",
          "Intended Audience :: Customer Service",
          "Intended Audience :: System Administrators",
          "Operating System :: POSIX :: Linux",
          "License :: OSI Approved :: MIT License",
          "Programming Language :: Python :: 2",
      ],
      platforms='Posix')
