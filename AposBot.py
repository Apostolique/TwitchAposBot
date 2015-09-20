"""This file is part of TwitchAposBot.

TwitchAposBot is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

TwitchAposBot is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with TwitchAposBot.  If not, see <http://www.gnu.org/licenses/>."""

import socket
import re
import sys
from datetime import datetime
from threading import Thread
import urllib.request
import simplejson as json
import random
import pycurl
from io import BytesIO
import arrow

from AposBotSettings import KEY, HOST, PORT, NICK, IDENT, REALNAME, CHANNEL, PASSWORD, CURRENTACCOUNT, bot_mod, \
    CHATDATABASE, COMMANDDATABASE, REGEXDATABASE
import threading

# TODO: Record chat statistics, save people's name. Find how active people are.
#      Make the bot be able to join and monitor multiple channels. Settings should be saved based on channels.

database = {}
allCommands = {}
allRegex = {}

giveawayStarted = False
giveawayParticipants = {}

try:
    with open(CHATDATABASE) as fp:
        database = json.load(fp)
except:
    print ("Could not load database. \n{}".format(sys.exc_info()))
    f = open(CHATDATABASE, "w")


def set_interval(func, sec):
    def func_wrapper():
        set_interval(func, sec)
        func()
    timedthread = threading.Timer(sec, func_wrapper)
    timedthread.start()
    return t


def allowed(name, nameList):
    if len(nameList) == 0:
        return True
    for i in nameList:
        if i == name:
            return True
    return False


def parseName(text):
    name = ""
    for i in text[1:]:
        if i != '!':
            name += i
        else:
            return name


def getCommand(text):
    try:
        if text[1] == '!':
            return text[2:].lower()
        else:
            return ""
    except Exception as e:
        return ""


def parseCommands(text, match):
    command = getCommand(text)
    if command is not "" and len(command) == len(match):
        for lt, lc in zip(command, match):
            if lt != lc.lower():
                return False
        return True
    return False


def hello(senderName, channel, message, argument):
    whisperMessage(senderName, "Hello {}!".format(senderName))


def soultran(senderName, channel, message, argument):
    writeMessage("Soultran is the second best Sion played in the world! After Apostolique of course.", channel)


def uptime(senderName, channel, message, argument):
    buffer = BytesIO()
    c = pycurl.Curl()
    c.setopt(c.URL, 'https://api.twitch.tv/kraken/streams/{}'.format(channel[1:]))
    c.setopt(c.WRITEDATA, buffer)
    c.perform()
    c.close()

    body = buffer.getvalue()

    parsed = json.loads(body.decode('utf8'))

    print (json.dumps(parsed, indent=4, sort_keys=True))

    if parsed['stream'] is not None:
        streamUptime = parsed['stream']['created_at']
        dt = arrow.get(streamUptime)
        uptime = arrow.utcnow() - dt
        hourString = "hour" if (uptime.seconds // 3600) == 1 else "hours"
        minuteString = "minute" if ((uptime.seconds // 60) % 60) == 1 else "minutes"
        secondString = "second" if (uptime.seconds % 60) == 1 else "seconds"

        dateMessage = "The stream has been up for {} {}, {} {} and {} {}!".format(uptime.seconds // 3600, hourString,
                                                                                  (uptime.seconds // 60) % 60,
                                                                                  minuteString, (uptime.seconds % 60),
                                                                                  secondString)
        # print (dateMessage)
        writeMessage(dateMessage, channel)
    else:
        writeMessage("Stream is offline", channel)



def setAccount(senderName, channel, message, argument):
    global CURRENTACCOUNT
    writeMessage("Current Account updated to: {}".format(" ".join(message)), channel)
    CURRENTACCOUNT = " ".join(message)


def runes(senderName, channel, message, argument):
    writeMessage("Runes: http://na.op.gg/summoner/rune/userName={}".format(CURRENTACCOUNT), channel)


def masteries(senderName, channel, message, argument):
    writeMessage("Masteries: http://na.op.gg/summoner/mastery/userName={}".format(CURRENTACCOUNT), channel)


def profile(senderName, channel, message, argument):
    writeMessage("Profile: http://na.op.gg/summoner/userName={}".format(CURRENTACCOUNT), channel)


def rank(senderName, channel, message, argument):
    writeMessage("{}".format(getRank(CURRENTACCOUNT)), channel)


def roll(senderName, channel, message, argument):
    writeMessage("Dice roll: {}".format(random.randint(1, 6)), channel)


def quote(senderName, channel, message, argument):
    try:
        quoteLink = "http://www.iheartquotes.com/api/v1/random?source=oneliners&format=json&show_permalink=false&show_source=false"

        quoteURL = urllib.request.urlopen(quoteLink)
        quoteData = json.loads(quoteURL.read().decode('utf8'))

        quoteText = quoteData['quote'].replace("\n", "")

        print (quoteData)

        writeMessage(quoteText, channel)
    except Exception as e:
        writeMessage("Can't quote right now!", channel)


def fact(senderName, channel, message, argument):
    try:
        quoteLink = "http://catfacts-api.appspot.com/api/facts?source=1"

        quoteURL = urllib.request.urlopen(quoteLink)
        quoteData = json.loads(quoteURL.read().decode('utf8'))

        quoteText = quoteData['facts'][0].replace("\n", "")

        print (quoteData)

        writeMessage(quoteText, channel)
    except Exception as e:
        writeMessage("Can't state a fact right now!", channel)


def activity(senderName, channel, message, argument):
    writeMessage("{} has been seen in this channel on {} different days and wrote {} chat lines.".format(senderName,
                                                                                                         database[
                                                                                                             'names'][
                                                                                                             senderName][
                                                                                                             'activity'],
                                                                                                         database[
                                                                                                             'names'][
                                                                                                             senderName][
                                                                                                             'lines']),
                 channel)


def getMusic(senderName, channel, message, argument):
    with open('C:\\Users\\Apos\\Documents\\Snip\\Snip.txt', encoding='utf-8') as f:
        content = f.readlines()
        if len(content) > 0:
            writeMessage(content[0], channel)
        else:
            writeMessage("No songs currently playing.", channel)


def writeText(senderName, channel, message, argument):
    writeMessage(argument, channel);


def start(senderName, channel, message, argument):
    global giveawayStarted
    global giveawayParticipants

    print ("Started Giveaway!")
    giveawayParticipants.clear()
    giveawayStarted = True
    writeMessage("Giveaway started! Write '!enter' to participate!", channel)


def enterGiveaway(senderName, channel, message, argument):
    global giveawayParticipants
    if giveawayStarted:
        if senderName not in giveawayParticipants:
            giveawayParticipants[senderName] = True
            print ("Confirming! {}".format(senderName))
            whisperMessage(senderName, "You are entered!")
        else:
            print ("Confirming! {}".format(senderName))
            whisperMessage(senderName, "You were already entered!")
    else:
        whisperMessage(senderName, "No ongoing giveaway!")


def winner(senderName, channel, message, argument):
    global giveawayStarted
    giveawayWinner = list(giveawayParticipants.keys())[random.randint(0, len(giveawayParticipants) - 1)]
    writeMessage("Winner: {}".format(giveawayWinner), channel)
    whisperMessage(giveawayWinner, "You won! Make sure to claim your prize on twitch.tv/{}".format(channel))
    # giveawayStarted = False


def addCommand(senderName, channel, message, argument):
    print ("Adding command!")

    newCommand = getCommand(" {}".format(message[0]))
    if (newCommand != ""):
        if (newCommand not in allCommands or (newCommand in allCommands and allCommands[newCommand][3])):
            allCommands[newCommand] = [writeText, [], " ".join(message[1:]), True]
            try:
                with open(COMMANDDATABASE) as fp:
                    customC = json.load(fp)
                customC[newCommand] = " ".join(message[1:])

                try:
                    with open(COMMANDDATABASE, 'w') as f:
                        json.dump(customC, f)
                except:
                    print ("Could not save. \n{}".format(sys.exc_info()))
            except:
                print ("Could not load database. \n{}".format(sys.exc_info()))

            writeMessage("Command {} added!".format(newCommand), channel)
        else:
            writeMessage("Nice try but no, I won't add that command.", channel)
            print ("Can't overwrite bot command.")
    else:
        writeMessage("Could not add command, proper syntax: !add !name sentence", channel)
        print ("Could not parse command to add.")


def commandList(senderName, channel, message, argument):
    commandString = ""
    for i in allCommands:
        if allCommands[i][1] == []:
            # print ("Command: {}".format(i))
            commandString = "{} !{},".format(commandString, i)
    # writeMessage(commandString, channel)
    writeMessage(commandString, channel)


def getRank(name):
    try:
        url = "https://na.api.pvp.net/api/lol/na/v1.4/summoner/by-name/{}?api_key={}".format(name.lower(), KEY)

        jsonSummonerUrl = urllib.request.urlopen(url)
        jsonSummonerData = json.loads(jsonSummonerUrl.read().decode('utf8'))

        summonerID = jsonSummonerData[name.lower()]['id']

        url2 = "https://na.api.pvp.net/api/lol/na/v2.5/league/by-summoner/{}/entry?api_key={}".format(summonerID, KEY)

        jsonLeagueURL = urllib.request.urlopen(url2)
        jsonLeagueData = json.loads(jsonLeagueURL.read().decode('utf8'))

        print (jsonLeagueData)

        division = jsonLeagueData["{}".format(summonerID)][0]['entries'][0]['division']
        leaguePoints = jsonLeagueData["{}".format(summonerID)][0]['entries'][0]['leaguePoints']
        tier = jsonLeagueData["{}".format(summonerID)][0]['tier']

        if 'miniSeries' in jsonLeagueData["{}".format(summonerID)][0]['entries'][0]:
            losses = jsonLeagueData["{}".format(summonerID)][0]['entries'][0]['miniSeries']['losses']
            wins = jsonLeagueData["{}".format(summonerID)][0]['entries'][0]['miniSeries']['wins']
            return "Current Rank: {} / {} in {} {} promos".format(wins, losses, tier, division)
        else:
            return "Current Rank: {} {} with {} LP".format(tier, division, leaguePoints)
    except Exception as e:
        print ("------\n{}\n-------".format(e))
        return "Riot's Server didn't respond to the API request."


def whisperMessage(username, text):
    textLen = len(text)
    last = 0
    current = 200

    try:
        while last < textLen:
            print ("Last: {}, len: {}".format(last, textLen))
            t.send(bytes("PRIVMSG #jtv :/w {} {}\r\n".format(username, text[last:current]), 'UTF-8'))
            last = current
            current += 400
    except Exception as e:
        print (e)


def writeMessage(text, channel):
    textLen = len(text)
    last = 0
    current = 200

    while last < textLen:
        print ("Last: {}, len: {}".format(last, textLen))
        s.send(bytes("PRIVMSG {} :{}\r\n".format(channel, text[last:current]), 'UTF-8'))
        last = current
        current += 400


def loadCustomCommands():
    try:
        with open(COMMANDDATABASE) as fp:
            customC = json.load(fp)
        for key in customC:
            # print ("Loading {}".format(key))
            # print ("Text: {}".format(customC[key]))
            allCommands[key] = [writeText, [], customC[key], True]
    except:
        print ("Could not load database. \n{}".format(sys.exc_info()))

def loadRegex():
    try:
        with open(REGEXDATABASE) as fp:
            customC = json.load(fp)
        for reg in range(0,len(customC)):
            # print (customC[reg])
            # print ("Loading {}".format(key))
            # print ("Text: {}".format(customC[key]))
            allRegex[reg] = [writeText, [], customC[reg], True]
    except:
        print ("Could not load database. \n{}".format(sys.exc_info()))




def updateUserDataBase(senderName):
    global database

    if not 'names' in database:
        database['names'] = {}

    currentDate = (datetime.today().date() - datetime.strptime("2014-10-05", "%Y-%m-%d").date()).days

    if senderName in database['names']:
        print ("Yep!")
        database['names'][senderName]['lines'] = database['names'][senderName]['lines'] + 1
        # NOTE: This code would not add activity to someone that only posts once a year on the same day of the year. Kappa.
        if database['names'][senderName]['last-active'] < currentDate:
            database['names'][senderName]['activity'] = database['names'][senderName]['activity'] + 1
            database['names'][senderName]['last-active'] = currentDate
    else:
        print ("Nope")
        database['names'][senderName] = {}
        database['names'][senderName]['lines'] = 1
        database['names'][senderName]['activity'] = 1
        database['names'][senderName]['last-active'] = currentDate


def receiveData():
    global TIME
    global allCommands
    global allRegex
    global bot_mod
    TIME = datetime.now()
    readbuffer = ""

    # allCommands['hello'] = [hello, [], "", False]
    allCommands['soultran'] = [soultran, bot_mod, "", False]
    allCommands['uptime'] = [uptime, [], "", False]
    allCommands['set'] = [setAccount, bot_mod, "", False]
    allCommands['runes'] = [runes, [], "", False]
    allCommands['masteries'] = [masteries, [], "", False]
    allCommands['mastery'] = [masteries, [], "", False]
    allCommands['profile'] = [profile, [], "", False]
    allCommands['rank'] = [rank, [], "", False]
    allCommands['roll'] = [roll, [], "", False]
    allCommands['quote'] = [quote, [], "", False]
    allCommands['fact'] = [fact, [], "", False]
    allCommands['activity'] = [activity, [], "", False]
    allCommands['song'] = [getMusic, [], "", False]
    allCommands['add'] = [addCommand, bot_mod, "", False]
    allCommands['start'] = [start, bot_mod, "", False]
    allCommands['enter'] = [enterGiveaway, [], False]
    allCommands['winner'] = [winner, bot_mod, False]
    allCommands['commands'] = [commandList, [], False]

    loadCustomCommands()
    loadRegex()
    # reg = re.compile("^(?=.*?regex).*$")

    while 1:
        somebytes = s.recv(1024).decode('UTF-8')
        readbuffer += readbuffer + somebytes
        temp = str.split(readbuffer, '\r\n')
        readbuffer = temp.pop()

        for line in temp:
            line = str.rstrip(line)
            line = str.split(line)

            if len(line) > 3:
                if line[1] == 'PRIVMSG':
                    name = parseName(line[0])
                    print ("Message by {} in channel {}".format(name, line[2]))

                    if line[2][1:] == CHANNEL:
                        updateUserDataBase(name)

                    currentCommand = getCommand(line[3])
                    currentMessage = line[3]

                    if currentCommand in allCommands and allowed(name, allCommands[currentCommand][1]):
                        allCommands[currentCommand][0](name, line[2], line[4:], allCommands[currentCommand][2])
                    else:
                        for exp in range(0,len(allRegex)):
                            flagString = allRegex[exp][2]['flags']
                            flags = None
                            for f in range(0,len(flagString)):
                                print (flagString[f])
                                if flagString[f] == "m":
                                    if flags == None:
                                        flags = re.MULTILINE
                                    else:
                                        flags = flags | re.MULTILINE
                                if flagString[f] == "i":
                                    if flags == None:
                                        flags = re.IGNORECASE
                                    else:
                                        flags = flags | re.IGNORECASE
                                if flagString[f] == "s":
                                    if flags == None:
                                        flags = re.DOTALL
                                    else:
                                        flags = flags | re.DOTALL
                                if flagString[f] == "u":
                                    if flags == None:
                                        flags = re.UNICODE
                                    else:
                                        flags = flags | re.UNICODE
                            if flags != None:
                                regToTest = re.compile(allRegex[exp][2]['command'], flags)
                            else:
                                regToTest = re.compile(allRegex[exp][2]['command'])
                            answer = allRegex[exp][2]['answer']
                            if regToTest.match(currentMessage):
                                writeMessage(answer, line[2])
                    try:
                        print (line)
                    except:
                        print ("-----------------------------------")
                        print ("---Failed to print user message.---")
                        print ("-----------------------------------")
                elif line[3] == '+o':
                    bot_mod.append(line[4])
                    print (line)
                    print ("Added " + line[4] +  " as a mod!")
                elif line[3] == '-o':
                    # It removes Mods now. Not so hard.
                    bot_mod.remove(line[4])
                    print (line)
                    print ("Removed a mod!")
                else:
                    print (line)
            if (line[0] == "PING"):
                s.send(bytes("PONG {}\r\n".format(line[1]), 'UTF-8'))


def receiveTeamData():
    junkbuffer = ""

    while 1:
        junkbytes = t.recv(1024).decode('UTF-8')
        junkbuffer += junkbuffer + junkbytes
        junkTemp = str.split(junkbuffer, '\r\n')
        junkbuffer = junkTemp.pop()

        for line in junkTemp:
            line = str.rstrip(line)
            line = str.split(line)
            if (line[0] == "PING"):
                print ("PING PONG")
                t.send(bytes("PONG {}\r\n".format(line[1]), 'UTF-8'))


s = socket.socket()
s.connect((HOST, PORT))
s.send(bytes("PASS oauth:{}\r\n".format(PASSWORD), 'UTF-8'))
s.send(bytes("NICK {}\r\n".format(NICK), 'UTF-8'))
s.send(bytes("USER {} {} bla :{}\r\n".format(IDENT, HOST, REALNAME), 'UTF-8'))
s.send(bytes("CAP REQ :twitch.tv/commands\r\n", 'UTF-8'))
s.send(bytes("CAP REQ :twitch.tv/membership\r\n", 'UTF-8'))
s.send(bytes("JOIN #{}\r\n".format(CHANNEL), 'UTF-8'))

t = socket.socket()
t.connect(("199.9.253.119", 443))
t.send(bytes("PASS oauth:{}\r\n".format(PASSWORD), 'UTF-8'))
t.send(bytes("NICK {}\r\n".format(NICK), 'UTF-8'))
t.send(bytes("USER {} {} bla :{}\r\n".format(IDENT, HOST, REALNAME), 'UTF-8'))
# t.send(bytes("JOIN #{}\r\n".format("_apostolique_1435426130074"), 'UTF-8'))
# t.send(bytes("PRIVMSG #jtv :/w {} {}\r\n".format("apostolique", "Hello World!"), 'UTF-8'))

socketThread = Thread(target=receiveData)
socketThread.start()

teamThread = Thread(target=receiveData)
teamThread.start()

while 1:
    userInput = input()
    if userInput == "quit":
        try:
            print(database['names'])
            with open(CHATDATABASE, 'w') as fp:
                json.dump(database, fp)
        except:
            print ("Could not save. \n{}".format(sys.exc_info()))

        try:
            s.close()
            t.close()
        except:
            print ("Could not end the connection.")
        break
    elif userInput == "save":
        try:
            print(database['names'])
            with open(CHATDATABASE, 'w') as fp:
                json.dump(database, fp)
        except:
            print ("Could not save. \n{}".format(sys.exc_info()))
    elif userInput == "load":
        loadCustomCommands()
    elif userInput == "uptime":
        uptime("", "", "")
    elif userInput == "add":
        print("Mod to add?")
        userInput = input()
        bot_mod.append(userInput)
        print("Done adding that mod manually!")
    elif userInput == "join":
        userInput = input()
        s.send(bytes("JOIN #{}\r\n".format(userInput), 'UTF-8'))
    elif userInput[0] == '\\':
        s.send(bytes("{}\r\n".format(userInput[1:-1]), 'UTF-8'))
    else:
        s.send(bytes("PRIVMSG #{} :{}\r\n".format(CHANNEL, userInput), 'UTF-8'))
