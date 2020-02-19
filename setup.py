import setuptools

with open("README.md") as f:
	long_description = f.read()

setuptools.setup(
	name="telstra-smart-modem",
	version="1.0.0",
	author="hatdz",
	description="Library to retrieve information from a Telstra Smart Modem.",
	license="MIT",
	long_description=long_description,
	long_description_content_type="text/markdown",
	url="https://github.com/hatdz/telstra-smart-modem",
	packages=setuptools.find_packages(),
	classifiers=[
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
	],
	python_requires='>=3.6',
	install_requires=[
		'requests>=2.22,<3',
		'beautifulsoup4>=4.8.2,<5'
	]
)
