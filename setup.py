from setuptools import setup, find_packages, os

here = os.path.abspath(os.path.dirname(__file__))
exec(open(os.path.join(here, 'oktaawscli/version.py')).read())

setup(
    name='okta-awscli',
    version=__version__,
    description='Provides a wrapper for Okta authentication to awscli forked and slightly modified from jmhale/okta-awscli',
    packages=find_packages(),
    license='Apache License 2.0',
    author='Richard Rodgers',
    author_email='rich@motelrich.com',
    url='https://github.com/richard-9000/okta_awscli',
    entry_points={
        'console_scripts': [
            'okta-awscli=oktaawscli.okta_awscli:main',
        ],
    },
    install_requires=[
        'requests',
        'click',
        'bs4',
        'boto3',
        'ConfigParser',
        ],
    extras_require={
        'U2F': ['python-u2flib-host']
    },
)
