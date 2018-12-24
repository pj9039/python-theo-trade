import setuptools

setuptools.setup(
    name='theo-trade',
    version='0.0.1',
    install_requires=['theo-framework'],
    url='https://github.com/TheodoreWon/python-theo-trade',
    license='MIT',
    author='Theodore Won',
    author_email='taehee.won@gmail.com',
    description='theo-trade',
    packages=['theo', 'theo.src.trade'],
    # long_description='GitHub : https://github.com/TheodoreWon/python-theo-trade',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    zip_safe=False,
)

'''
NOTE: How to make a package and release the software
0. pip install setuptools, pip install wheel, pip install twine
1. python setup.py bdist_wheel
2. cd dist
3. twine upload xxx.whl
'''
