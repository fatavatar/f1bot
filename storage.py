import sqlite3
import os
import logging
from contextlib import closing
import datetime

maxpicks = 5

class User:
    def __init__(self, id, name, email, code):
        self.email = email
        self.name = name
        self.id = id
        self.code = code

class Driver:
    def __init__(self, id, name, team, usage=0):
        self.team = team
        self.name = name
        self.id = id
        self.usage = usage

class Race:
    def __init__(self, id, name, start):
        self.start = start
        self.name = name
        self.id = id

    def canPick(self):
        return self.start > datetime.datetime.now()

db_name = "data/f1.db"
def setup():    
    if os.path.isfile(db_name):
        return

    with closing(sqlite3.connect(db_name)) as con, con,  \
            closing(con.cursor()) as cur:

        cur.execute("""CREATE TABLE user(
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                email TEXT NOT NULL, 
                name TEXT NOT NULL,
                code TEXT NOT NULL
            );""")
        
        cur.execute("""CREATE TABLE driver (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                name INTEGER NOT NULL,
                team TEXT NOT NULL
            );""")

        cur.execute("""CREATE TABLE race (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                name INTEGER NOT NULL,
                start INTEGER NOT NULL 
            );""")
        
        cur.execute("""CREATE TABLE pick (                
                num INTEGER NOT NULL,
                user INTEGER NOT NULL,
                race INTEGER NOT NULL,
                driver INTEGER NOT NULL,
                PRIMARY KEY (num, user, race),
                FOREIGN KEY (user) REFERENCES user (id),
                FOREIGN KEY (race) REFERENCES race (id),
                FOREIGN KEY (driver) REFERENCES driver (id)
            );""")                

        cur.execute("""CREATE TABLE result (
                race INTEGER NOT NULL,
                driver INTEGER NOT NULL,
                points INTEGER NOT NULL,
                PRIMARY KEY (driver, race),
                FOREIGN KEY (race) REFERENCES race (id),
                FOREIGN KEY (driver) REFERENCES driver (id)
            );""")

        con.commit()

def addUser(name, email, code):
    try:
        with closing(sqlite3.connect(db_name)) as con, con,  \
            closing(con.cursor()) as cur:
            cur.execute("INSERT INTO user (name, email, code) VALUES (?,?,?) ", (name, email, code))
            con.commit()
        return True
    except Exception as e:
        logger.debug("Error adding user: ", str(e))
        return False

def addDriver(name, team):
    try:
        with closing(sqlite3.connect(db_name)) as con, con,  \
            closing(con.cursor()) as cur:
            cur.execute("INSERT INTO driver (name, team) VALUES (?,?) ", (name, team))
            con.commit()
        return True
    except Exception as e:
        logger.debug("Error adding driver: ", str(e))
        return False
    

def addRace(name, date):
    timestamp = date.timestamp()
    try:
        with closing(sqlite3.connect(db_name)) as con, con,  \
            closing(con.cursor()) as cur:
            cur.execute("INSERT INTO race (name, start) VALUES (?,?) ", (name, timestamp))
            con.commit()
        return True
    except Exception as e:
        logger.debug("Error adding race: ", str(e))
        return False
    
def getRaces():
    try:
        with closing(sqlite3.connect(db_name)) as con, con,  \
            closing(con.cursor()) as cur:
            cur.execute("SELECT id, name, start FROM race ORDER BY start ASC")
            races = []
            for row in cur:
                date = datetime.datetime.fromtimestamp(row[2])
                race = Race(row[0], row[1], date)
                races.append(race)
            return races
    except Exception as e:
        return None
    
def getRace(id):
    try:
        with closing(sqlite3.connect(db_name)) as con, con,  \
            closing(con.cursor()) as cur:
            cur.execute("SELECT name, start FROM race WHERE id = ?", (id,))
            name, start = cur.fetchone()
            date = datetime.datetime.fromtimestamp(start)

            return Race(id, name, date)
    except Exception as e:
        return None
    
def getDriversForUser(id):
    try:
        with closing(sqlite3.connect(db_name)) as con, con,  \
            closing(con.cursor()) as cur:
            cur.execute("SELECT id, name, team FROM driver ORDER BY id ASC")
            drivers = []
            for row in cur:
                driver = Driver(row[0], row[1], row[2])
                drivers.append(driver)
            counts={}
            cur.execute("SELECT driver, COUNT(driver) FROM pick WHERE user = ? GROUP BY driver", (id,))
            for row in cur:
                counts[row[0]] = row[1]
            
            for driver in drivers:
                if driver.id in counts:
                    driver.usage = counts[driver.id]
                else:
                    driver.usage = 0
    
        return drivers
    except Exception as e:
        print(str(e))
        return None
    
def getAllPicksForRace(raceid): 
    try:
        with closing(sqlite3.connect(db_name)) as con, con,  \
            closing(con.cursor()) as cur:            
            cur.execute("SELECT num, user.name, driver.name FROM pick INNER JOIN driver on driver.id = pick.driver INNER JOIN user ON user.id = pick.user WHERE race = ?", (raceid, ))
            picks = {}
            for row in cur:
                if row[1] not in picks:
                    picks[row[1]] = {}
                picks[row[1]][row[0]] = row[2]

            return picks
                    
    except Exception as e:
        print(str(e))
        return None
    
def getPicksForRace(raceid, userid): 
    try:
        with closing(sqlite3.connect(db_name)) as con, con,  \
            closing(con.cursor()) as cur:            
            cur.execute("SELECT num, name FROM pick INNER JOIN driver on driver.id = pick.driver WHERE user = ? AND race = ?", (userid, raceid))
            picks = {}
            for row in cur:
                picks[row[0]] = row[1]
            return picks
                    
    except Exception as e:
        print(str(e))
        return None

def clearPicks(raceid, userid):
    try:
        with closing(sqlite3.connect(db_name)) as con, con,  \
            closing(con.cursor()) as cur:            
            cur.execute("DELETE FROM pick WHERE race = ? AND user = ?", (raceid, userid))            
            con.commit()
        return True
    except Exception as e:
        print(str(e))
        return False
    

def validatePicks(userid, raceid, pick1, pick2, pick3):
    try:
        with closing(sqlite3.connect(db_name)) as con, con,  \
            closing(con.cursor()) as cur:            
            cur.execute("SELECT COUNT(driver) as drivercount FROM pick WHERE user = ? AND race != ? AND driver in (?,?,?) GROUP BY driver ORDER BY drivercount DESC LIMIT 1", (userid, raceid, pick1, pick2, pick3))
            
            maxcount = cur.fetchone()
            if maxcount is not None and maxcount[0] >= maxpicks:
                return False
            
        return True
    except Exception as e:
        print(str(e))
        return False

def setPicks(userid, raceid, pick1, pick2, pick3):
    try:
        with closing(sqlite3.connect(db_name)) as con, con,  \
            closing(con.cursor()) as cur:            
            cur.execute("DELETE FROM pick WHERE race = ? AND user = ?", (raceid, userid))
            cur.execute("INSERT INTO pick (num, user, race, driver) VALUES (?,?,?,?)", (1, userid, raceid, pick1))
            cur.execute("INSERT INTO pick (num, user, race, driver) VALUES (?,?,?,?)", (2, userid, raceid, pick2))
            cur.execute("INSERT INTO pick (num, user, race, driver) VALUES (?,?,?,?)", (3, userid, raceid, pick3))
            con.commit()
        return True
    except Exception as e:
        print(str(e))
        return False
    

def getUserByCode(code):
    try:
        with closing(sqlite3.connect(db_name)) as con, con,  \
            closing(con.cursor()) as cur:
            cur.execute("SELECT id, name, email FROM user WHERE code = ?", (code,))
            user_id, name, email = cur.fetchone()
            user = User(user_id, name, email, code)
            return user
    except Exception as e:
        return None

def getDrivers():
    try:
        with closing(sqlite3.connect(db_name)) as con, con,  \
            closing(con.cursor()) as cur:
            cur.execute("SELECT id, name, team FROM driver ORDER BY id ASC")
            drivers = []
            for row in cur:
                driver = Driver(row[0], row[1], row[2])
                drivers.append(driver)
            return drivers
    except Exception as e:
        return None
    

setup()
logger = logging.getLogger("F1")