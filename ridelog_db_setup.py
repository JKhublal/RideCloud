# Configuration - import necessary libraries, modules
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, Date, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
Base = declarative_base()

# Mapper
# Create a table for usernames and passwords
class User(Base):
	__tablename__ = 'user'
	name = Column(String(20), nullable = False)
	pword = Column(String(10), nullable = False)
	id = Column(Integer, primary_key = True)

# Create a table where user's overall stats will be stored
class Overall(Base):
	__tablename__ = 'overall'
	id = Column(Integer, ForeignKey('user.id'), primary_key = True)
	user = relationship(User)
	totalRides = Column(Integer, nullable = False, default = 0)
	totalMiles = Column(Float, nullable = False, default = 0)
	totalElevation = Column(Float, nullable = False, default = 0)
	avgSpeed = Column(Float, nullable = False, default = 0)
	avgHR = Column(Integer, nullable = False, default = 0)
	maxSpeed = Column(Float, nullable = False, default = 0)
	maxHR = Column(Integer, nullable = False, default = 0)
	maxDistance = Column(Float, nullable = False, default = 0)
	maxElevation = Column(Float, nullable = False, default = 0)

class Ride(Base):
	__tablename__ = 'ride'
	date = Column(Date, nullable = False)
	description = Column(String(80), nullable = False)
	id = Column(Integer, primary_key = True)
	hours = Column(Integer, nullable = False)
	minutes = Column(Integer, nullable = False)
	seconds = Column(Integer, nullable = False)
	distance = Column(Float, nullable = False)
	elevation = Column(Float, nullable = False, default = 0)
	avgSpeed = Column(Float, nullable = False)
	maxSpeed = Column(Float, nullable = False, default = 0)
	avgHR = Column(Integer, nullable = False, default = 0)
	maxHR = Column(Integer, nullable = False, default = 0)
	weather = Column(String(80), nullable = False)
	comments = Column(String(200), nullable = False)
	userID = Column(Integer, ForeignKey('user.id'))
	user = relationship(User)

	# Define a function to serialize the API endpoint
	@property
	def serialize(self):
		return {
			'date' : str(self.date),
			'description' : self.description,
			'id' : self.id,
			'hours' : self.hours,
			'minutes' : self.minutes,
			'seconds' : self.seconds,
			'distance' : self.distance,
			'elevation' : self.elevation,
			'avgSpeed' : self.avgSpeed,
			'maxSpeed' : self.maxSpeed,
			'avgHR' : self.avgHR,
			'maxHR' : self.maxHR,
			'comments': self.comments,
		}

# Code to create the database file
engine = create_engine('sqlite:///ridelog_db.db')
Base.metadata.create_all(engine)