import os
import sys
import api
import logging
from flask import Flask, request, redirect, render_template
from werkzeug.exceptions import abort
from flask_moment import Moment
import datetime
import json

#from flask_bootstrap import Bootstrap


app = Flask(__name__)
#Bootstrap(app)

moment = Moment(app)

@app.route("/races", methods=['GET','POST'])
@app.route("/", methods=['GET','POST'])
def index():
    if request.cookies.get("usercode") is None:
        return error("Please use the login link you were emailed")
    
    user = api.getUserByCode(request.cookies.get("usercode"))
    if user is None:
        return error("Sorry, your user could not be found.")

    races = api.getSchedule()
    if races is None:
        return error("Sorry, something has gone terribly wrong")
    
    return render_template('races.html', races=races)


@app.route("/login/<code>", methods=['GET','POST'])
def login(code):
    user = api.getUserByCode(code)
    if user is None:
        return error("Sorry, that code is not valid!")
    
    response = redirect('/')
    expire_date = datetime.datetime.now()
    expire_date = expire_date + datetime.timedelta(days=270)
    response.set_cookie('usercode', code, expires=expire_date)
    return response

@app.route("/user/<code>", methods=['GET','POST'])
def userpage(code):

    user = api.getUserByCode(code)
    if user is None:
        abort(404)
    return render_template('user.html', user=user.name)

@app.route("/drivers", methods=['GET','POST'])
def drivers():

    drivers = api.getDrivers()
    if drivers is None:
        abort(404)
    users = api.getUsers()
    picks = api.getDriverUsage()

    return render_template('drivers.html', drivers=drivers, users=users, picks=picks)

@app.route("/standings", methods=['GET','POST'])
def standings():
    
    if request.cookies.get("usercode") is None:
        return error("Please use the login link you were emailed")
    code = request.cookies.get("usercode")
    user = api.getUserByCode(code)
    if user is None:
        abort(404)
    standings = api.getStandings()
    users = api.getUsers()
    race_scores = []
    races = api.getSchedule()
    for race in races:
        if not race.canPick():
            race_scores.append(api.getScoresForRace(race.id))

    if standings is None:
        return error("Something when wrong getting the standings")
    
    return render_template('standings.html', standings=standings, race_scores=race_scores, users=users)


@app.route("/race/<id>", methods=['GET','POST'])
def race(id):
    if request.cookies.get("usercode") is None:
        return error("Please use the login link you were emailed")
    code = request.cookies.get("usercode")
    race = api.getRaceById(id)
    user = api.getUserByCode(code)
    if user is None:
        abort(404)

    if request.method == 'POST':
        if 'clear' in request.form:
            api.clearPicks(id, user.id)
        else:
            pick1 = int(request.form['pick1'])
            pick2 = int(request.form['pick2'])
            pick3 = int(request.form['pick3'])
            print("Picks: " + str(pick1) + " " + str(pick2) + " " + str(pick3))
            if pick1 is None or pick2 is None or pick3 is None:
                return error("Not all picks made")
            
            if pick1 == pick2 or pick2 == pick3 or pick1 == pick3:
                return error("Picks are not valid")
                

            if race is None or not race.canPick():
                return error("Race was not pickable")
            if api.validatePicks(user.id, id, pick1, pick2, pick3):
                api.setPicks(user.id, id, pick1, pick2, pick3)
            else:
                return error("Picks were not valid")

    drivers = api.getDriversForUser(user.id)
    if race is None or drivers is None:
        return error("Error getting drivers for the race")
    
    picks = api.getPicksForRace(id, user.id)
    if not picks is None and len(picks) != 3:
        picks = None

    allpicks = None
    if not race.canPick():
        allpicks = api.getAllPicksForRace(id)

    return render_template('race.html', race=race, user=user, drivers=drivers, picks=picks, allpicks=allpicks)


@app.route("/race2/<id>", methods=['GET','POST'])
def race2(id):
    if request.cookies.get("usercode") is None:
        return error("Please use the login link you were emailed")
    code = request.cookies.get("usercode")
    user = api.getUserByCode(code)
    race = api.getRaceById(id)
    if race is None:
        abort (404)
    if user is None:
        abort(404)

    if request.method == 'POST':
        if 'clear' in request.form:
            api.clearPicks(id, user.id)
        else:
            logger.info(len(request.form))
            
            if len(request.form) == 0:
                api.clearPicks(id, user.id)
            else:
                picks = [None, None, None]
                count = 0
                if len(request.form) > 3:
                    return error("Picks are not valid")
                for value in request.form:
                    picks[count] = value
                    count = count + 1
                                
                print("Picks: " + str(picks[0]) + " " + str(picks[1]) + " " + str(picks[2]))
                for i in range(len(request.form)):
                    for j in range(i+1,count):
                        if picks[i] == picks[j]:
                            return error("Picks are not valid")    

                if race is None or not race.canPick():
                    return error("Race was not pickable")
                if api.validatePicks2(user.id, id, picks):
                    logger.info("Setting picks")
                    api.setPicks2(user.id, id, picks)
                else:
                    return error("Picks were not valid")
                
    race = api.getRaceById(id, user.id)
    scores = api.getScoresForRace(id)

    drivers = api.getDrivers()
    if drivers is None or len(drivers) == 0: 
        return error("Dang shit has gone WRONG")
    counts = api.getDriversForUser(user.id)
    users = api.getUsers()
    # if race is None or drivers is None:
    #     return error("Error getting drivers for the race")
    
    # picks = api.getPicksForRace(id, user.id)

    # if picks is not None:
    #     for pick in picks:
    #         for driver in drivers:
    #             if picks[pick] == driver.name:
    #                 driver.setPickedByUser()
    #                 break


    # allpicks = None
    # if not race.canPick():
    #     allpicks = api.getAllPicksForRace(id)

    # return render_template('race2.html', race=race, user=user, drivers=drivers, picks=picks, allpicks=allpicks)
    return render_template('race2.html', race=race, drivers = drivers, scores=scores, users=users, counts=counts)



def error(errorstring):
    return render_template('error.html', error=errorstring)

    
if __name__ == "__main__":

    logger = logging.getLogger("F1")
    formatter = logging.Formatter('[%(levelname)s] %(message)s')
    handler = logging.StreamHandler()
    try:
        prod = os.environ['PRODUCTION']
        if prod == "1":
            prod = True
    except Exception as e:
        prod = False    

    if prod:
        handler = logging.StreamHandler(sys.stdout)
        
    handler.setFormatter(formatter)

    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    logger.debug("Startup")
    try:
        if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
            api.startup()
        app.run(host="0.0.0.0",debug=True, port=6000)
    finally:
        api.shutdown()




