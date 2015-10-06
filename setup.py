import os
from setuptools import setup

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.txt')) as f:
    README = f.read()

setup(
    name='score.auth',
    version='0.3.3',
    description='Authorization and Authentication for The SCORE Framework',
    long_description=README,
    author='strg.at',
    author_email='support@strg.at',
    url='http://strg.at',
    keywords='score framework authentication authorization pyramid',
    packages=['score.auth'],
    namespace_packages=['score'],
    zip_safe=False,
    license='LGPL',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Framework :: Pyramid',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General '
            'Public License v3 or later (LGPLv3+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Security',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
    ],
    include_package_data=True,
    install_requires=[
        'score.init >= 0.2.2',
        'score.ctx >= 0.2.4',
    ],
)
