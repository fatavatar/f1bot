import storage
import sys
import datetime

if len(sys.argv) != 4:
    print("Usage: " + sys.argv[0] + " <race> <date> <time>")
    print(str(len(sys.argv)))
    sys.exit(1)

name=sys.argv[1]
date=sys.argv[2]
time=sys.argv[3]
print("Adding race " + name + " with date " + date + " at time " + time)

timestring = date + " " + time
date = datetime.datetime.strptime(timestring, '%m/%d/%Y %H%M')

print("Date in UTC is: " + date.astimezone(datetime.timezone.utc).strftime('%d/%m/%Y %H:%M'))

if storage.addRace(name, date):    
    print("Success!")
else:
    print("Failed!")


