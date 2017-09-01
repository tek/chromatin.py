from setuptools import setup, find_packages

version_parts = (0, 7, 0)
version = '.'.join(map(str, version_parts))

setup(
    name='chromatin',
    description='neovim python plugin manager',
    version=version,
    author='Torsten Schmits',
    author_email='torstenschmits@gmail.com',
    license='MIT',
    url='https://github.com/tek/chromatin',
    include_package_data=True,
    packages=find_packages(exclude=['unit', 'unit.*', 'integration', 'integration.*']),
    install_requires=[
        'ribosome~=10.16.2',
    ],
    tests_require=[
        'kallikrein',
    ],
)
