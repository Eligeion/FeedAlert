import json
from time import sleep

import mysql.connector
import cassiopeia as cass
import riotwatcher as rw

cass.set_riot_api_key("RIOT-API-KEY")
cass.set_default_region("NA")

matchmm = 3154904286  # 3152058384

watcher = rw.RiotWatcher('RIOT-API-KEY')
my_region = 'na1'

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="",
    database="lol_database"
)

mycursor = mydb.cursor()


def getRedSideByMatch(id):
    return cass.get_match(id).red_team.to_json()


def getBlueSideByMatch(id):
    return cass.get_match(id).blue_team.to_json()


def getGameByMatchID(id):
    return cass.get_match(id).to_json()


def players(side, g, match):
    j = json.loads(side)
    p = j['participants']
    for x in p:
        feedingPercent(x, g, side, match, x['summonerName'])


def feedingPercent(x, g, side, match, name):
    feedScore = 0
    lane = x['timeline']['lane']
    role = x['timeline']['role']
    if role == "DUO_SUPPORT":
        lane = "SUPPORT"
    stats = x['stats']
    kills = stats['kills']
    deaths = stats['deaths']
    assists = stats['assists']
    duration = gameDuration(g)
    expectedDeaths = averageDeathsWithoutPlayer(side, x)
    if deaths > expectedDeaths:
        feedScore += int(((deaths - expectedDeaths) * 49))
    damage = stats['totalDamageDealtToChampions']
    expectedDamage = averageDamageWithoutPlayer(side, x)
    # if damage < expectedDamage and lane != "SUPPORT":
    #    if feedScore > 90 and ((damage - expectedDamage) < ((duration / 60) * 5)):
    #        feedScore += int(((expectedDamage - damage) / 8))
    goldSpent = stats['goldSpent']
    goldEarned = stats['goldEarned']
    if goldSpent < goldEarned * .6:
        feedScore += 200
    level = stats['champLevel']
    expectedLevel = averageTeamLevelWithoutPlayer(side, x)
    if level < expectedLevel:
        if lane == "SUPPORT":
            if feedScore < 100:
                feedScore += int((expectedLevel - level - 2) * 50)
            else:
                feedScore += int((expectedLevel - level - 1) * 50)
        else:
            if level < expectedLevel - 3:
                feedScore += int((expectedLevel - level) * 100)
            else:
                feedScore += int((expectedLevel - level) * 50)
    timeLiving = stats['longestTimeSpentLiving']
    expectedTimeLiving = averageTimeSpentLiving(side, x)
    # if timeLiving < expectedTimeLiving + 120:
    #     feedScore += int(((expectedTimeLiving-120-timeLiving)*.7))
    #     print(str(((expectedTimeLiving-timeLiving)*.7)))
    if feedScore < 0:
        feedScore = 0
    if not matchRecorded(match, name):
        recordPlayer(x, feedScore, match)
    return "(" + lane + "   Level: " + str(level) + "    Feed Score: " + str(feedScore) + ")"


def gameDuration(g):
    j = json.loads(g)
    return j['gameDuration']


def averageTeamLevelWithoutPlayer(side, p):
    totalLevel = 0
    side = json.loads(side)
    for l in side['participants']:
        if l['summonerId'] != p['summonerId']:
            totalLevel += l['stats']['champLevel']
    return int(totalLevel / 4)


def averageDeathsWithoutPlayer(side, p):
    totalDeaths = 0
    side = json.loads(side)
    for l in side['participants']:
        if l['summonerId'] != p['summonerId']:
            totalDeaths += l['stats']['deaths']
    return int(totalDeaths / 4)


def averageDamageWithoutPlayer(side, p):
    totalDamage = 0
    side = json.loads(side)
    for l in side['participants']:
        if l['summonerId'] != p['summonerId']:
            totalDamage += l['stats']['totalDamageDealtToChampions']
    return int(totalDamage / 4)


def averageDamageToTurrets(side, p):
    totalDamage = 0
    side = json.loads(side)
    for l in side['participants']:
        if l['summonerId'] != p['summonerId']:
            totalDamage += l['stats']['damageDealtToTurrets']
    return int(totalDamage / 4)


def averageTimeSpentLiving(side, p):
    totalDamage = 0
    side = json.loads(side)
    for l in side['participants']:
        if l['summonerId'] != p['summonerId']:
            totalDamage += l['stats']['longestTimeSpentLiving']
    return int(totalDamage / 4)


def numberOfDuplicateItems(side, p):
    totalDamage = 0
    for l in side['participants']:
        if l['summonerId'] != p['summonerId']:
            totalDamage += l['stats']['longestTimeSpentLiving']
    return int(totalDamage / 4)


def getMatchHistoryByName(name):
    player = watcher.summoner.by_name(my_region, name)
    ml = watcher.match.matchlist_by_account(encrypted_account_id=player['accountId'], region=my_region)
    return ml['matches']


def getFeedersMatchHistory(name):
    history = getMatchHistoryByName(name)
    print("Loading match history for: " + name)
    for x in history:
        blue = getBlueSideByMatch(x['gameId'])
        red = getRedSideByMatch(x['gameId'])
        game = getGameByMatchID(x['gameId'])
        if int(json.loads(game)['duration']) > 300:
            players(red, game, x['gameId'])
            players(blue, game, x['gameId'])
        sleep(3)
    getNextPlayer()


def matchRecorded(matchId, name):
    mycursor.execute("SELECT * FROM lol_game WHERE match_id='" + str(matchId) + "' AND player_name='" + name + "'")
    res = mycursor.fetchall()
    return len(res) != 0


def recordPlayer(p, feedScore, matchId):
    sqls = "INSERT INTO `lol_game`(`match_id`, `player_name`, `player_id`, `player_team`, `player_position`, " \
           "`player_kills`, `player_deaths`, `player_assists`, `player_feedScore`, `champion_id`, `icon_id`) VALUES (" \
           "'" + str(matchId) + "', '" + str(p['summonerName']) + "', '" + str(p['summonerId']) + "', '" \
           + str(p['side']) + "', '" + str(p['id']) + "', '" + str(p['stats']['kills']) + "', '" \
           + str(p['stats']['deaths']) + "', '" + str(p['stats']['assists']) + "', '" + str(feedScore) + "', '" \
           + str(p['championId']) + "', '" + str(p['profileIconId']) + "') "
    mycursor.execute(sqls)
    mydb.commit()


def getNextPlayer():
    sqls = "SELECT player_name FROM lol_game WHERE player_name IN (SELECT player_name FROM lol_game GROUP BY " \
           "player_name HAVING COUNT(*)<5) LIMIT 1 "
    mycursor.execute(sqls)
    res = mycursor.fetchall()
    if res:
        getFeedersMatchHistory(str(res[0][0]))
    else:
        getNextPlayer()


getNextPlayer()
