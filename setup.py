from setuptools import setup, find_namespace_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name='spatify',
      version='0.1.0',
      author='Bruno Gola',
      author_email='me@bgo.la',
      description='Spatial audio over WebRTC',
      long_description=long_description,
      long_description_content_type="text/markdown",
      url="https://github.com/bgola/spatify",
      packages=find_namespace_packages(include=['spatify', 'spaitfy.*']),
	  classifiers=[
          "Programming Language :: Python :: 3",
          "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
          "Operating System :: OS Independent",
		  "Framework :: AsyncIO",
      ],
	  install_requires=['python-osc'],
      keywords='webrtc audio osc opensoundcontrol',
      python_requires='>=3.7',
      entry_points={
          'console_scripts': [
              'spatify = spatify.__main__:main'
          ]
      },
      )
