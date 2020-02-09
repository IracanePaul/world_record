ScriptName = "WR"
Website = "https://speedrun.com/"
Description = "Pulls the World Record for a Category when called with 'commandName Category'" #See Line 15
Creator = "AuroTheAzure"
Version = "1.1.0"

''' 
Notes:
    Currently only works with top 50 runners.  For some weird reason code can't pull back past runner...58 or so, so 50 to be safe.
    Please make sure the name on like 18 matches your speedrun.com username
    Cooldown on line 16 is in seconds.
    Match Category in Twitch Title to the Tab in hte main board. :) (Any% | World Peace | All Red Berries | 70 Star etc.
'''

commandName = "!wr"     #String to start the command
cooldown = 1            #Cooldown of the command in seconds

import datetime         #For converting time from a number of seconds to a human readable format (1:23:45.67)
import json             #For quickly / easily parsing data from speedrun.com/


headers = {'Client-ID': 'umyyc7qkoxedtjir8wo50iinz6qzs8'}  #No touchey

def Init():
    return


def Execute(data):
    if data.GetParam(0) != commandName or Parent.IsOnCooldown(ScriptName, commandName) or not Parent.IsLive():
        #If we're not called with our command name, or we're on cooldown, quit.
        #Parent.Log("!wr", "The game is {}".format(game))
        return
    else:
        game, title = getGame()
        if game == -1 and title == -1:
            send_message("There was an issue grabbing the game / title from Twitch.")
            return
        gameURL = SpeedrunGame(game)
        url, category = getCategories(gameURL, title)
        if url == -5 and category == -5:            # This means the category wasn't found in the twitch title
            gameURL = CategoryExtensions(game)
            url, category = getCategories(gameURL, title)
            if url == -5 and category == -5:
                send_message("I couldn't find any categories in the stream title.")
                return
        elif url == -2 and category == -2:          # This means the category page failed to load.
            send_message("Contact the creator, because your game is not currently supported.") #Gotta get more work somehow :)
            return
        runs = getRuns(url)
    
        WRrun = runs[0]['run'] #WR run
        Parent.Log("!wr", str(WRrun))
        Parent.Log("!wr", str(type(WRrun)))
        runner_name = getRunnerName(WRrun['players'][0]['id'])
        Time = WRrun['times']['primary_t']
        TimeParsed = datetime.timedelta(seconds=Time)
        TimeString = str(TimeParsed)
        while TimeString[0] == '0' or TimeString[0] == ':':
            TimeString = TimeString[1::]
        if '.' in TimeString:
            TimeString = TimeString[0:TimeString.index('.')+4] # Cut the time down to 3 decimal places at most
        send_message("The WR in {} {} is {} held by {}.".format(game, category, TimeString, runner_name))
	return


def Tick():
    return


def SpeedrunGame(TwitchGameName):
    #TwitchGameName is Game according to Twitch
    if TwitchGameName == "Super Mario Odyssey":     #SMO Main board
        return "smo"
    elif TwitchGameName == "Super Mario 64":        #SM64 Main Board
        return "sm64"
    elif TwitchGameName == "Celeste":               #Celeste Main Board
        return "celeste"
    elif TwitchGameName == "Super Mario Sunshine":
        return "sms"
    elif TwitchGameName == "Yu-Gi-Oh! Forbidden Memories":
        return "yugiohfm"

def CategoryExtensions(TwitchGameName):
    #TwitchGameName is the Game according to Twitch
    if TwitchGameName == "Super Mario Odyssey":     #SMO Category Extensions
        return "smoce"
    elif TwitchGameName == "Super Mario 64":        #SM64 Category Extensions
        return "sm64memes"
    elif TwitchGameName == "Celeste":               #Celeste Category Extensions
        return "celeste_category_extensions"
    elif TwitchGameName == "Super Mario Sunshine":
        return "smsce"
    elif TwitchGameName == "Yu-Gi-Oh! Forbidden Memories":
        return "yugiohfmextensions"

def getRunnerName(speedrunner_id):
    #Get the runners ID from speedrun.com to query the speedrun API less.
    Parent.Log("!wr", "Pulling from speedrun.com/api/v1/users/{}".format(speedrunner_id))
    runnerPage = Parent.GetRequest("https://speedrun.com/api/v1/users/{}".format(speedrunner_id), {})
    runnerPage = json.loads(runnerPage)                     #Get speedrun.com data for user code
    Parent.Log("!wr", "Runner Page: {}".format(runnerPage))
    runnerPage = json.loads(runnerPage['response'])
    speedrunner_name = runnerPage['data']['names']['international']   #Grab international username for current WR holder
    Parent.Log("!wr", "Runner Name is {}".format(speedrunner_name))
    return speedrunner_name
	
    
def getGame():
    #Pulls the json blob from twitch, and returns the Game (As a string), and the Title of the stream.
    Parent.Log("!wr", "Connecting to Twitch API to pull the game you're playing.")
    r = Parent.GetRequest("https://api.twitch.tv/helix/streams?user_login={}".format(Parent.GetChannelName()), headers)
    rJson = json.loads(r)       #Parent.GetRequest pulls information back as a string, we're converting it to a json object
    if rJson['status'] == 200:  # If successful response
        Live = 1
        GameJson = json.loads(rJson['response'])
        #Parent.Log("!wr", "GameJson: {}".format(GameJson))
        Game_Code = GameJson['data'][0]['game_id']
        #Parent.Log("!wr", str(Game_Code))
        #Twitch api stores games as an ID (######) we need a human readable game name
        r = Parent.GetRequest("https://api.twitch.tv/helix/games?id={}".format(Game_Code), headers)
        r = json.loads(json.loads(r)['response'])
        game = r['data'][0]['name']
        title = GameJson['data'][0]['title']
        Parent.Log("!wr", "Title is : {}".format(title))
        Parent.Log("!wr", "Game is {}".format(game))
        return game, title
    return -1, -1


def getCategories(game, TwitchTitle):
    #Uses the speedrun API to get a list of category names for the game being run
    #This functions returns a link to the leaderboard page, and the name of the category to print later...
    #Debating returning the blob
    Parent.Log("!wr", "Getting list of category names from speedrun.com.")
    CategoryPage = Parent.GetRequest("https://speedrun.com/api/v1/games/{}/categories".format(game), {})
    CategoryPage = json.loads(CategoryPage)
    if CategoryPage['status'] == 200:
        CategoryPage = json.loads(CategoryPage['response'])
        TwitchTitleUpper = TwitchTitle.upper()
        for each in CategoryPage['data']:
            Parent.Log("!wr", "checking for {} in Title.".format(each['name']))
            if each['name'].upper() in TwitchTitleUpper:
                for link in each['links']:
                    if link['rel'] == "records":
                        return link['uri'], each['name']
    else:   #Failed to load the categories page for the game
        Parent.Log("!wr", "{} has no categories page.".format(game))
        return -2, -2
    #If we found no matching category in the title of the stream
    Parent.Log("!wr", "Error pulling the categories for {}.".format(game))
    return -5, -5
    
def getRuns(LeaderboardURL):
    #Pull the list of runs from the speedrun api
    Leaderboard = Parent.GetRequest(LeaderboardURL, {})
    Leaderboard = json.loads(Leaderboard)
    Parent.Log("!wr", str(Leaderboard))
    if Leaderboard['status'] != 200:
        Parent.Log("There was an issue getting the leaderboard {}.".format(LeaderboardURL))
        return "Blame speedrun.com for being broken. :)"
    Leaderboard = json.loads(Leaderboard['response'])
    return Leaderboard['data'][0]['runs']

def send_message(message):
    Parent.SendStreamMessage(message)
    return
