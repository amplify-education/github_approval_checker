from __future__ import print_function

"""setup.py controls the build, testing, and distribution of the egg"""

from setuptools import setup, find_packages
import re
import os.path


VERSION_REGEX = re.compile(r"""
    ^__version__\s=\s
    ['"](?P<version>.*?)['"]
""", re.MULTILINE | re.VERBOSE)

VERSION_FILE = os.path.join("github_approval_checker", "version.py")


def get_long_description():
    """Reads the long description from the README"""
    # Attempt to convert the markdown readme to a reStructuredText one to work with legacy PyPi
    try:
        import pypandoc
        return pypandoc.convert('README.md', 'rst')
    except Exception as ex:
        print("Unable to convert README to RST: '{}'".format(ex))
        return ""


def get_version():
    """Reads the version from the package"""
    with open(VERSION_FILE) as handle:
        lines = handle.read()
        result = VERSION_REGEX.search(lines)
        if result:
            return result.groupdict()["version"]
        else:
            raise ValueError("Unable to determine __version__")


def get_requirements():
    """Reads the installation requirements from requirements.pip"""
    with open("requirements.pip") as reqfile:
        return [line for line in reqfile.read().split("\n") if not line.startswith(('#', '-'))]

setup(
    name='github_approval_checker',
    version=get_version(),
    description="Lambda-based webhook for overriding failed status checks.",
    long_description=get_long_description(),
    # Get strings from http://www.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],
    keywords='',
    author='Amplify Education',
    author_email='github@amplify.com',
    url='https://github.com/amplify-education/github_approval_checker',
    license='MIT',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=get_requirements(),
    test_suite='nose.collector',
)
