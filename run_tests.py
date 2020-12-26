#!/usr/bin/env python
# -*- coding: utf-8 -*-
if __name__ == '__main__':
    import pytest
    import sys
    package_name = 'mkinit'
    pytest_args = [
        '-p', 'no:doctest',
        '--cov-config', '.coveragerc',
        '--cov-report', 'html',
        '--cov-report', 'term',
        '--cov=' + package_name,
        '--xdoctest',
        package_name, 'tests'
    ]
    pytest_args = pytest_args + sys.argv[1:]
    pytest.main(pytest_args)
