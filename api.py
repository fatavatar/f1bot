import json
import datetime
from queue import Queue
from threading import Lock, Thread
import atexit
import storage
import copy
import logging
from urllib.request import urlopen

class Driver:
    def __init__(self, number, firstname : str, lastname : str, code : str, team : str):
        self.team = team
        self.firstname = firstname
        self.lastname = lastname
        self.code = code
        self.number = int(number)
        self.name = firstname + " " + lastname
        self.usage = 0
        self.pickers = []
        self.finishplace = 0
        self.picked = False
    
    def setUsage(self, picks : list[int, int]):
        self.usage = picks
    
    def setPickedByUser(self):
        self.picked = True
    
    def addPicker(self, user : int):
        self.pickers.append(user)
        
        

class Race:
    def __init__(self, id, name : str, start : datetime.datetime):
        self.start = start
        self.name = name
        self.id = int(id)
        self.results = None
        self.qualifying = None
        self.sprint = None
        self.userPicks = []
        self.allPicks = {}
        
    
    def setResults(self, results : dict[int, int]):
        self.results = results

    def setSprint(self, sprint : dict[int, int]):
        self.sprint = sprint

    def setQualifying(self, qualifying : dict[int, int]):
        self.qualifying = qualifying        

    def canPick(self):
        return self.start > datetime.datetime.now()
    
    def setUserPicks(self, picks : list[int]):
        self.userPicks = picks

    def wasPickedByUser(self, driverId) -> bool:
        return driverId in self.userPicks
    
    def getUserPickCount(self) -> int:
        return len(self.userPicks)
    
    def setAllPicks(self, allPicks : dict[int, list[int]]):
        logger.info("Setting picks")
        self.allPicks = allPicks
    
    def getAllPicksForDriver(self, driver : int) -> list[int]:
        if driver in self.allPicks:
            return self.allPicks[driver]
        retval = []
        return retval
    

class Result:
    def __init__(self, driver, position):
        self.driver = driver
        self.position = position

def getUsers() -> dict[int, storage.User]:
    return storage.getUsers()

def getJsonResp(url):
    response = urlopen(url)
    data_json = json.loads(response.read())
    return data_json


def _getDrivers() -> list[Driver]:
    try:
        driver_json = getJsonResp("https://ergast.com/api/f1/current/driverStandings.json")
        standings = driver_json['MRData']['StandingsTable']['StandingsLists'][0]['DriverStandings']
        retval = []
        for entry in standings:
            driver = entry['Driver']
            team = entry['Constructors'][0]['name']
            newdriver = Driver(driver['permanentNumber'], driver['givenName'], driver['familyName'], driver['code'], team)
            retval.append(newdriver)
        return retval
    except Exception as e:
        print(str(e))
        return None

def _getSchedule() -> list[Race]:
    try:
        data_json = getJsonResp("https://ergast.com/api/f1/current.json")
        schedule=data_json['MRData']['RaceTable']['Races']
        retval = []
        for event in schedule:
            racetime = datetime.datetime.strptime(event['date'] + " " + event['time'], "%Y-%m-%d %H:%M:%SZ")
            # Special case the las vegas race
            if event['round'] == "21":
                racetime = racetime + datetime.timedelta(days=1)
            race = Race(int(event['round']), event['raceName'], racetime)
            retval.append(race)
        return retval
    except Exception as e:
        print(str(e))
        return None
    
        
def _getSprint(race : int) -> dict[int, int]:
    try:
        results_json = getJsonResp("https://ergast.com/api/f1/current/" + str(race) + "/sprint.json")
        results=results_json['MRData']['RaceTable']['Races'][0]['SprintResults']
        retval = {}
        for result in results:
            driver = result['Driver']
            retval[int(driver['permanentNumber'])] = int(result['position'])
   
        return retval
    except Exception as e:
        # print(str(e))
        # This is OK for races that haven't happend yet.
        return None
    
def _getQualifying(race : int) -> dict[int, int]:
    try:
        results_json = getJsonResp("https://ergast.com/api/f1/current/" + str(race) + "/qualifying.json")
        results=results_json['MRData']['RaceTable']['Races'][0]['QualifyingResults']
        retval = {}
        for result in results:
            driver = result['Driver']
            retval[int(driver['permanentNumber'])] = int(result['position'])
 
        return retval
    except Exception as e:
        # print(str(e))
        # This is OK for races that haven't happend yet.
        return None
    
def _getResults(race : int) -> dict[int, int]:
    try:
        results_json = getJsonResp("https://ergast.com/api/f1/current/" + str(race) + "/results.json")
        results=results_json['MRData']['RaceTable']['Races'][0]['Results']
        retval = {}
        for result in results:
            driver = result['Driver']
            retval[int(driver['permanentNumber'])] = int(result['position'])

        return retval
    except Exception as e:
        print(str(e))
        return None
    

q = Queue()
t1 = None
lock = Lock()
cache_drivers = None
cache_races = None

def updateLoop():
    while True:
        try:
            q.get(timeout=1200) #20 minutes
            logger.info("Got End Message")
            break
        except Exception as e:
            # Expected
            populateCache()

def getDrivers() -> list[Driver]:
    global cache_drivers
    return cache_drivers

def getSchedule() -> list[Race]:
    global cache_races
    return cache_races

def populateCache():

    global cache_drivers
    global cache_races

    logger.info("Populating Cache")
    drivers = _getDrivers()
    if drivers is None:
        return
    races = _getSchedule()
    if races is None:
        return
    for race in races:
        if not race.canPick():
            results = _getResults(race.id)
            if results is not None:
                race.setResults(results)
        else:
            qualifying = _getQualifying(race.id)
            logger.info("Qualifying = " + str(qualifying))
            sprint = _getSprint(race.id)
            logger.info("Sprint = " + str(sprint))
            if qualifying is not None:
                race.setQualifying(qualifying)
            if sprint is not None:
                race.setSprint(sprint)
            if qualifying is None and sprint is None:
                break
    
    lock.acquire()
    cache_drivers = drivers
    cache_races = races
    lock.release()

def getUserByCode(code) -> storage.User:
    return storage.getUserByCode(code)

def getDriversForUser(id : int) -> dict[int, int]:
    picks = storage.getDriversForUser(id)
    return picks

def getDriverById(id) -> Driver:
    lock.acquire()
    for driver in cache_drivers:
        if driver.number == id:
            lock.release()
            return driver
    lock.release()
    return None

def getPicksForRace(race, user) -> list[int]:
    picks = storage.getPicksForRace(race, user)    
    return picks

def getAllPicksForRace(race) -> dict[int, list[int]]:    
    return storage.getAllPicksForRace(race)

def getScoresForRace(id) -> dict[int, int]:    
    scores = None
    lock.acquire()
    race = _getRaceById(id)
    if race.results is not None and race.allPicks is not None:    
        scores = {}    
        for driver in cache_drivers:
            if driver.number in race.allPicks:           
                for user in race.allPicks[driver.number]:            
                    place = race.results[driver.number]
                    if user not in scores:
                        scores[user] = 0
                    scores[user] = scores[user] + place
        for user in getUsers():
            if user not in scores:
                scores[user] = 60
        newscores = dict(sorted(scores.items(), key=lambda x:x[1]))
        scores = newscores
    lock.release()
    return scores
   
def getDriverUsage() -> dict[int, dict[int, int]]: 
    lock.acquire()
    picks = {}
    
    for race in cache_races:
        if not race.canPick():
            upicks = storage.getAllPicksForRace(race.id)
            for driver in cache_drivers:                
                if driver.number in upicks:
                    # logger.info("Driver = " + str(driver.number))
                    for user in upicks[driver.number]:
                        if user not in picks:
                            picks[user] = {}
                        if driver.number not in picks[user]:
                            picks[user][driver.number] = 0
                        picks[user][driver.number] = picks[user][driver.number] + 1
                        
    lock.release()
    return picks

def getStandings():
    global cache_races
    global cache_drivers
    scores = {}
    lock.acquire()

    for race in cache_races:

        if race.results is not None and race.allPicks is not None: 
            raceusers = {}
            for driver in cache_drivers:
                upicks = storage.getAllPicksForRace(race.id)

                if driver.number in upicks:
                
                    for user in upicks[driver.number]:            
                        raceusers[user] = True
                        place = race.results[driver.number]
                        if user not in scores:
                            scores[user] = 0
                        scores[user] = scores[user] + place
            for user in getUsers():
                if user not in raceusers:
                    if user not in scores:
                        scores[user] = 60
                    else:
                        scores[user] = scores[user] + 60
                    
    standings = dict(sorted(scores.items(), key=lambda x:x[1]))
    lock.release()
    return standings

#def getPicksForRace(id) -> :

def getRaceById(id, user=None) -> Race:
    lock.acquire()
    race = _getRaceById(id, user)
    lock.release()
    return race

def _getRaceById(id, user=None) -> Race:
    retval = None
    
    for race in cache_races:        
        if int(id) == race.id:
            retval = race
            break
    
    allPicks = storage.getAllPicksForRace(id)
    logger.info("All Picks for race: " + str(race.name) + " = " + str(len(allPicks)))
    retval.setAllPicks(allPicks)
    if user is None:
        return retval
    
    picks = storage.getPicksForRace(id, user)
    retval.setUserPicks(picks)
    return retval

def clearPicks(race, user):
    storage.clearPicks(race, user)

def validatePicks2(user, race, picks):
    return storage.validatePicks2(user, race, picks)

def setPicks2(user, race, picks):
    return storage.setPicks2(user, race, picks)

def validatePicks(user, race, p1, p2, p3):
    return storage.validatePicks(user, race, p1, p2, p3)

def setPicks(user, race, p1, p2, p3):
    return storage.setPicks(user, race, p1, p2, p3)

def startup():
    global t1
    if t1 is None:    
        t1 = Thread(target=updateLoop)
        populateCache()
        t1.start()
        

def shutdown():
    print("Shutting down update thread")
    global t1
    if t1 is not None:
        q.put(("",))

        t1.join()
        t1 = None

atexit.register(shutdown)

logger = logging.getLogger("F1")
    