import requests
import json

url = "https://f1-live-motorsport-data.p.rapidapi.com/races/2023"

headers = {
	"X-RapidAPI-Key": "21ae9fff4cmshf7ccd5fed26825fp1bd0d1jsn6982ceeb63b4",
	"X-RapidAPI-Host": "f1-live-motorsport-data.p.rapidapi.com"
}

response = requests.request("GET", url, headers=headers)
responsejson = json.loads(response.text)
# print(json.dumps(responsejson["results"][0], indent=2))
# print(json.dumps(responsejson["results"][2], indent=2))

url = "https://f1-live-motorsport-data.p.rapidapi.com/session/" + str(responsejson["results"][2]["sessions"][0]['id'])
response = requests.request("GET", url, headers=headers)
responsejson = json.loads(response.text)
print(json.dumps(responsejson["results"], indent=2))
