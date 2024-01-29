from setuptools import setup, find_packages
import os

# Read the version from your __version__.py file
version = {}
with open(os.path.join("__version__.py")) as f:
    exec(f.read(), version)

# Dynamically read dependencies from requirements.txt
with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='rewst_remote_agent',
    version=version['__version__'],
    author='Rewst',
    author_email='tim@rewst.io',
    description='An RMM-agnostic remote agent using the Azure IoT Hub',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/rewstapp/rewst_remote_agent',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License', # Update if you have a different license
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Operating System :: Microsoft :: Windows',
        # Add other classifiers as needed
    ],
    install_requires=required,
)
