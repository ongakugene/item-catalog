import random
import string
import json
import os
from datetime import datetime

import dicttoxml

import httplib2
import requests
from flask import session as login_session
from flask import Flask, render_template, request
from flask import jsonify, flash, redirect, url_for
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.bootstrap import Bootstrap
from flask.ext.wtf import Form
from flask import make_response
from flask import Response
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import Length, DataRequired
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError


# Initializing the app and setting config data
app = Flask(__name__)
app.config['SECRET_KEY'] = 'S@n@@hamD0s1n11B@sKhUd@k@ShUkRHa!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.sqlite3'


# OAuth2 Sign In Related
# The call below is to make it work on IDEs
os.chdir(os.path.dirname(os.path.realpath(__file__)))
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Item Calalog"


# Initialising Bootstrap and ORM
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)


# Model definitions
class Category(db.Model):
    """
    Category class representing blueprint for categories
    """
    __tablename__ = 'tbl_categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(25), index=True, unique=True)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return '<Category {0}>'.format(self.name)


class Item(db.Model):
    """
    Item class representing blueprint for items
    """
    __tablename__ = 'tbl_items'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(30), index=True)
    description = db.Column(db.Text)
    category_id = db.Column(db.Integer, db.ForeignKey('tbl_categories.id'))
    date_created = db.Column(db.DateTime)

    def __init__(self, title, description, category_id, date_created=None):
        self.title = title
        self.description = description
        self.category_id = category_id
        if date_created is None:
            date_created = datetime.utcnow()
        self.date_created = date_created

    def __repr__(self):
        return '<Item {0}>'.format(self.title)


# Form definitions
class CategoryForm(Form):
    """
    Form for new category creation
    """
    name = StringField('Enter new item name', validators=[DataRequired(),
                                                          Length(1, 30)])
    submit = SubmitField('Create')


class ItemForm(Form):
    """
    Form for new item creation
    """
    categories = []

    def __init__(self, categories):
        Form.__init__(self)
        for category in categories:
            if not (((category.id, category.name)) in self.categories):
                self.categories.append((category.id, category.name))

    title = StringField('Enter new item name', validators=[DataRequired(),
                                                           Length(1, 30)])
    description = TextAreaField('Enter item description',
                                validators=[DataRequired(),
                                            Length(1, 300)])
    category = SelectField('Select Category', choices=categories, coerce=int)
    submit = SubmitField('Create')


class ItemDeleteForm(Form):
    """
    Form for item deletion
    """
    submit = SubmitField('Yes')


# Route definitions
@app.route('/')
def index():
    """
    The base index route.
    Shows Categories, Latest items and Login button
    Logged-in users see link to add items and categories
    """
    categories = db.session.query(Category).all()
    latest_items = db.session.query(Item).\
        order_by(Item.date_created.desc()).limit(10).all()
    category_names = {}
    for category in categories:
        category_names[category.id] = category.name
    return render_template('index.html', categories=categories,
                           latest_items=latest_items,
                           category_names=category_names,
                           login_session=login_session)


@app.route('/category/create', methods=['GET', 'POST'])
def create_category():
    """
    This route is for creating categories.
    Can be accessed by logged-in users only.
    """
    if 'username' not in login_session:
        return redirect(url_for('show_login'))
    duplicate = None
    created = None
    form = CategoryForm()
    if form.validate_on_submit():
        name = form.name.data
        form.name.data = ''
        if Category.query.filter_by(name=name).first() is None:
            db.session.add(Category(name=name))
            db.session.commit()
            created = True
        else:
            duplicate = True
    return render_template('create-category.html',
                           form=form, created=created,
                           duplicate=duplicate)


@app.route('/items/<category_id>')
def list_items(category_id):
    """
    This route is for listing all items in a category.
    Category ID is required in the URL.
    """
    items = db.session.query(Item).filter_by(category_id=category_id).all()
    category = db.session.query(Category).filter_by(id=category_id).first()
    category_name = category.name
    return render_template('list-items.html',
                           category_name=category_name,
                           items=items,
                           login_session=login_session)


@app.route('/item/<item_id>')
def show_item(item_id):
    """
    This route is for listing details for an item.
    Item ID is required in the URL.
    """
    item = db.session.query(Item).filter_by(id=item_id).first()
    category = db.session.query(Category).\
        filter_by(id=item.category_id).first()
    category_name = category.name
    return render_template('show-item.html',
                           item=item, category_name=category_name,
                           login_session=login_session)


@app.route('/item/create', methods=['GET', 'POST'])
def create_item():
    """
    This route is for creating items.
    Can be accessed by logged-in users only.
    """
    if 'username' not in login_session:
        return redirect(url_for('show_login'))
    duplicate = None
    created = None
    categories = db.session.query(Category).all()
    form = ItemForm(categories)
    if form.validate_on_submit():
        title = form.title.data
        description = form.description.data
        category_id = form.category.data
        form.title.data = ''
        form.description.data = ''
        form.category.data = ''
        if Item.query.filter_by(title=title).first() is None:
            db.session.add(Item(title=title,
                                description=description,
                                category_id=category_id))
            db.session.commit()
            created = True
        else:
            duplicate = True
    return render_template('create-item.html',
                           form=form, created=created,
                           duplicate=duplicate)


@app.route('/item/edit/<item_id>', methods=['GET', 'POST'])
def edit_item(item_id):
    """
    This route is for editing items.
    Can be accessed by logged-in users only.
    """
    if 'username' not in login_session:
        return redirect(url_for('show_login'))
    edited = None
    categories = db.session.query(Category).all()
    target_item = db.session.query(Item).filter_by(id=item_id).first()
    form = ItemForm(categories)
    form.title.data = target_item.title
    form.description.data = target_item.description
    form.category.data = target_item.category_id
    form.submit.label.text = "Update"
    if form.validate_on_submit():
        target_item = db.session.query(Item).filter_by(id=item_id).first()
        target_item.title = request.form.get('title')
        target_item.description = request.form.get('description')
        target_item.category_id = request.form.get('category')
        form.title.data = target_item.title
        form.description.data = target_item.description
        form.category.data = target_item.category_id
        db.session.commit()
        edited = True
    return render_template('edit-item.html',
                           form=form, edited=edited,
                           login_session=login_session)


@app.route('/item/delete/<item_id>', methods=['GET', 'POST'])
def delete_item(item_id):
    """
    This route is for deleting items.
    Can be accessed by logged-in users only.
    """
    if 'username' not in login_session:
        return redirect(url_for('show_login'))
    deleted = None
    form = ItemDeleteForm()
    target_item = db.session.query(Item).filter_by(id=item_id).first()
    if form.validate_on_submit():
        target_item = db.session.query(Item).filter_by(id=item_id).first()
        db.session.delete(target_item)
        db.session.commit()
        deleted = True
    return render_template('delete-item.html',
                           form=form, item=target_item,
                           deleted=deleted,
                           login_session=login_session)


@app.route('/login')
def show_login():
    """
    This route is for showing the Google login interface.
    """
    state = ''.join(random.
                    choice(string.
                           ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', state=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['credentials'] = credentials.to_json()
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;' \
              'border-radius: 150px;' \
              '-webkit-border-radius: 150px;' \
              '-moz-border-radius: 150px;"> '
    flash("You are now logged in as %s" % login_session['username'])
    print "done!"
    return output


@app.route('/logout')
def gdisconnect():
    """
    This route is for logging-out a logged-in user.
    """
    # Only disconnect a connected user.
    access_token = login_session['access_token']
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['access_token']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected. '
                                            'Please visit again.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


@app.route('/catalog.json')
def get_json():
    """
    This route provides a JSON endpoint for data.
    """
    catalog = {}
    categories = db.session.query(Category).all()
    for category in categories:
        catalog[category.id] = {}
        catalog[category.id]['category-id'] = category.id
        catalog[category.id]['category-name'] = category.name
        catalog[category.id]['items'] = {}
        items = db.session.query(Item).filter_by(category_id=category.id)
        for item in items:
            catalog[category.id]['items'][item.id] = {}
            catalog[category.id]['items'][item.id]['item-id'] = item.id
            catalog[category.id]['items'][item.id]['title'] = item.title
            catalog[category.id]['items'][item.id]['description'] = \
                item.description
    return jsonify(catalog)


@app.route('/catalog.xml')
def get_xml():
    """
    This route provides an XML endpoint for data.
    """
    catalog = {}
    categories = db.session.query(Category).all()
    for category in categories:
        catalog[str(category.id)] = {}
        catalog[str(category.id)]['category-id'] = category.id
        catalog[str(category.id)]['category-name'] = category.name
        catalog[str(category.id)]['items'] = {}
        items = db.session.query(Item).filter_by(category_id=category.id)
        for item in items:
            catalog[str(category.id)]['items'][str(item.id)] = {}
            catalog[str(category.id)]['items'][str(item.id)]['item-id'] = \
                item.id
            catalog[str(category.id)]['items'][str(item.id)]['title'] = \
                item.title
            catalog[str(category.id)]['items'][str(item.id)]['description'] = \
                item.description
    xml = dicttoxml.dicttoxml(catalog)
    return Response(xml, mimetype='text/xml')


# Starting the app after creating the database
if __name__ == '__main__':
    db.create_all()  # For creating the initial DB
    app.run(debug=False)
