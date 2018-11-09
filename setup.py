#!/usr/bin/python3

import os

from setuptools import find_packages, setup


def get_requirements():
    with open("./requirements.txt") as file:
        return file.readlines()

# https://packaging.python.org/guides/single-sourcing-package-version/
version = {}
with open("./ansible_bender/version.py") as fp:
    exec(fp.read(), version)

long_description = ''.join(open('README.md').readlines())


setup(
    name='ansible-bender',
    version=version["__version__"],
    description="A tool which builds container images using Ansible playbooks.",
    long_description=long_description,
    # long_description_content_type='text/markdown',
    packages=find_packages(exclude=['tests']),
    python_requires='>=3.6',
    install_requires=get_requirements(),
    entry_points='''
        [console_scripts]
        ab=ansible_bender.cli:main
    ''',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Software Development',
        'Topic :: Utilities',
    ],
    keywords='containers,ansible,buildah',
    author='Tomas Tomecek',
    author_email='tomas@tomecek.net',
    url='https://github.com/TomasTomecek/ansible-bender',
    include_package_data=True,
)
