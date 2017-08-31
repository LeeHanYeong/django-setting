from setuptools import setup

setup(
    name='django-setting',
    version='0.1.4',
    description='Help set up project for Deployment, Docker, Secret key management',
    author='lhy',
    author_email='dev@azelf.com',
    license='MIT',
    packages=[
        'django_setting',
        'django_setting.docker',
        'django_setting.startproject',
        'django_setting.removeproject',
        'django_setting.settings',
        'django_setting.utils',
    ],
    package_data={
        'django_setting': [
            'files/*',
            'files/config/*',
            'files/config/docker/**/*',
            'files/config/nginx/**/*',
            'files/config/supervisor/**/*',
            'files/config/uwsgi/**/*',
            'codes/*',
            'codes/**/*',
        ]
    },
    zip_safe=False,
    scripts=['bin/django-setting'],
)
