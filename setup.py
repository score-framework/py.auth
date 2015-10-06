import os
from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.txt')) as f:
    README = f.read()

setup(
    name='score.auth',
    version='0.3.2',
    description='Authorization and Authentication for The SCORE Framework',
    long_description=README,
    author='strg.at',
    author_email='support@strg.at',
    url='http://strg.at',
    keywords='web wsgi bfg pylons pyramid',
    packages=['score.auth'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'score.init >= 0.2.2',
        'score.ctx >= 0.2.4',
    ],
)
