# sport-catalog

## Table of Contents

- [Table of Contents](#table-of-contents)
- [Intro](#intro)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Instructions](#instructions)

## Intro

This application runs a small website for a Sporting Goods store. It has the functionallity to Display, Add, Update and Delete sporting good products that belong to specific categories. 

The initial page shows each category along with the three most recently modified items and gives the user the ability to select either the category or the displayed item. If the category is displayed, the items that belong to that category is displayed. If an item is selected, detail about that item is displayed.

The user also has the ability to authenticate through google. Once the user is authenticated using googe, he/she has the ability to add an item to the database. Once an authenticated user adds an item, he/she is authorized to edit or delete that item. The authenticated user only has the authorization to edit/delete items that they have added.

## Prerequisites

* asn1crypto==0.24.0
* certifi==2019.9.11
* chardet==3.0.4
* Click==7.0
* configparser==3.5.0b2
* cryptography==2.3
* docopt==0.6.2
* entrypoints==0.2.3.post3
* enum34==1.1.6
* Flask==1.1.1
* httplib2==0.13.1
* idna==2.8
* ipaddress==1.0.17
* itsdangerous==1.1.0
* Jinja2==2.10.1
* keyring==15.1.0
* keyrings.alt==3.1
* MarkupSafe==1.1.1
* oauth2client==4.1.3
* pipreqs==0.4.9
* pyasn1==0.4.7
* pyasn1-modules==0.2.6
* pycrypto==2.6.1
* PyGObject==3.30.1
* pyxdg==0.25
* requests==2.22.0
* rsa==4.0
* SecretStorage==2.3.1
* six==1.12.0
* SQLAlchemy==1.3.8
* urllib3==1.25.6
* Werkzeug==0.15.6
* yarg==0.1.9


## Installation

To clone software:
```
git clone https://github.com/edwilsonny/sport-catalog.git
```
To start server:
```
cd/sport-catalog
./project.py
```

## Instructions

Launch a web browser and type: http://localhost:8080

For a JSON listing of all item data - type: http://localhost:8080/item/JSON/

For a JSON listing of a given Item  - type: http://localhost:8080/item/JSON/*item_id*/
     Where: *item_id* is the item_id of the product.


[(Back to TOC)](#table-of-contents)
