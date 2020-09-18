ScriptName = "WR"
Website = "https://speedrun.com/"
Description = "Pulls the World Record for a Category when called with 'commandName Category'" #See Line 15
Creator = "AuroTheAzure"
Version = "1.2.0"

''' 
Notes:
    Cooldowns on lines 16 and 17 are in seconds.
    Line 16 is the command cooldown
    Line 17 is the individual user cooldown
    Match Category in Twitch Title to the Tab in hte main board. :) (Any% | World Peace | All Red Berries | 70 Star etc.
'''

commandName = "!wr"     #String to start the command
cooldown = 2            #Cooldown of the command in seconds
userCooldown = 30

import datetime         #For converting time from a number of seconds to a human readable format (1:23:45.67)
import json             #For quickly / easily parsing data from speedrun.com/

headers = {'Client-ID': 'umyyc7qkoxedtjir8wo50iinz6qzs8'}  #No touchey

def Init():
    return


def Execute(data):
    if data.GetParam(0) != commandName or Parent.IsOnCooldown(ScriptName, commandName) or not Parent.IsLive() or Parent.IsOnUserCooldown(ScriptName, commandName, data.User):
        #If we're not called with our command name, or we're on cooldown, or the user who called it is on cooldown, quit.
        #Parent.Log("!wr", "The game is {}".format(game))
        return
    else:
        game, title = getGame()
        #Parent.Log("!wr", "{} {}".format(game, title))
        if game == -1 and title == -1:
            send_message("There was an issue grabbing the game / title from Twitch.")
            return
        gameURL = SpeedrunGame(game)
        url, category = getCategories(gameURL, title)
        if url == -5 and category == -5:            # This means the category wasn't found in the twitch title
            send_message("I couldn't find any categories in the stream title.")
            return
        elif url == -2 and category == -2:          # This means the category page failed to load.
            send_message("Contact the creator, because your game is not currently supported.") #Gotta get more work somehow :)
            return
        runs = getRuns(url)
    
        try:
            WRrun = runs[0]['run'] #WR run
        except IndexError:
            send_message("There is no verified WR for {} {}".format(game, category))
            return
        #Parent.Log("!wr", str(WRrun))
        #Parent.Log("!wr", str(type(WRrun)))
        runner_name = getRunnerName(WRrun['players'][0]['id'])
        Time = WRrun['times']['primary_t']
        #Parent.Log("!wr", str(type(Time)))
        TimeParsed = datetime.timedelta(seconds=Time)
        TimeString = str(TimeParsed)
        while TimeString[0] == '0' or TimeString[0] == ':':
            TimeString = TimeString[1::]
        if '.' in TimeString:
            TimeString = TimeString[0:TimeString.index('.')+4] # Cut the time down to 3 decimal places at most
        send_message("The (Verified) WR in {} {} is {} held by {}.".format(game, category, TimeString, runner_name))
        Parent.AddUserCooldown(ScriptName, commandName, data.User, userCooldown)
        Parent.AddCooldown(ScriptName, commandName, cooldown)
	return


def Tick():
    return


def SpeedrunGame(TwitchGameName):
    #TwitchGameName is Game according to Twitch
    #Format for the return is [mainboard, category extension]
    #Parent.Log("!wr", "Game Name: {}".format(TwitchGameName))
    IdList = []
    #Parent.Log("!wr", "Reaching out to speedrun.com")
    SearchBlob = Parent.GetRequest("https://speedrun.com/api/v1/games?name={}".format(TwitchGameName), {})
    #Parent.Log("!wr", SearchBlob)
    SearchBlob = json.loads(SearchBlob)
    #Parent.Log("!wr", str(SearchBlob['status']))
    if SearchBlob['status'] == 200:
        #Parent.Log("!wr", "Successful query.")
        blob = json.loads(SearchBlob['response'])
        for each in blob['data']:
            if each['names']['twitch'] == TwitchGameName:
                Parent.Log("!wr", "Found match: {}".format(each['id']))
                if not each['romhack']:
                    IdList.append(each['id'])
    return IdList

def getRunnerName(speedrunner_id):
    #Get the runners ID from speedrun.com to query the speedrun API less.
    #Parent.Log("!wr", "Pulling from speedrun.com/api/v1/users/{}".format(speedrunner_id))
    runnerPage = Parent.GetRequest("https://speedrun.com/api/v1/users/{}".format(speedrunner_id), {})
    runnerPage = json.loads(runnerPage)                     #Get speedrun.com data for user code
    #Parent.Log("!wr", "Runner Page: {}".format(runnerPage))
    runnerPage = json.loads(runnerPage['response'])
    speedrunner_name = runnerPage['data']['names']['international']   #Grab international username for current WR holder
    #Parent.Log("!wr", "Runner Name is {}".format(speedrunner_name))
    return speedrunner_name
	
    
def getGame():
    #Pulls the json blob from Decapi.me, and returns the Game (As a string), and the Title of the stream.
    #Parent.Log("!wr", "Pulling stream information from decapi.me")
    GameName = Parent.GetRequest("https://decapi.me/twitch/game/{}".format(Parent.GetChannelName()), headers)
    GameName = json.loads(GameName) # Parent.GetRequest pulls information back as a string, we're converting it to a json object
    if GameName['status'] == 200:  # If successful response
        game = GameName['response']
        title = Parent.GetRequest("https://decapi.me/twitch/title/{}".format(Parent.GetChannelName()), headers)
        title = json.loads(title)
        if title['status'] == 200:
            title = title['response']
            #Parent.Log("!wr", "Title is {}".format(title))
            #Parent.Log("!wr", "Game is {}".format(game))
            return game, title
        else:
            Parent.Log("!wr", "Issue pulling title from decapi.me")
            return -5, -5
    Parent.Log("!wr", "Issue pulling game from decapi.me")
    return -1, -1


def getCategories(game, TwitchTitle):
    #Uses the speedrun API to get a list of category names for the game being run
    #This functions returns a link to the leaderboard page, and the name of the category to print later...
    #Debating returning the blob
    categories = {}     # Category : Records Page
    #Parent.Log("!wr", "Game: {}".format(game))
    #Parent.Log("!wr", "TwitchTitle: {}".format(TwitchTitle))
    #Parent.Log("!wr", "Getting list of category names from speedrun.com.")
    for each in game:
        CategoryPage = Parent.GetRequest("https://speedrun.com/api/v1/games/{}/categories".format(each), {})
        CategoryPage = json.loads(CategoryPage)
        #Parent.Log("!wr", "{}".format(CategoryPage['status']))
        if CategoryPage['status'] == 200:
            CategoryPage = json.loads(CategoryPage['response'])
            TwitchTitleUpper = TwitchTitle.upper()
            for each in CategoryPage['data']:
                #Parent.Log("!wr", "checking for {} in Title.".format(each['name']))
                if each['name'].upper() in TwitchTitleUpper and each['type'] == "per-game":
                    for link in each['links']:
                        if link['rel'] == "records":
                            categories[each['name']] = link['uri']
        else:   #Failed to load the categories page for the game ('game' value does not point to a valid page)
            Parent.Log("!wr", "{} has no categories page.".format(each))
            return -2, -2
    if categories:
        LongestMatch = max(categories.keys(),key=len)
        return categories[LongestMatch], LongestMatch
    else:   
        #If we found no matching category in the title of the stream
        Parent.Log("!wr", "Error pulling the categories for {}.".format(game))
        return -5, -5
    
def getRuns(LeaderboardURL):
    #Pull the list of runs from the speedrun api
    Leaderboard = Parent.GetRequest(LeaderboardURL, {})
    Leaderboard = json.loads(Leaderboard)
    #Parent.Log("!wr", str(Leaderboard))
    if Leaderboard['status'] != 200:
        Parent.Log("There was an issue getting the leaderboard {}.".format(LeaderboardURL))
        return "Blame speedrun.com for being broken. :)"
    Leaderboard = json.loads(Leaderboard['response'])
    return Leaderboard['data'][0]['runs']

def send_message(message):
    Parent.SendStreamMessage(message)
    return
