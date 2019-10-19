import cassiopeia as cass
import json

cass.set_riot_api_key("RIOT-PLS")
cass.set_default_region("NA")

matchID = 3152058384

red = cass.get_match(matchID).red_team.to_json()
blue = cass.get_match(matchID).blue_team.to_json()
game = cass.get_match(matchID).to_json()


def players(side, g):
    j = json.loads(side)
    p = j['participants']
    for x in p:
        kills = str(x['stats']['kills'])
        deaths = str(x['stats']['deaths'])
        assists = str(x['stats']['assists'])
        print(j['side'] + ": " + x['summonerName'] + "  (" + kills + "/" + deaths + "/" + assists + ")")
        print(feedingPercent(x, g, side))
    print("")


def feedingPercent(x, g, side):
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
        feedScore += int(((deaths-expectedDeaths)*43))
    damage = stats['totalDamageDealtToChampions']
    expectedDamage = averageDamageWithoutPlayer(side, x)
    if damage < expectedDamage:
        if feedScore > 90 and ((damage-expectedDamage) < ((duration/60)*5)):
            feedScore += int(((expectedDamage-damage)/8))
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
            feedScore += int((expectedLevel - level) * 50)

    return "(" + lane + "   Level: " + str(level) + "  Feed Score:" + str(feedScore) + ")\n"


def gameDuration(g):
    j = json.loads(g)
    return j['gameDuration']


def averageTeamLevelWithoutPlayer(side, p):
    totalLevel = 0
    side = json.loads(side)
    for l in side['participants']:
        if l['summonerId'] != p['summonerId']:
            totalLevel += l['stats']['champLevel']
    return int(totalLevel/4)


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


print(game)
players(blue, game)
players(red, game)
