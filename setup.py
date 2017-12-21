from setuptools import setup

setup(
    name='Apache+PHP Develoment Server',
    version='1.3.1',
    py_modules=['apds'],
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        apds=apds:cli
    ''',
)
