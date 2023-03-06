import storage
import sys

if len(sys.argv) != 3:
    print("Usage: " + sys.argv[0] + " <name> <team>")
    print(str(len(sys.argv)))
    sys.exit(1)

name=sys.argv[1]
team=sys.argv[2]
print("Adding driver " + name + " with team " + team)

if storage.addDriver(name, team):    
    print("Success!")
else:
    print("Failed!")


