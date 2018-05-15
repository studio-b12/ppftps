from setuptools import setup

def readme():
    with open('README') as f:
        return f.read()

setup(name='ppftps',
    version='0.2.1',
    description='Push directories over a secured FTP connection.',
    long_description=readme(),
    long_description_content_type='text/markdown',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: File Transfer Protocol (FTP)',
    ],
    keywords='cli ftp ftps keepass push pull sync util',
    url='https://github.com/studio-b12/ppftps',
    author='Christoph Polcin',
    author_email='c.polcin@studio-b12.de',
    license='BSD',
    packages=['ppftps'],
    install_requires=[
        'ftputil',
    ],
    dependency_links=['https://codeload.github.com/pschmitt/pykeepass/tar.gz/2.8.1'],
    scripts=['bin/ppftps'],
    entry_points = {
        'console_scripts': ['ppftps=ppftps:cli'],
    },
    include_package_data=True,
    zip_safe=False,
    project_urls={
        'Bug Reports': 'https://github.com/studio-b12/ppftps/issues',
        'Source': 'https://github.com/studio-b12/ppftps',
    },
    python_requires='>=3',
)

