#!/usr/bin/env python


from flask import Flask, render_template, request, redirect
from flask import jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User
from flask import session as login_sess
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
import datetime

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Sporting Goods Catalog"

# Connect to Database and create database session
engine = create_engine('sqlite:///sports-catalog.db',
                       connect_args={'check_same_thread': False})
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create anti-forgery state token


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_sess['state'] = state
    # return "The current session state is %s" % login_sess['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_sess['state']:
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
        return response

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

    stored_access_token = login_sess.get('access_token')
    stored_gplus_id = login_sess.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('User is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_sess['access_token'] = credentials.access_token
    login_sess['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_sess['username'] = data['name']
    login_sess['picture'] = data['picture']
    login_sess['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_sess['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_sess)
    login_sess['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_sess['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_sess['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: \
      150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_sess['username'])
    print "done!"
    return output

# User Helper Functions


def createUser(login_sess):
    newUser = User(name=login_sess['username'], email=login_sess[
                   'email'], picture=login_sess['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_sess['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except Exception:
        return None

# DISCONNECT - Revoke a current user's token and reset their login_sess


@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_sess.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke user token.'),
                                 400)
        response.headers['Content-Type'] = 'application/json'
        return response

# Show all category and latest items


@app.route('/')
@app.route('/category/')
def showCategory():

    categories = session.query(Category).order_by(asc(Category.name))
    items = session.query(Item).join(Category) \
        .order_by(Item.create_dttm.desc()).limit(3).all()
    itemcnt = "(" + str(session.query(Item).limit(3).count()) + ")"
    splash_scrn = '1'
    print splash_scrn
    if 'username' not in login_sess:
        return render_template('categorypublic.html', categories=categories,
                               items=items, itemcnt=itemcnt,
                               splash_scrn=splash_scrn)
    else:
        return render_template('category.html', categories=categories,
                               items=items, itemcnt=itemcnt,
                               splash_scrn=splash_scrn)

# Show all category and its items


@app.route('/category/<int:category_id>/')
def showCategoryItem(category_id):
    categories = session.query(Category).order_by(asc(Category.name))
    items = session.query(Item).order_by(asc(Item.name)) \
        .filter_by(category_id=category_id).all()
    for item in items:
        cat_name = item.category.name
    itemcnt = "(" + str(session.query(Item)
                        .filter_by(category_id=category_id).count()) + ")"
    splash_scrn = '0'
    if 'username' not in login_sess:
        return render_template('categorypublic.html', categories=categories,
                               items=items, itemcnt=itemcnt, cat_name=cat_name)
    else:
        return render_template('category.html', categories=categories,
                               items=items, itemcnt=itemcnt, cat_name=cat_name)


# Show an item


@app.route('/item/<int:item_id>/')
def showItem(item_id):
    items = session.query(Item).filter_by(id=item_id).one()
    creator = getUserInfo(items.user_id)
    if 'username' not in login_sess or creator.id != login_sess['user_id']:
        return render_template('itempublic.html', items=items,
                               creator=creator)
    else:
        return render_template('item.html', items=items, creator=creator)

# Create a new item


@app.route('/item/new/', methods=['GET', 'POST'])
def newItem():

    if 'username' not in login_sess:
        return redirect('/login')
    option_list = session.query(Category).order_by(asc(Category.name))
    now = datetime.datetime.now()
    if request.method == 'POST':
        newItem = Item(
            name=request.form['name'],
            description=request.form['description'],
            category_id=request.form['category_id'],
            create_dttm=now.strftime("%Y-%m-%d %H:%M:%S.000"),
            user_id=login_sess['user_id'])
        session.add(newItem)
        category_id = request.form['category_id']
        flash('New Item %s Successfully Created' % newItem.name)
        session.commit()
        return redirect(url_for('showCategoryItem', category_id=category_id))
    else:
        return render_template('itemnew.html', option_list=option_list)

# Edit an item


@app.route('/item/edit/<int:item_id>/', methods=['GET', 'POST'])
def editItem(item_id):
    if 'username' not in login_sess:
        return redirect('/login')
    option_list = session.query(Category).order_by(asc(Category.name))
    editedItem = session.query(Item).filter_by(id=item_id).one()
    now = datetime.datetime.now()
    creator = getUserInfo(editedItem.user_id)

    if request.method == 'POST':
        if request.form['name']:
            editedItem.name = request.form['name']
        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['category_id']:
            editedItem.category_id = request.form['category_id']
        editedItem.create_dttm = now.strftime("%Y-%m-%d %H:%M:%S.000")
        session.add(editedItem)
        flash('Item %s Successfully Edited' % editedItem.name)
        session.commit()
        return redirect(url_for('showItem', item_id=item_id))
    else:
        return render_template('itemedit.html', option_list=option_list,
                               item=editedItem, creator=creator)

# Delete an item


@app.route('/item/delete/<int:item_id>', methods=['GET', 'POST'])
def deleteItem(item_id):
    if 'username' not in login_sess:
        return redirect('/login')
    itemToDelete = session.query(Item).filter_by(id=item_id).one()

    if request.method == 'POST':
        session.delete(itemToDelete)
        session.commit()
        flash('Item Successfully Deleted')
        return redirect(url_for('showCategory'))
    else:
        return render_template('itemdelete.html', item=itemToDelete)

# JSON APIs to view Product Information


@app.route('/item/JSON/')
def itemsJSON():
    items = session.query(Item).all()
    return jsonify(items=[r.serialize for r in items])


@app.route('/item/JSON/<int:item_id>/')
def ItemJSON(item_id):
    items = session.query(Item).filter_by(id=item_id).one()
    return jsonify(items=items.serialize)

# Disconnect


@app.route('/disconnect')
def disconnect():
    if 'provider' in login_sess:
        if login_sess['provider'] == 'google':
            gdisconnect()
            del login_sess['gplus_id']
            del login_sess['access_token']
        del login_sess['username']
        del login_sess['email']
        del login_sess['picture']
        del login_sess['user_id']
        del login_sess['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showCategory'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showCategory'))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8080)
