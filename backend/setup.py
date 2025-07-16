"""
Setup script for GoatMeasure Pro Django backend
"""
from setuptools import setup, find_packages

setup(
    name='goat-measure-pro',
    version='1.0.0',
    description='Django backend for GoatMeasure Pro morphometric analysis',
    author='Your Name',
    author_email='your.email@example.com',
    packages=find_packages(),
    install_requires=[
        'Django>=5.0.0',
        'djangorestframework>=3.14.0',
        'django-cors-headers>=4.3.0',
        'python-decouple>=3.8',
        'psycopg2-binary>=2.9.0',
        'Pillow>=10.0.0',
        'celery>=5.3.0',
        'redis>=5.0.0',
        'django-extensions>=3.2.0',
        'python-dotenv>=1.0.0',
        'dj-database-url>=2.1.0',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Framework :: Django',
        'Framework :: Django :: 5.0',
    ],
    python_requires='>=3.9',
)