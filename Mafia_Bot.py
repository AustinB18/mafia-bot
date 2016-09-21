#!/usr/bin/env python
import time
import random
from random import shuffle

import praw

import OAuth2Util
from settings import user_agent

r = praw.Reddit(user_agent)
o = OAuth2Util.OAuth2Util(r)

print("Logging in....\n")
o.refresh(force=True)
print("Logged in!\n")

print("Connecting to subreddit...\n")
subreddit = r.get_subreddit('RedditBotMafiaTest')
print("Connected to r/RedditBotMafiaTest!")

print("Loading game data...\n")
gameData = open("data.txt", "r+") #File where games are stored
gameIDList = [] #List of ongoing mafia games (thread ids)
gameList = [] #List of Game objects
maxPlayers = 3


class Game: #I created this object because I think it will make it easier to store information about a game if we have an object for it
    def __init__(self,threadID1):
        self.threadID = threadID1
    playerList = [] #List of players in the game
    started = ['0'] #Has the game started or not
    roleList = ["godfather","mafioso","sheriff","sheriff","doctor","doctor","sk"] 
    playerRoleList = [] #Which player is assigned to which role
    randomPlayerList = []
    masterArray = []
    nightEvents = [['0'],['0'],['0'],['0'],['0'],['0'],['0'],['0'],['0'],['0']] #stores everything that happens to each player at night (list of lists)
    day = 1
    skip = 0
    lynchCount = [0,0,0,0,0,0,0,0,0,0]
    def load(self):
        with open(self.threadID + '.txt','r') as loadFile:
            for line in loadFile: 
                self.masterArray.append(line.rstrip().split(",")) #This is a way to get an entire array line by line from a txt file
        self.playerList = self.masterArray[0]
        self.started = self.masterArray[1]
        self.roleList = self.masterArray[2]
        self.day = int(self.masterArray[3][0])
        for i in range(4,14):
            self.nightEvents[i-4] = self.masterArray[i]
        self.randomPlayerList = self.masterArray[14]
        self.skip = int(self.masterArray[15][0])
        for i in range(0,10):
            self.lynchCount[i] = int(self.masterArray[16][i])
        loadFile.close()
    def save(self):
        saveFile = open(self.threadID + '.txt', 'w')
        saveFile.truncate() #clears the contents
        for s in self.playerList:
            saveFile.write(s)
            if self.playerList.index(s) != len(self.playerList)-1:
                saveFile.write(',')
        saveFile.write("\n")
        for s in self.started:
            saveFile.write(str(s))
            if self.started.index(s) != len(self.started)-1:
                saveFile.write(',')
        saveFile.write("\n")
        for s in self.roleList:
            saveFile.write(s)
            if self.roleList.index(s) != len(self.roleList)-1:
                saveFile.write(',')
        saveFile.write("\n")
        saveFile.write(str(self.day))
        saveFile.write("\n")
        for alist in self.nightEvents:
            for s in alist:
                saveFile.write(s)
                if alist.index(s) != len(alist)-1:
                    saveFile.write(',')
            saveFile.write('\n')
        for s in self.randomPlayerList:
            saveFile.write(s)
            if self.randomPlayerList.index(s) != len(self.randomPlayerList)-1:
                saveFile.write(',')
        saveFile.write('\n')
        saveFile.write(str(self.skip))
        saveFile.write('\n')
        i = 0
        for integer in self.lynchCount:
            saveFile.write(str(integer))
            if i != len(self.lynchCount)-1:
                saveFile.write(',')
            i+=1
        saveFile.write('\n')
        saveFile.close()

def initGameList():
    for line in gameData:#Initialize the gameList to whatever is in data.txt
        gameIDList.append(line.rstrip())
    for ID in gameIDList:
        newGameObject = Game(ID)
        newGameObject.load()
        gameList.append(newGameObject)

def updateGameList():
    submissions = subreddit.get_hot()
    for sub in submissions:
        if sub.id not in gameIDList and sub.title.find("!") != -1: #Checks that the game isn't already in the gameList and that the submisison has a "!" in the title 
            gameIDList.append(sub.id)
            newGameObject = Game(sub.id)
            newGameObject.save()
            gameList.append(newGameObject)
            print("[" + sub.title + "] added\n")
            gameData.write(sub.id + "\n")


def processGames():
    for game in gameList:
        if game.started[0] == '0':
            submission = r.get_submission(submission_id=game.threadID)
            for comment in submission.comments:
                if comment.body == "!join" and comment.author.name not in game.playerList:
                    game.playerList.append(comment.author.name)
                    print(game.playerList)
                if len(game.playerList) >= maxPlayers: #  NEW  : 'maxPlayers' will have to be given a value somewhere
                    game.started[0] = '1' #  NEW  : sets to 1 if game is full. 

        if game.started[0] == '1': #  NEW  : everything in this 'if' statement is new code
            temp = []
            for user in game.playerList:
                temp.append(user)
            for thing in temp:
                game.randomPlayerList.append(thing)
            random.shuffle(game.playerList) # calls function to randomize the roles, *now accepts the game object in question as a parameter
            print(game.randomPlayerList)
            print(game.playerList)
            #pmPlayers(game) # messages the players their roles
            game.started[0] = '2' # sets to 2 after everyone is assigned a role and has been messaged

        if game.started[0] == '2': #  NEW  : everything in 'if' statement is new code, once roles are assigned and players are messaged, this if statement will execute
            thread = r.get_submission(url=None,submission_id=game.threadID)
            playerText = ""
            for player in game.randomPlayerList:  
                playerText+=player
                playerText+="\n\n"
            #thread.add_comment("**Mafia Day %s** \n\nPlayer list: %s" %(str(game.day),playerText) + "\n\nLynch vote: !lynch name\n\nSkip Day: !skip")
            game.started[0] = '3'

        if game.started[0] == '3':
            monitorComments(game)
            

def monitorComments(game):
    submission = r.get_submission(url=None,submission_id=game.threadID)
    for comment in submission.comments:
        if comment.body.find("!lynch") and comment.author != "MafiaBot":
            print('skip found')
            replies = comment.replies
            found = False
            for reply in replies:
                print(reply.author)
                if reply.author == "MafiaBot":
                    found = True
            if not found:
                comment.reply("Vote counted. Current skip vote: " + str(game.skip))
        if comment.body.find("!lynch") and comment.author != "MafiaBot":
            print('lynch found')
            pos = checkForUsername(game,comment)
            game.lynchCount[pos]+=1
            comment.reply("Vote counted. Current lynch vote for " + str(game.playerList[pos]) + ": " + str(game.lynchCount[pos]))


def checkForUsername(game,comment):
    for player in game.playerList:
        if comment.body.find(player):
            return game.playerList.index(player)

def processPM():
    for msg in r.get_unread():
        user = msg.author
        for game in gameList:
            if user in game.playerList:
                pos = game.playerList.index(user) 
                kill = msg.body.find('kill')
                heal = msg.body.find('heal')
                check = msg.body.find('check')
                if kill and (pos == 0 or pos == 1 or pos == 6):
                    player = game.randomPlayerList[int(msg.body[kill+2])-1] #look 2 indeces after the word "kill" to find the number they want to kill
                    game.nightEvents[game.playerList.index(player)].append('-1') #convert the number they want to kill from randomPlayerList to playerList and add the -1 to their event list
                if heal and (pos == 4 or pos == 5):
                    player = game.randomPlayerList[int(msg.body[heal+2])-1]
                    game.nightEvents[game.playerList.index(player)].append('1')
                if check and (pos == 2 or pos == 3):
                    player = game.randomPlayerList[int(msg.body[check+2])-1]
                    if game.randomPlayerList.index(player) and (pos == 1 or pos == 6):
                        r.send_mesage(user,'Your target seems suspicious...',from_sr=None,raise_captcha_exception=True)
                    else:
                        r.send_mesage(user,'Your target seems unsuspicious...',from_sr=None,raise_captcha_exception=True)
                        
                        
                    

#  NEW  : pm's the players their roles, *also accepts the game object as a parameter
def pmPlayers(game):
    i = 0
    print("Messaging players their roles.....\n")
    while i < maxPlayers: 
        r.send_message(game.playerList[i],'Mafia Game Role','Your role is: %s.\n\n  Check the side bar for details on your role!' %(game.roleList[i]),from_sr=None,raise_captcha_exception=True)
        i+=1               
        time.sleep(10)
    print("Done!\n\n")
        # basically, the relationship between the player and their role is that they share the same index number (player at index 0 of randomizedPlayerList will be the role at index 0 in the roleList)




initGameList()
choice = 1

while choice is not '0':
    print("1. Update game list \n2. Enter max number of players \n3. Process Games\nPress 0 to exit\n")
    choice = input()

    if choice == '1':
        print("updating")
        updateGameList()
        print(gameIDList)

    if choice == '2':
        print("Enter the max number of players: ")
        maxPlayers = int(input())

    if choice == '3':
        processGames()

#    if choice == '4': #  NEW  : Choice 3 will have the user pick the game (threadID) and then enter the picked game's max players
#        print("Pick a Game ID to inititalize its number of players: \n")
#        print(    + "\nType the wanted game ID: ")
#        pickedGame = input()
#
#        while maxPlayers != '0':
#            if pickedGame in :
#                print("\n  Now enter the max amount of players (more than zero): ")
#                maxPlayers = input()
#            
#            else:
#                print("Entered ID not in list\n")
        
              

for game in gameList:
    game.save()
gameData.close() 
