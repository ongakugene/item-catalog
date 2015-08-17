# Item Catalog
### Repository: item-catalog
#### *Note : This repository contains the code for an educational project. No copyright infringement is intended.

This code is for an Item Catalog management system built on top of Flask framework using Python language.
The code conforms to PEP8 standards for Python.
The project uses wtf forms for csrf protection and also provides an option to sign in using Google+
The provided sqlite DB is for test purposes only.


## Quick start

To run the project, Python needs to be installed on the system ::

- [Download the latest release](https://github.com/ongakugene/item-catalog/archive/master.zip)
    or
- Clone the repo: `git clone https://github.com/ongakugene/item-catalog.git`.
- Install the following library dependencies if you do not have them already:   
`pip install flask-sqlalchemy`

`pip install flask-bootstrap`

`pip install flask-wtf`

`pip install oauth2client`

`pip install requests`

- On the shell, navigate into the project directory: `cd path/to/item-catalog`
- If you do not want to use the test database and start with a clear db, please delete the file data.sqlite3 in the project directory.
- The project can be run using the command: `python Item_Catalog.py`
- The project can be accessed at:  http://127.0.0.1:5000 or http://localhost:5000 using any web browser.