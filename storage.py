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
        
        # cur.execute("""CREATE TABLE driver (
        #         id INTEGER PRIMARY KEY AUTOINCREMENT, 
        #         name INTEGER NOT NULL,
        #         team TEXT NOT NULL,
        #         firstname TEXT,
        #         lastname TEXT,
        #         number INTEGER,
        #         code TEXT
        #     );""")

        # cur.execute("""CREATE TABLE race (
        #         id INTEGER PRIMARY KEY AUTOINCREMENT, 
        #         name INTEGER NOT NULL,
        #         start INTEGER NOT NULL,
        #         round INTEGER 
        #     );""")
        
        cur.execute("""CREATE TABLE pick (                
                num INTEGER NOT NULL,
                user INTEGER NOT NULL,
                race INTEGER NOT NULL,
                driver INTEGER NOT NULL,
                PRIMARY KEY (num, user, race)
            );""")                

        # cur.execute("""CREATE TABLE result (
        #         race INTEGER NOT NULL,
        #         driver INTEGER NOT NULL,
        #         points INTEGER NOT NULL,
        #         PRIMARY KEY (driver, race),
        #         FOREIGN KEY (race) REFERENCES race (id),
        #         FOREIGN KEY (driver) REFERENCES driver (id)
        #     );""")

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
    
def getDriversForUser(id : int) -> dict[int, int]:
    try:
        with closing(sqlite3.connect(db_name)) as con, con,  \
            closing(con.cursor()) as cur:

            counts={}
            cur.execute("SELECT driver, COUNT(driver) FROM pick WHERE user = ? GROUP BY driver", (id,))
            for row in cur:
                counts[row[0]] = row[1]
            return counts
        
    except Exception as e:
        print(str(e))
        return None
    
def getAllPicksForRace(raceid) -> dict[int, list[int]]: 
    picks = {}
    try:
        with closing(sqlite3.connect(db_name)) as con, con,  \
            closing(con.cursor()) as cur:            
            cur.execute("SELECT user, driver FROM pick WHERE race = ?", (raceid, ))
            for row in cur:
                if row[1] not in picks:
                    picks[row[1]] = []
                picks[row[1]].append(row[0])

            return picks
                    
    except Exception as e:
        print(str(e))
        return picks
    
def getUsers() -> dict[int, User]:
    users = {}
    try:
        with closing(sqlite3.connect(db_name)) as con, con,  \
            closing(con.cursor()) as cur:
            cur.execute("SELECT id, name, email, code FROM user")
            for row in cur:
                
                user = User(row[0], row[1], row[2], row[3])
                users[user.id] = user
            
        return users
    except Exception as e:
        return users
   
def getPicksForRace(raceid, userid) -> list[int]: 
    picks = []
    try:
        with closing(sqlite3.connect(db_name)) as con, con,  \
            closing(con.cursor()) as cur:            
            cur.execute("SELECT num, driver FROM pick WHERE user = ? AND race = ?", (userid, raceid))        
            for row in cur:
                picks.append(row[1])
            return picks
                    
    except Exception as e:
        print(str(e))
        return picks

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
    

def validatePicks2(userid, raceid, picks):
    try:
        with closing(sqlite3.connect(db_name)) as con, con,  \
            closing(con.cursor()) as cur:            
            for pick in picks:
                cur.execute("SELECT COUNT(driver) as drivercount FROM pick WHERE user = ? AND race != ? AND driver = ? GROUP BY driver", (userid, raceid, pick))
            
                maxcount = cur.fetchone()
                if maxcount is not None and maxcount[0] >= maxpicks:
                    return False
            
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
    
def setPicks2(userid, raceid, picks):
    try:
        with closing(sqlite3.connect(db_name)) as con, con,  \
            closing(con.cursor()) as cur:            
            cur.execute("DELETE FROM pick WHERE race = ? AND user = ?", (raceid, userid))
            
            for i in range(len(picks)):
                if picks[i] is not None:
                    logger.info("Inserting pick " + str(i+1) + " of value: " + picks[i])
                    cur.execute("INSERT INTO pick (num, user, race, driver) VALUES (?,?,?,?)", (i+1, userid, raceid, picks[i]))            
            con.commit()
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
    
def getPicks():
    try:
        with closing(sqlite3.connect(db_name)) as con, con,  \
            closing(con.cursor()) as cur:            
            cur.execute("SELECT race, user, driver FROM pick ORDER BY race ASC")
            retval = {}
            for row in cur:
                if row[0] not in retval:
                    retval[row[0]]  = {}
                retval[row[0]][row[1]] = row[2]
            return retval
                        
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

    
setup()
logger = logging.getLogger("F1")