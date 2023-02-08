from setuptools import setup

setup(
    name='streamydeck',
    version='1.1.0',
    description='Streamy Deck',
    author='Philippe Remy',
    license='MIT',
    long_description_content_type='text/markdown',
    long_description=open('README.md').read(),
    packages=['streamydeck'],
    install_requires=['streamdeck', 'pillow']
)
