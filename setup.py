import os

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

design_path = 'src/picture_comparator/design'
view_path = 'src/picture_comparator/view'

for file in os.listdir(view_path):
    if file.endswith('.ui'):
        new_file = file[:-2] + '_ui.py'
        os.system(f'pyside6-uic {os.path.join(design_path, file)} > {os.path.join(view_path, new_file)}')

scripts_path = 'bin'
scripts = [os.path.join(scripts_path, f) for f in os.listdir(scripts_path)]

setup(
    name='picture_comparator',
    version='0.1.6',
    author='Armas',
    author_email='halftough29A@gmail.com',
    description='Find similar images in a set.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: GNU GENERAL PUBLIC LICENSE',
        'Operating System :: OS Independent'],
    packages=find_packages(where="src"),
    install_requires=[
        'requests',
        'importlib; python_version == "3.7"',
    ],

    scripts=scripts,
    package_dir={
        'picture_comparator': 'src/picture_comparator'
    },
    package_data={
        'picture_comparator.resources': ['edit-delete.svg']
    }
)
