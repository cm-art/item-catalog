from functools import wraps
from flask import Flask, render_template, request, redirect, jsonify, url_for, flash  # noqa
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Drive
from flask import session as login_session
import datetime
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)


# Application called Wipes, allows users to connect to the DrivewipeDB
# and make CRUD changes and also look at the data currently in the DB. 

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Drive Wipe Database Application"

# Connect to Database
engine = create_engine('sqlite:///drivewipe.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Login required
def login_required(f):
    @wraps(f)
    def login_function(*args, **kwargs):
        if 'user_id' not in login_session:
            return redirect(url_for('showLogin'))
        return f(*args, **kwargs)
    return login_function


# JSON APIs to show Drivewipe Information
@app.route('/api/v1/drivewipe.json')
def showDriveJSON():
    """Returns JSON of all HDD's in Drivewipe DB, order by date of wipe_end"""
    items = session.query(Drive).order_by(Drive.wipe_end.desc())
    return jsonify(Drive=[i.serialize for i in items])

@app.route('/api/v1/drives/<int:u_id>/JSON')
def wipeByUser(u_id):
    """Returns JSON of All drives wiped by user"""
    userWipe = session.query(Drive).filter_by(user_id = u_id)
    return jsonify(Drive=[i.serialize for i in userWipe])

@app.route('/api/v1/drives/<serialno>/JSON')
def driveSerialno(serialno):
    """Returns JSON of All drives that matches serialno"""
    serialNo = session.query(Drive).filter_by(serialno = serialno)
    return jsonify(Drive=[i.serialize for i in serialNo])

# CRUD for Drives
# READ, shows home and also Drives Wiped 
@app.route('/')
@app.route('/drives/')
def showDrives():
    """ Shows all HDD's that have been wiped """ 
    drives = session.query(Drive).all()
    items = session.query(Drive).order_by(Drive.wipe_end.desc())
    count = items.count()
    # We're going to return two pages, public_drives is for unauthorized
    if 'username' not in login_session:
        return render_template('public_drives.html',
            drives=drives, items=items, count=count)
    else:
        return render_template('drivewipe.html',
            drives=drives, items=items, count=count)


# CREATE, Add in another drive that has been wiped
@app.route('/drives/new', methods=['GET', 'POST'])
@login_required
def newDrive():
    """ Allows user to add in new drives to the database """
    if request.method == 'POST':
        print(login_session)
        if 'user_id' not in login_session and 'email' in login_session:
            login_session['user_id'] = getUserID(login_session['email'])
        newDrive = Drive(
            serialno=request.form['serialno'],
            manf=request.form['manf'],
            model=request.form['model'],
            wipe_status=request.form['wipe_status'],
            wipe_start=request.form['wipe_start'],
            wipe_end=request.form['wipe_end'],
            user_id=login_session['user_id'])
        session.add(newDrive)
        session.commit()
        flash("New Drive added!", 'success')
        return redirect(url_for('showDrives'))
    else:
        return render_template('new_drive.html')


# EDIT a Drive
@app.route('/drives/<int:serialno>/edit/', methods=['GET', 'POST'])
@login_required
def editDrive(serialno):
    """Allows user to edit an existing drive status"""
    editedDrive = session.query(
        Drive).filter_by(id=serialno).one()
    if editedDrive.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized!')}</script><body onload='myFunction()'>"  # noqa
    if request.method == 'POST':
        if request.form['serialno']:
            editedDrive.serialno = request.form['serialno']
            flash(
                'Drive Successfully Edited %s' % editedDrive.serialno,
                'success')
            return redirect(url_for('showDrives'))
    else:
        return render_template(
            'edit_drives.html', drive=editedDrive)

# DELETE a category
@app.route('/drives/<int:serialno>/delete/', methods=['GET', 'POST'])
@login_required
def deleteDrive(serialno):
    """Allows user to delete an existing Drive"""
    driveToDelete = session.query(
        Drive).filter_by(id=serialno).one()
    if driveToDelete.user_id != login_session['user_id']:
        return "<script>function myFunction() {alert('You are not authorized!')}</script><body onload='myFunction()'>"  # noqa
    if request.method == 'POST':
        session.delete(driveToDelete)
        flash('%s Successfully Deleted' % driveToDelete.serialno, 'success')
        session.commit()
        return redirect(
            url_for('showDrive', serialno=serialno))
    else:
        return render_template(
            'delete_drive.html', drive=driveToDelete)


# Login Handling
# Start by creating anti-forgery token. 
@app.route('/login')
def showLogin():
    state = ''.join(
        random.choice(
            string.ascii_uppercase + string.digits) for x in range(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

# Google auth call for token. 
@app.route('/gconnect', methods=['POST'])
def gconnect():
    # check state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    code = request.data

    # OAuth flow
    try:
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    
    # Verify token is valid. 
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify the user's token matches them
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify the token is valid for this app
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response
    
    # Check if the user is already logged in and store token
    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(
            json.dumps('Current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    
    login_session['access_token'] = credentials.to_json()
    login_session['gplus_id'] = gplus_id

    # Collect user data
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['provider'] = 'google'
    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    # Check if user exists if not create them. 
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Hello , '
    output += login_session['username']
    output += '!, welcome to the drivewipe db!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '  # noqa
    flash("you are now logged in as %s" % login_session['username'], 'success')
    print("done!")
    return output

# Google Logout 
@app.route('/glogout')
def glogout():
    # check connection stauts before logging out 
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-type'] = 'application/json'
        return response
    # HTTP request to revoke access token
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token 
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # delete the user's data
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    else:
        # error if token fails to be revoked!
        response = make_response(
            json.dumps('Failed to revoke token for given user.'), 400)
        response.headers['Content-Type'] = 'application/json'
        return response

# User helper functions
def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def createUser(login_session):
    newUser = User(
        name=login_session['username'],
        email=login_session['email'],
        picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)