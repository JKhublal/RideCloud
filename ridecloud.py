# Import flask and necessary methods, classes
from flask import Flask, render_template, url_for, request, redirect, flash, jsonify
from flask.ext.basicauth import BasicAuth
from datetime import datetime, date
# Import bleach to sanitize database inputs
import bleach
bc = bleach.clean
# Create an instance of Flask class with the name of the running program as an argument
app = Flask(__name__)
# Create an instance of BasicAuth for the app
basic_auth = BasicAuth(app)
app.config['BASIC_AUTH_USERNAME'] = ''
app.config['BASIC_AUTH_PASSWORD'] = ''
app.config['BASIC_AUTH_ID'] = ''
# Define a function to check authentification
def check_auth(user_id):
	requestedUserData = session.query(User).filter_by(id = user_id).one()
	if user_id == app.config['BASIC_AUTH_ID'] and app.config['BASIC_AUTH_USERNAME'] == requestedUserData.name and app.config['BASIC_AUTH_PASSWORD'] == requestedUserData.pword:
		return True
 
# Import SQL Alchemy modules to interact with the database
from sqlalchemy import create_engine, func, desc
from sqlalchemy.orm import sessionmaker
from ridelog_db_setup import Base, User, Ride, Overall
# Prepare the session 
engine = create_engine('sqlite:///ridelog_db.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
session = DBSession()
# Define global variable to query all users
allUsers = session.query(User)

# API Endpoint (for GET requests) that returns data for all of a user's rides
@app.route('/rides/<int:user_id>/api/')
def userAllRidesAPI(user_id):
	if check_auth(user_id) == True:
		# Query the user's info and data for all of their rides
		userData = session.query(User).filter_by(id = user_id).one()
		userRides = session.query(Ride).filter_by(userID = user_id).order_by(Ride.date.desc())
		# Return the requested data in JSON
		return jsonify(Rides=[i.serialize for i in userRides])
	else:
		return redirect(url_for('userLogin'))

# API Endpoint for a single ride
@app.route('/rides/<int:user_id>/<int:ride_id>/api/')
def userSingleRideAPI(user_id, ride_id):
	if check_auth(user_id) == True:
		# Query the user's info and data for a specified ride
		userData = session.query(User).filter_by(id = user_id).one()
		# In order to NOT return another user's ride, filter by both user ID and ride ID
		userRide = session.query(Ride).filter_by(userID = user_id, id = ride_id).one()
		# Return the requested data in JSON
		return jsonify(Ride=[userRide.serialize])
	else: 
		return redirect(url_for('userLogin'))

# Main Page
@app.route('/')
@app.route('/index/')
def mainPage():
	return render_template('index.html')

# About RideCloud
@app.route('/about/')
def about():
	return render_template('about.html')

# About RideCloud page for logged-in users
@app.route('/<int:user_id>/about/')
def aboutLog(user_id):
	return render_template('about.html', user_id = user_id)

# Create New User
@app.route('/newuser/', methods = ['GET', 'POST'])
def newUser():
	if request.method == 'POST':
		# Check to see if the user name is already taken
		for i in allUsers:
			# DEBUGGING print "New user name: %s check: %s" % (request.form['name'], i.name)
			if i.name == request.form['name']:
				flash("User name '%s' is taken. Please choose another user name." % request.form['name'])
				return render_template('newUser.html')
		# Verify that the user entered the same password in both fields
		if request.form['password'] != request.form['passconf']:
			flash("The passwords you entered did not match. Please try again.")
			return render_template('newUser.html')
		# If everything checks out, add the user name and password to the database
		else:
			newUser = User(name = bleach.clean(request.form['name']), pword = bleach.clean(request.form['password']))
			session.add(newUser)
			session.commit()
			flash("Welcome to RideCloud, %s!" % newUser.name)
			app.config['BASIC_AUTH_USERNAME'] = newUser.name
			app.config['BASIC_AUTH_PASSWORD'] = newUser.pword
			app.config['BASIC_AUTH_ID'] =  newUser.id
			return redirect(url_for('dashboard', user_id = newUser.id))
	else:
		return render_template('newuser.html')

# Existing User Login
@app.route('/login/', methods = ['GET', 'POST'])
def userLogin():
	if request.method == 'POST':
		uName = bc(request.form['name'])
		uPass = bc(request.form['password'])
		# Check to see if the username exists.
		for i in allUsers:
			if i.name == uName:
				loginUser = session.query(User).filter_by(name = uName).one()
				# If the username exists, check to see if the password is correct
				if uPass == loginUser.pword:
					flash("Welcome to RideCloud, %s!" % loginUser.name)
					app.config['BASIC_AUTH_USERNAME'] = loginUser.name
					app.config['BASIC_AUTH_PASSWORD'] = loginUser.pword
					app.config['BASIC_AUTH_ID'] =  loginUser.id
					return redirect(url_for('dashboard', user_id = loginUser.id))
				else: 
					flash("The password you entered is incorrect. Please try again.")
					return render_template('login.html')
		# If the username doesn't exist...
		else: 
			flash("The username you entered does not exist in the database. Please try again.")
			return render_template('login.html')
	else: 
		return render_template('login.html')
	# redirect to ride list page

# Leaderboard
@app.route('/<int:user_id>/leaderboards/')
def leaderboards(user_id):
	distLeaders = session.query(Overall).order_by(Overall.totalMiles.desc()).limit(10)
	elevLeaders = session.query(Overall).order_by(Overall.totalElevation.desc()).limit(10)
	userNames = session.query(User).all()
	return render_template('leaderboards.html', distLeaders = distLeaders, userNames = userNames, elevLeaders = elevLeaders, user_id = user_id)

# List all of a user's rides
@app.route('/rides/<int:user_id>/dashboard/', methods = ['GET', 'POST'])
def dashboard(user_id):
	userData = session.query(User).filter_by(id = user_id).one()
	userRides = session.query(Ride).filter_by(userID = user_id).order_by(Ride.date.desc())
	if check_auth(user_id) == True:
		# Calculate totals
		totalRides = session.query(Ride).filter_by(userID = user_id).count()
		if totalRides > 0:
			totalMiles = session.query(func.sum(Ride.distance).label('totalMiles')).filter_by(userID = user_id).scalar()
			totalElevation = session.query(func.sum(Ride.elevation).label('totalElevation')).filter_by(userID = user_id).scalar()
			# Calculate total time
			totalSeconds = session.query(func.sum(Ride.seconds).label('totalSeconds')).filter_by(userID = user_id).scalar()
			displaySeconds = totalSeconds % 60
			# Display the remainder of dividing total seconds by 60. Seconds over 60 will be converted to minutes.
			secondsToMinutes = (totalSeconds - displaySeconds)/60
			totalMinutes = session.query(func.sum(Ride.minutes).label('totalMinutes')).filter_by(userID = user_id).scalar()
			# Add the extra seconds to the total minutes, then run the same operations on the minutes.
			totalMinutes += secondsToMinutes
			displayMinutes = totalMinutes % 60
			minutesToHours = (totalMinutes - displayMinutes)/60
			# Format the minutes and seconds to always show 2 places
			strDisplaySeconds = str(displaySeconds).zfill(2)
			strDisplayMinutes = str(displayMinutes).zfill(2)
			totalHours = session.query(func.sum(Ride.hours).label('totalHours')).filter_by(userID = user_id).scalar()
			displayHours = totalHours + minutesToHours
			# Determine averages and maximums
			avgSpeed = round(session.query(func.sum(Ride.avgSpeed).label('avgSpeed')).filter_by(userID = user_id).scalar() / totalRides, 2)
			avgHR = session.query(func.sum(Ride.avgHR).label('avgHR')).filter_by(userID = user_id).scalar() / totalRides		
			maxSpeed = session.query(func.max(Ride.maxSpeed)).filter_by(userID = user_id).scalar()
			maxHR = session.query(func.max(Ride.maxHR)).filter_by(userID = user_id).scalar()
			maxDistance = session.query(func.max(Ride.distance)).filter_by(userID = user_id).scalar()
			maxElevation = session.query(func.max(Ride.elevation)).filter_by(userID = user_id).scalar()
			print maxSpeed, maxHR, maxDistance, maxElevation
			# If this is the user's first ride, create a row in the Overall table
			if totalRides == 1 and session.query(Overall).filter_by(id = user_id).first() == None:
				overall = Overall(id = user_id, totalRides = totalRides, totalMiles = totalMiles, totalElevation = totalElevation, \
							avgSpeed = avgSpeed, avgHR = avgHR, maxSpeed = maxSpeed, maxHR = maxHR, maxDistance = maxDistance, \
							maxElevation = maxElevation)
				session.add(overall)
				session.commit()
			# Otherwise, Update the user's Overall records 
			else:
				overall = session.query(Overall).filter_by(id = user_id).one()
				overall.totalRides = totalRides
				overall.totalMiles = totalMiles
				overall.totalElevation = totalElevation
				overall.avgSpeed = avgSpeed
				overall.avgHR = avgHR
				overall.maxSpeed = maxSpeed
				overall.maxHR = maxHR
				overall.maxDistance = maxDistance
				overall.maxElevation = maxElevation
				session.add(overall)
				session.commit()
			return render_template('dashboard.html', userData=userData, userRides=userRides, overall = overall, displayHours = displayHours, displayMinutes = strDisplayMinutes, displaySeconds = strDisplaySeconds)
		else:
			if session.query(Overall).filter_by(id = user_id).first() != None:
				deleteTotal = session.query(Overall).filter_by(id = user_id).first()
				session.delete(deleteTotal)
				session.commit()
			return render_template('dashboard.html', userData=userData, userRides=userRides, totalRides=totalRides, overall = '')
	else: 
		flash("You are not authorized to view that user's records.")
		return redirect(url_for('forbidden', user_id = app.config['BASIC_AUTH_ID']))

@app.route('/<int:user_id>/forbidden/', methods = ['GET', 'POST'])
def forbidden(user_id):
	print user_id
	return render_template('forbidden.html', user_id = user_id)

# Add a New Ride
@app.route('/rides/<int:user_id>/new/', methods = ['GET', 'POST'])
def addRide(user_id):
	if check_auth(user_id) == True:
		if request.method == 'POST':
			# Make it easier to call request.form
			rf = request.form
			# Convert the date to Python date type so that the database can accept it
			convDate = datetime.strptime(rf['date'], '%Y-%m-%d').date()
			# If the user enters '0' for average speed, calculate the average speed for them
			averageSpeed = 0
			if rf['avgSpeed'] == '0':
				averageSpeed = float(rf['distance'])/(float(rf['hours']) + float(rf['minutes'])/60 + float(rf['seconds'])/60**2)
			else:
				averageSpeed = float(rf['avgSpeed'])
			newRide = Ride(userID = user_id, date = convDate, description = bc(rf['description']), \
						hours = bc(rf['hours']), minutes = bc(rf['minutes']), seconds = bc(rf['seconds']), distance = bc(rf['distance']), \
						elevation = bc(rf['elevation']), avgSpeed = bc(round(averageSpeed, 2)), maxSpeed = bc(rf['maxSpeed']), \
						avgHR = bc(rf['avgHR']), maxHR = bc(rf['maxHR']), weather = bc(rf['weather']), comments = bc(rf['comments']))
			session.add(newRide)
			session.commit()
			return redirect(url_for('dashboard', user_id = user_id))
		else:
			curDate = date.today()
			return render_template('addride.html', curDate=curDate, user_id = user_id)
	else:
		flash("You are not authorized to edit that user's records.")
		return redirect(url_for('forbidden', user_id = app.config['BASIC_AUTH_ID']))


# Edit a Ride
@app.route('/rides/<int:user_id>/<int:ride_id>/edit/', methods = ['GET', 'POST'])
def editRide(user_id, ride_id):
	if check_auth(user_id) == True:
		if request.method == 'POST':
			rf = request.form
			convDate = datetime.strptime(rf['date'], '%Y-%m-%d').date()
			# If the user enters '0' for average speed, calculate the average speed for them
			averageSpeed = 0
			if rf['avgSpeed'] == '0':
				averageSpeed = float(rf['distance'])/(float(rf['hours']) + float(rf['minutes'])/60 + float(rf['seconds'])/60**2)
			else:
				averageSpeed = float(rf['avgSpeed'])
			# Update the database record with the edited data
			editRide = session.query(Ride).filter_by(id = ride_id).one()
			editRide.date = convDate
			editRide.description = bc(rf['description'])
			editRide.hours = bc(rf['hours'])
			editRide.minutes = bc(rf['minutes'])
			editRide.seconds = bc(rf['seconds'])
			editRide.distance = bc(rf['distance'])
			editRide.elevation = bc(rf['elevation'])
			editRide.avgSpeed = bc(round(averageSpeed, 2))
			editRide.maxSpeed = bc(rf['maxSpeed'])
			editRide.avgHR = bc(rf['avgHR'])
			editRide.maxHR = bc(rf['maxHR'])
			editRide.weather = bc(rf['weather'])
			editRide.comments = bc(rf['comments'])
			session.add(editRide)
			session.commit()
			flash("Your ride has been edited successfully!")
			return redirect(url_for('dashboard', user_id = user_id))
		else:
			# Query and store the existing data in variable 'exData'
			exData = session.query(Ride).filter_by(id = ride_id).one()
			return render_template('editride.html', exData=exData, user_id = user_id, ride_id = ride_id)
		return "Edit a ride"
	else:
		flash("You are not authorized to edit that user's records.")
		return redirect(url_for('forbidden', user_id = app.config['BASIC_AUTH_ID']))

# Delete a Ride
@app.route('/rides/<int:user_id>/<int:ride_id>/delete/', methods=['GET', 'POST'])
def deleteRide(user_id, ride_id):
	if check_auth(user_id) == True:
		if request.method == 'POST':
			if request.form['button'] == 'Delete Ride':
				delRide = session.query(Ride).filter_by(id = ride_id).one()
				session.delete(delRide)
				session.commit()
				flash("The ride has been deleted.")
				return redirect(url_for('dashboard', user_id = user_id)) 
			else:
				return redirect(url_for('dashboard', user_id = user_id))
		else:
			return render_template('deleteride.html', ride_id = ride_id, user_id = user_id)
	else:
		flash("You are not authorized to edit that user's records.")
		return redirect(url_for('forbidden', user_id = app.config['BASIC_AUTH_ID']))




# Run the script
if __name__ == '__main__':
	# Set a key for message flashing
	app.secret_key = ''# secret key goes here
	app.debug = True
	print "Dialing it up to 400 watts on port 5000..."
	app.run(host = '0.0.0.0', port = 5000)
	