import os
import sys
import storage
import logging
from flask import Flask, request, redirect, render_template
from werkzeug.exceptions import abort
from flask_moment import Moment
#from flask_bootstrap import Bootstrap


app = Flask(__name__)
#Bootstrap(app)

moment = Moment(app)

@app.route("/", methods=['GET','POST'])
def index():
    if request.cookies.get("usercode") is None:
        return error("Please use the login link you were emailed")
    
    user = storage.getUserByCode(request.cookies.get("usercode"))
    if user is None:
        return error("Sorry, your user could not be found.")

    races = storage.getRaces()
    if races is None:
        return error("Sorry, something has gone terribly wrong")
    
    return render_template('races.html', races=races)


@app.route("/login/<code>", methods=['GET','POST'])
def login(code):
    user = storage.getUserByCode(code)
    if user is None:
        return error("Sorry, that code is not valid!")
    
    response = redirect('/')
    response.set_cookie('usercode', code)
    return response

@app.route("/user/<code>", methods=['GET','POST'])
def userpage(code):

    user = storage.getUserByCode(code)
    if user is None:
        abort(404)
    return render_template('user.html', user=user.name)

@app.route("/drivers", methods=['GET','POST'])
def drivers():

    drivers = storage.getDrivers()
    if drivers is None:
        abort(404)
    return render_template('drivers.html', drivers=drivers)


@app.route("/race/<id>", methods=['GET','POST'])
def race(id):
    if request.cookies.get("usercode") is None:
        return error("Please use the login link you were emailed")
    code = request.cookies.get("usercode")
    race = storage.getRace(id)
    user = storage.getUserByCode(code)
    if user is None:
        abort(404)

    if request.method == 'POST':
        if 'clear' in request.form:
            storage.clearPicks(id, user.id)
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
            if storage.validatePicks(user.id, id, pick1, pick2, pick3):
                storage.setPicks(user.id, id, pick1, pick2, pick3)
            else:
                return error("Picks were not valid")

    drivers = storage.getDriversForUser(user.id)
    if race is None or drivers is None:
        return error("Error getting drivers for the race")
    
    picks = storage.getPicksForRace(id, user.id)
    if not picks is None and len(picks) != 3:
        picks = None

    allpicks = None
    if not race.canPick():
        allpicks = storage.getAllPicksForRace(id)

    return render_template('race.html', race=race, user=user, drivers=drivers, picks=picks, allpicks=allpicks)

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
    app.run(host="0.0.0.0",debug=True)




