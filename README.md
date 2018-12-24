# theo-trade

It is the API what makes using trade related API easy.

Kiwoom is the API to control Kiwoom open API.
Kiwoom provides various interfaces, but the interfaces are not matched with others.
This module wants to support same interfaces for trade API.

I am likely waiting a any kind of contribution.


# Theo series

Framework : pip install theo-framework, https://github.com/TheodoreWon/python-theo-framework  
Database : pip install theo-database, https://github.com/TheodoreWon/python-theo-database  
Message : pip install theo-message, https://github.com/TheodoreWon/python-theo-message  
Trade : pip install theo-trade, https://github.com/TheodoreWon/python-theo-trade


# How to use

Install the framework  
> pip install theo-trade

Print docstrings  
> from theo.trade import Kiwoom, KiwoomCtrl  
> print(Kiwoom.&#95;&#95;doc&#95;&#95;)  
> print(KiwoomCtrl.&#95;&#95;doc&#95;&#95;)


# Authors

Theodore Won - Owner of this project


# License

This project is licensed under the MIT License - see the LICENSE file for details


# Versioning

Basically, this project follows the 'Semantic Versioning'. (https://semver.org/)  
But, to notify new feature, I added several simple rules at the Semantic Versioning.  
I would like to call 'Theo Versioning'.

- Version format is MAJOR.MINOR.PATCH  
- MAJOR version is increased when API is changed or when new feature is provided.  
  - New feature does not affect a interface.  
  - But, to notify new feature, New feature makes MAJOR version up.  
  - Before official version release (1.0.0), MAJOR is kept 0 and MINOR version is used.  
- MINOR version is up when the API is added. (New functionality)  
- PATCH version is lifted when bug is fixed, test code is uploaded, comment or document or log is updated.  
