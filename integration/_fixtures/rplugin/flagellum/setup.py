from setuptools import setup, find_packages

setup(
    name='flagellum',
    description='test plugin 1',
    version='1.0.0',
    author='Torsten Schmits',
    author_email='torstenschmits@gmail.com',
    license='MIT',
    packages=find_packages(),
    install_requires=[
        'ribosome~=11.1.2',
    ],
)
