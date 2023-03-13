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
    def __init__(self, number, firstname, lastname, code, team):
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
    
    def setUsage(self, picks):
        self.usage = picks
    
    def setPickedByUser(self):
        self.picked = True
    
    def addPicker(self, user):
        self.pickers.append(user)
        
        

class Race:
    def __init__(self, id, name, start):
        self.start = start
        self.name = name
        self.id = int(id)
        self.results = None
    
    def setResults(self, results):
        self.results = results
        
    def canPick(self):
        return self.start > datetime.datetime.now()

class Result:
    def __init__(self, driver, position):
        self.driver = driver
        self.position = position


def getJsonResp(url):
    response = urlopen(url)
    data_json = json.loads(response.read())
    return data_json


def _getDrivers():
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

def _getSchedule():
    try:
        data_json = getJsonResp("https://ergast.com/api/f1/current.json")
        schedule=data_json['MRData']['RaceTable']['Races']
        retval = []
        for event in schedule:
            racetime = datetime.datetime.strptime(event['date'] + " " + event['time'], "%Y-%m-%d %H:%M:%SZ")
            race = Race(int(event['round']), event['raceName'], racetime)
            retval.append(race)
        return retval
    except Exception as e:
        print(str(e))
        return None
    
def _getResults(race):
    try:
        results_json = getJsonResp("https://ergast.com/api/f1/current/" + str(race) + "/results.json")
        results=results_json['MRData']['RaceTable']['Races'][0]['Results']
        retval = {}
        for result in results:
            driver = result['Driver']
            #team = result['Constructor']['name']
            retval[int(driver['permanentNumber'])] = int(result['position'])
            # newdriver = Driver(int(driver['permanentNumber']), driver['givenName'], driver['familyName'], driver['code'], team)
            # place = Result(newdriver, )
            #retval.append(place)     
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

def getDrivers():
    global cache_drivers
    return cache_drivers

def getSchedule():
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
    
    lock.acquire()
    cache_drivers = drivers
    cache_races = races
    lock.release()

def getUserByCode(code):
    return storage.getUserByCode(code)

def getDriversForUser(id):
    picks = storage.getDriversForUser(id)
    if picks is None:
        return cache_drivers
    
    lock.acquire()
    newdrivers=[]
    for driver in cache_drivers:
        newdriver = copy.deepcopy(driver)
        if newdriver.number in picks:
            newdriver.setUsage(picks[newdriver.number])
        newdrivers.append(newdriver)
    lock.release()
    return newdrivers

def getDriverById(id):
    lock.acquire()
    for driver in cache_drivers:
        if driver.number == id:
            lock.release()
            return driver
    lock.release()
    return None

def getPicksForRace(race, user):
    picks = storage.getPicksForRace(race, user)
    if picks is None:
        return None
    for pick in picks:
        driver = picks[pick]
        picks[pick] = getDriverById(driver).name
    return picks

def getAllPicksForRace(race):
    try:
        picks = storage.getAllPicksForRace(race)
        race = getRaceById(race)

        if picks is None:
            return None
        lock.acquire()
        retval = [None] * len(cache_drivers)   
            
        place = 0
        for driver in cache_drivers:
            newdriver = copy.deepcopy(driver)
            for user in picks:
                for up in picks[user]:
                    theirdriver = picks[user][up]
                    if theirdriver == newdriver.number:
                        print("Adding user " + user + " for driver " + newdriver.name + " on pick " + str(up))
                        newdriver.addPicker(user)
            if race.results is not None:
                place = race.results[newdriver.number]     
                newdriver.finishplace=place
                print("Place = " + str(place))           
            else:
                place = place + 1
            retval[place-1] = newdriver
                # picks[pick] = getDriverById(driver).name
        lock.release()
        return retval
        # for user in picks:
        #     print(user)
        #     for up in picks[user]:
        #         print(up)
        #         driver = picks[user][up]
        #         # logger.info("Pick = " + str(driver))            
        #         picks[user][up] = getDriverById(driver).name
        #         #print(picks[user][up])
        # return picks    
    except Exception as e:
        print(str(e))
        return None

def getStandings():
    global cache_races
    scores = {}
    lock.acquire()
    for race in cache_races:
        if race.results is not None:
            picks = storage.getAllPicksForRace(race.id)
            if picks is None:
                continue

            for user in picks:
                for up in picks[user]:
                    theirdriver = picks[user][up]
                    place = race.results[theirdriver]
                    if user not in scores:
                        scores[user] = 0
                    scores[user] = scores[user] + place
                    
    standings = dict(sorted(scores.items(), key=lambda x:x[1]))
    lock.release()
    return standings


def getRaceById(id):
    lock.acquire()
    for race in cache_races:        
        if int(id) == race.id:
            lock.release()
            return race
    lock.release()
    return None

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
    
# db_races = storage.getRaces()
# for race in schedule:
#     racetime = datetime.datetime.strptime(race['date'] + " " + race['time'], "%Y-%m-%d %H:%M:%SZ")
#     for dbrace in db_races:
#         if dbrace.start == racetime:
#             print(str(race['round']) + " matches Race: " + str(dbrace.id))
#             # storage.mapRaceToApi(dbrace.id, race['round'])

    
# driver_json = getJsonResp("https://ergast.com/api/f1/2023/drivers.json")
# drivers = driver_json['MRData']['DriverTable']['Drivers']

# db_drivers = storage.getDrivers()
# for driver in drivers:
#     name=driver['givenName'] + " " + driver['familyName']
#     found = False
#     for db_driver in db_drivers:
#         if name == db_driver.name:
#             print(driver['code'] + " = " + db_driver.name)
#             storage.mapDriverToApi(db_driver.id, driver['code'], driver['permanentNumber'], driver['givenName'], driver['familyName'])
#             found = True
#     if not found:
#         print(driver['code'] + " could not be matched ( " + name + ")")
    


# response = urlopen("http://ergast.com/api/f1/2023/1/results.json")
# results_json = json.loads(response.read())

# results = results_json['MRData']['RaceTable']['Races'][0]['Results']

# for result in results:
#     #print(json.dumps(result, indent=2))
#     print(result['position'] + " - " + result['Driver']['familyName']) 

# results = getResults(1)
# for result in results:
#     print(str(result.position) + " - " + result.driver.lastname)