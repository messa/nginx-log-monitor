#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name='nginx-log-monitor',
    version='0.0.1',
    description='Nginx Log Monitor',
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    packages=find_packages(exclude=['doc', 'tests*']),
    install_requires=[
        'aiohttp',
        'pyyaml',
    ],
    entry_points={
        'console_scripts': [
            'nginx-log-monitor=nginx_log_monitor:nginx_log_monitor_main'
        ],
    })
