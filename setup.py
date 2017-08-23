from setuptools import setup, find_packages

version_parts = (0, 1, 0)
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
    packages=find_packages(exclude=['unit', 'unit.*', 'integration', 'integration.*']),  # type: ignore
    install_requires=[
        'amino>=10.8.1',
        'ribosome>=10.10.0',
    ],
    tests_require=[
        'kallikrein',
    ],
)
