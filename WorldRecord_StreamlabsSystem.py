ScriptName = "ddWorldRecord"
Website = "https://speedrun.com/"
Description = "Pulls World Record for Category when called with 'commandName Category'" #See Line 7
Creator = "AuroTheAzure"
Version = "1.0.0"

commandName = "!wr"
cooldown = 1
global game
game = ""
# Script will pull your current game (On Twitch, Sorry Mixer) when the command is run.
# Currently has help for SMO, Celeste, and SM64 :")

import json             # For quickly / easily parsing data from speedrun.com/
from re import split    # For splitting times for formatting from 1H1M1S to 1:01:01

global Live
headers = { 'Client-ID': 'umyyc7qkoxedtjir8wo50iinz6qzs8'}

def Init():
    global Live
    Live = 0
    return


def Execute(data):
    global Live
    global game
    if Parent.IsLive() and Live == 0:
        game = getGame()
        if game != "":  #If we have a game, we don't come back in here
            Live = 1
    if data.GetParam(0) != commandName or Parent.IsOnCooldown(ScriptName, commandName):
        #If we're not called with our command name, or we're on cooldown, quit.
        #Parent.Log("!wr", "The game is {}".format(game))
        return
    elif data.GetParamCount() < 2:
        game = getGame()
        #If we're called without a category, Inform the user that we need a category, then quit.
        weError(game)
        return
    else:
        #Parent.Log("!wr", "Called with {} arguments.".format(data.GetParamCount()))
        if data.GetParamCount() == 3:
            game = data.GetParam(1)
            #Parent.Log("!wr", "Game is {} Should be {}".format(game,data.GetParam(1)))
            category = data.GetParam(2)
        else:
            game = getGame()
            category = data.GetParam(1)
        url, category = getUrl(category.upper(), game)
        response = Parent.GetRequest(url, {})                   #Send a get request
        page = json.loads(response)                             #Parse the get request to a json
        if page['status'] != 200:
            send_message("There was a problem grabbing the {} leaderboard for {} ,"
                         " are you sure you got the format the same way as speedrun? (_'s instead of spaces?)".format(category, game))
            return
        page = json.loads(page['response'])                     #Grab the data portion
        WorldRecordRun = page["data"]["runs"][0]                #Grab the specific run
        #Parent.Log("!wr", str(WorldRecordRun))                 #Log the json of the run
        Time = WorldRecordRun['run']['times']['primary'][2::]   #Grab the time (1H12M38.423S format)
        TimeParsed = "" 
            
        TimeParsed = split('[A-Za-z]', Time)                    #Split time into digits
        TimeParsed = TimeParsed[0:-1]                           #Remove the trailing section due to split
        for i, each in enumerate(TimeParsed):                   #This loop sucks.
            if i == 0:                                          #Ignore the first place (Most Significant time unit)
                pass                                            #Then pad the rest to 2 characters
            else:
                TimeParsed[i] = each.rjust(2,'0')
                
        TimeParsed = ":".join(TimeParsed)                       #Join the times to get 1:42:13
        User = WorldRecordRun['run']['players'][0]['id']        #Grab User ID
        UserResponse = Parent.GetRequest("https://speedrun.com/api/v1/users/{}".format(User), {})
        UserPage = json.loads(UserResponse)                     #Get speedrun.com data for user code
        UserPage = json.loads(UserPage['response'])             #Make speedrun.com data parsable
        username = UserPage['data']['names']['international']   #Grab international username for current WR holder
        
        send_message("The current World Record for {} {} is {} held by {}".format(game, category, TimeParsed, username))
	
        Parent.AddCooldown(ScriptName, commandName, cooldown)
    return


def Tick():
    return


def getUrl(category, title):
    #Title is Game, Category is type of run, in all caps
    #Parent.Log("!wr", "We're in the GetURL section.")
    #Parent.Log("!wr", "The game is {} Category is {}".format(title, category))
    Display = category
    
    if title == "Super Mario Odyssey":      #SMO Main board
        title = "smo"
        #Parent.Log("!wr", "Game is {}".format(title))
        if category == "ANY" or category == "ANY%":
            category = "Any"
            Display = "Any%"
        elif category == "WP":
            category = "World_Peace"
            Display = "World Peace"
        elif category == "DARK":
            category = "Dark_Side"
            Display = "Dark Side"
        elif category == "DARKER":
            category = "Darker_Side"
            Display = "Darker Side"
        elif category == "100" or category == "100%":
            category = "100"
            Display = "100%"
        elif category == "AM":
            category = "All_Moons"
            Display = "All Moons"
    elif title == "Super Mario 64":     #SM64 Main Board
        title = "sm64"
        #Parent.Log("!wr", "Game is {} Part Duex".format(title))
        if category == "120":
            category = "120_Star"
            Display = "120 Stars"
        elif category == "70":
            category = "70_Star"
            Display = "70 Star"
        elif category == "16":
            category = "16_Star"
            Display = "16 Star"
        elif category == "1":
            category = "1_Star"
            Display = "1 Star"
        elif category == "0":
            category = "0_Star"
            Display = "0 Star"
    elif title == "Celeste":           #Celeste Main Board
        title = "celeste"
        #Parent.Log("!wr", "Game is {}".format(title))
        if category == "ANY" or category == "ANY%":
           category = "Any"
           Display = "Any%"
        elif category == "TE" or category == "TRUE":
            category = "True_Ending"
            Display = "True Ending"
        elif category == "ARB":
            category = "All_Red_Berries"
            Display = "All Red Berries"
        elif category == "AH":
            category = "All_Hearts"
            Display = "All Hearts"
        elif category == "AC":
            category = "All_Chapters"
            Display = "All Chapters"
        elif category == "100" or category == "100%":
            category = "100"
            Display = "100%"
    url = 'https://speedrun.com/api/v1/leaderboards/{}/category/{}'.format(title, category)
    Parent.Log("!wr", "Attemping to grab {}'s {} leaderboard".format(title, category))
    return url, Display


def getGame():
    Parent.Log("!wr", "Connecting to Twitch API to pull the game you're playing.")
    r = Parent.GetRequest("https://api.twitch.tv/helix/streams?user_login={}".format(Parent.GetChannelName()), headers)
    rJson = json.loads(r)
    if rJson['status'] == 200:
        Live = 1
        GameJson = json.loads(rJson['response'])
        Game_Code = GameJson['data'][0]['game_id']
        #Parent.Log("!wr", str(Game_Code))
        r = Parent.GetRequest("https://api.twitch.tv/helix/games?id={}".format(Game_Code), headers)
        r = json.loads(json.loads(r)['response'])
        global game 
        game = r['data'][0]['name']
        Parent.Log("!wr", "Game is {}".format(game))
    return game


def weError(gamename):
    if gamename == "Super Mario Odyssey":
        send_message("Please include the category name. (Any, WP, Dark, Darker, AM, 100%)")
        return
    elif gamename == "Celeste":
        send_message("Please include the category name. (Any, True, ARB, AH, AC, 100)")
    elif gamename == "Super Mario 64":
        send_message("Please include the Star count. (120, 70, 16, 1, 0)")
        
        
def send_message(message):
    Parent.SendStreamMessage(message)
    return