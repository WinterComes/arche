from setuptools import setup, find_packages


setup(
    packages=find_packages(),
    package_data={
        'templates': ['arche/templates/*.html'],
    },
)
