from setuptools import setup, find_packages


setup(
    name='lib_ddos_simulator',
    packages=find_packages(),
    version='0.1.0',
    authors=['Justin Furuness', 'Anna Gorbenko'],
    author_email=['jfuruness@gmail.com', 'agorbenko97@gmail.com'],
    url='https://github.com/agorbenko/lib_ddos.git',
    download_url='https://github.com/agorbenko/lib_ddos.git',
    keywords=['Furuness', 'Gorbenko', 'DDOS', 'Simulation'],
    install_requires=[
        'matplotlib',
        'tikzplotlib',
        'wheel',
        'setuptools',
        'tqdm',
        'pytest',
    ],
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 3'],
    entry_points={
        'console_scripts': 'ddos_sim = lib_ddos_simulator.__main__:main'},
    setup_requires=['pytest-runner'],
    tests_require=['pytest'],
)