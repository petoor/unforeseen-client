import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()


setuptools.setup(
    name='unforeseen',
    version='0.0.1',
    author='Peter Lunding Jensen',
    author_email='peterlundingj@gmail.com',
    description='Initial setup',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/petoor/unforseen-client',
    project_urls = {
        "Issues": "https://github.com/petoor/unforseen-client/issues"
    },
    license='MIT',
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],

    python_requires='>=3.6'
)
