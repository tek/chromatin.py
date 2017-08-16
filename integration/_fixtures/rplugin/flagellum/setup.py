from setuptools import setup, find_packages

setup(
    name='tubbs',
    description='ebnf-based text objects',
    version='1.0.0',
    author='Torsten Schmits',
    author_email='torstenschmits@gmail.com',
    license='MIT',
    packages=find_packages(),
    install_requires=[
        'ribosome>=10.5.1',
    ],
)
