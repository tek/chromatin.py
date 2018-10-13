from setuptools import setup, find_packages


def spec_setup(name: str, description: str='test plugin') -> None:
    setup(  # type: ignore
        name=name,
        description=description,
        version='1.0.0',
        author='Torsten Schmits',
        author_email='torstenschmits@gmail.com',
        license='MIT',
        packages=find_packages(),
        install_requires=[
            'ribosome~=13.0.1a2',
        ],
    )
