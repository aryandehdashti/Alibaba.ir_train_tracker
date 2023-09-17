import os
import requests
import jdatetime
import json

BASE_URI = 'https://ws.alibaba.ir/api'




def convertUserDate(userDate):
    jdate = jdatetime.datetime.strptime(userDate,"%Y-%m-%d").date()
    return jdate.togregorian().strftime('%Y-%m-%d')


def searchCities(value):
    with open('cities.json') as f:
        data = json.load(f)
        for item in data:
            if item['name'] == value or item['name_en'] == value:
                return item['code']
    return None

def searchTrips(org,dest,date):
    with open('trips.json') as f:
        data = json.load(f)
        for item in data:
            if item['origin'] == org and item['destination'] == dest and item['departureDate'] == date:
                return item


def getCitiesID(userOrg,userDst):
    originCode = searchCities(userOrg)
    destinationCode = searchCities(userDst)

    return originCode, destinationCode

class Trip:
    def __init__(self,userOrigin,userDestination,userDate):
        self.faOrigin = userOrigin
        self.origin = searchCities(userOrigin)
        self.faDestination = userDestination
        self.destination = searchCities(userDestination)
        self.faDepartureDate = userDate
        self.departureDate = convertUserDate(userDate)
        try:
            self.token = requests.post(f"{BASE_URI}/v2/train/available", json={
                "passengerCount": "1",
                "ticketType": "Family",
                "isExclusiveCompartment": "false",
                "departureDate": self.departureDate,
                "destination": self.destination,
                "origin": self.origin
            }).json()['result']['requestId']
        except requests.exceptions.RequestException as err:
            print(f'Some error occured while get available Train token in alibaba (try again and remove this trip): {str(err)}')
        self.lastCheck = ""
        self.lastUpdate = ""
    def to_dict(self):
        jsonTrip = {
            'origin': self.origin,
            'faOrigin': self.faOrigin,
            'destination': self.destination,
            'faDestination':self.faDestination,
            'departureDate': self.departureDate,
            'faDepartureDate': self.faDepartureDate,
            'token': self.token,
            'lastCheck': self.lastCheck,
            'lastUpdate': self.lastUpdate
        }
        if os.path.getsize("trips.json") > 0:
            with open("trips.json") as f:
                data = json.load(f)
            data.append(jsonTrip)
            with open("trips.json", "w") as f:    
                json.dump(data, f)
        else:
            with open("trips.json", "w") as f:    
                json.dump([jsonTrip], f)


class Train:
    def __init__(self, proposalId, originName, destinationName, originCode, destinationCode, timeOfArrival, moveDatetime, cost, availableSeats):
        self.proposalId = proposalId
        self.originName = originName
        self.destinationName = destinationName
        self.timeOfArrival = timeOfArrival
        self.moveDatetime = moveDatetime
        self.cost = cost
        self.availableSeats = availableSeats
        self.originCode = originCode
        self.destinationCode = destinationCode
        self.lookingFor = True
        self.lastCheck = ""
        self.lastUpdate = ""
    def to_dict(self):
        jsonTrain = {
            'proposalId':self.proposalId,
            'originName':self.originName,
            'destinationName':self.destinationName,
            'timeOfArrival':self.timeOfArrival,
            'moveDatetime':self.moveDatetime,
            'cost':self.cost,
            'availableSeats':self.availableSeats,
            'originCode':self.originCode,
            'destinationCode':self.destinationCode,
            'lookingFor':self.lookingFor,
            'lastCheck':self.lastCheck,
            'lastUpdate':self.lastUpdate
        }
        if os.path.getsize("trains.json") > 0:
            with open("trains.json") as f:
                data = json.load(f)
            data.append(jsonTrain)
            with open("trains.json", "w") as f:    
                json.dump(data, f)
        else:
            with open("trains.json", "w") as f:    
                json.dump([jsonTrain], f)

    
def showAllTrips():
    with open('trips.json') as f:
        data = json.load(f)
        return data
        

    
def getTripsTickets(token):
    try:
        res = requests.get(f"{BASE_URI}/v1/train/available/{token}")
        res.raise_for_status()
        tickets = []
        for i in  res.json()['result']['departing']:
            tickets.append({'destinationCode':i['destinationCode'],'originCode':i['originCode'],'proposalId':str(i['proposalId']),'originName':i['originName'],'destinationName':i['destinationName'], 'moveDatetime':i['moveDatetime'], 'timeOfArrival':i['timeOfArrival'],'cost':str(i['cost']),'availableSeats':str(i['seat'])})
        return tickets
    except requests.exceptions.RequestException as err:
        print(f'Some error occured while get alibaba train trips: {str(err)}')
        return None
    
def getTrains(originCode, destinationCode, moveDatetime):
    trains = []
    with open('trains.json','r') as f:
        data = json.load(f)
        for item in data:
            if item['originCode'] == originCode and item['destinationCode'] == destinationCode and item['moveDatetime'] == moveDatetime:
                trains.append(item)
    return trains

def getSpecialTrains():
    trains = []
    with open('trains.json') as f:
        data = json.load(f)
        for item in data:
            if item['lookingFor'] == True:
                trains.append(item)
    return trains


def removeTrip(org, dest, date):
    with open('trips.json') as f:
        data = json.load(f)
    for item in data:
        if item['faOrigin'] == org and item['faDestination'] == dest and item['faDepartureDate'] == date:
            data.remove(item)
            break
    with open('trips.json', 'w') as f:
        json.dump(data, f)


def getTripToken(origin, destination, departureDate):
    with open('trips.json') as f:
        data = json.load(f)
    for item in data:
        if item['origin'] == origin and item['destination'] == destination and item['departureDate'] == departureDate:
            return item['token']

def removeTrain(proposalId):
    with open('trains.json') as f:
        data = json.load(f)
    for item in data:
        if item['proposalId'] == proposalId:
            data.remove(item)
            break
    with open('trains.json', 'w') as f:
        json.dump(data, f)


def isTrainTicketAvailable(tickets):
        return any(int(item['availableSeats']) > 0 for item in tickets)








