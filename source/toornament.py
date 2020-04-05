import requests
import sys
import json
import re
import datetime
import math
from time import sleep
from discord import Colour

class Toornament:

    def __init__(self, baseFolder, tokenFile, teamsFile, stagesFile, enableAPI = False):
        self.baseFolder = baseFolder
        if not self.baseFolder.endswith('/'):
            self.baseFolder += '/'

        self.tokenFile = tokenFile
        self.teamsFile = teamsFile
        self.stagesFile = stagesFile
        self.enableAPI = enableAPI

        # Reads toornament API token from token file
        try:
            toornamentFile = open(tokenFile, 'r')
            toornamentInfo = [line.rstrip('\n') for line in toornamentFile]

            self.token = toornamentInfo[0].strip()
            self.tournamentID = toornamentInfo[1].strip()
            self.tournamentName = toornamentInfo[2].strip()

            toornamentFile.close()
        except:
            print('Could not read toornament API token file')
            sys.exit('Invalid toornament API token file or data')

        # Loads team emote info
        try:
            teamsFile = open(self.baseFolder + teamsFile, 'r')
            teamInfos = [line.rstrip('\n') for line in teamsFile]
            self.teamInfos = []

            for teamInfo in teamInfos:
                splitInfo = re.split(';', teamInfo)
                teamName = splitInfo[0].strip()
                teamEmote = splitInfo[1].strip()

                nextTeamInfo = TeamInfo()
                nextTeamInfo.name = teamName
                nextTeamInfo.emote = teamEmote
                
                if len(splitInfo) > 2:
                    nextTeamInfo.nickname = splitInfo[2].strip()

                self.teamInfos += [nextTeamInfo]

            teamsFile.close()
        except:
            print('Could not read teams file')
            sys.exit('Invalid team file or data')

        # Loads list of available stages and settings for those
        try:
            stagesFile = open(self.baseFolder + stagesFile, 'r')
            stageInfos = [line.rstrip('\n') for line in stagesFile]
            self.stages = []

            for stageInfo in stageInfos:
                splitInfo = re.split(';', stageInfo)
                stageName = splitInfo[0].strip()
                stageID = splitInfo[1].strip()
                stageGroupID = splitInfo[2].strip()
                stageLogo = splitInfo[3].strip()
                stageColour = splitInfo[4].strip()
                stageAlias = ''
                if len(splitInfo) > 5:
                    stageAlias = splitInfo[5].strip()

                stage = Stage(name = stageName, id = stageID, groupID = stageGroupID, logoURL = stageLogo, colour = stageColour, alias = stageAlias)

                self.stages += [stage]
            
            stagesFile.close()
        except:
            print('Could not read stages info file')
            sys.exit('Invalid stages data')

        # These headers need to be supplied with every API call for authorization
        self.headers = {'X-Api-Key': self.token}
        self.lastCall = datetime.datetime.now()

    # Returns information on the stage with the given name, alias or id
    def getStage(self, name):
        for stage in self.stages:
            if stage.name == name or stage.alias == name or stage.id == name or stage.groupID == name:
                return stage
    
    # Returns information on the team with the given name or nickname
    def getTeam(self, name):
        for teamInfo in self.teamInfos:
            if teamInfo.name == name or teamInfo.nickname == name:
                return teamInfo
                
    # Returns the URL of the tournament page of a given stage
    def getStageURL(self, stage):
        stageURL = f'https://www.toornament.com/en_GB/tournaments/{self.tournamentID}/stages/{stage.id}/'
        if not stage.groupID == '':
            stageURL += f'groups/{stage.groupID}/'

        return stageURL

    # Adds a new team to the list
    def addTeam(self, teamName, teamEmote, teamNickname, save = True):
        # Remove previous entries of the same team
        self.removeTeam(teamName = teamName, save = False)

        # Add new entry
        newTeamInfo = TeamInfo(name = teamName, emote = teamEmote, nickname = teamNickname)
        self.teamInfos += [newTeamInfo]

        # Save table
        if save:
            return self.saveTeamList()
        else:
            return True

    # Removes all exisiting teams with the given name or nickname from the list
    def removeTeam(self, teamName, save = True):
        # Remove team from table
        self.teamInfos = [item for item in self.teamInfos if not (item.name == teamName or item.nickname == teamName)]

        # Save table
        if save:
            return self.saveTeamList()
        else:
            return True

    # Saves team list
    def saveTeamList(self):
        try:
            file = open(self.baseFolder + self.teamsFile, 'w')
            
            for teamInfo in self.teamInfos:
                file.write(teamInfo.toCSV() + '\n')
            
            file.close()
            return True
        except:
            print('Error writing teams file')
            return False


    # Adds new stage to the list
    def addStage(self, fullName, stageID, groupID, logoURL, colour, alias, save = True):
        # Remove all existing entries of the stage
        self.removeStage(stageName = fullName, save = False)

        # Add new stage data
        newStage = Stage(fullName, stageID, groupID, logoURL, colour, alias)
        self.stages += [newStage]

        # Save table
        if save:
            return self.saveStagesList()
        else:
            return True

    # Removes all stages with the given name, alias or id from the list
    def removeStage(self, stageName, save = True):
        # Remove stage from table
        self.stages = [item for item in self.stages if not (item.name == stageName or item.alias == stageName or item.id == stageName or item.groupID == stageName)]
        
        # Save table
        if save:
            return self.saveStagesList()
        else:
            return True

    # Saves stage list
    def saveStagesList(self):
        try:
            file = open(self.baseFolder + self.stagesFile, 'w')

            for stage in self.stages:
                file.write(stage.toCSV() + '\n')
            
            file.close()
            return True
        except:
            print('Error writing stages file')
            return False

    # Returns the current ranking and upcoming fixtures for the given week
    def getWeekInfo(self, stage, weekNumber):

        week = Week()
        week.standings = self.getRanking(stage)
        week.matches = self.getMatches(stage, weekNumber)
        return week

    # Returns the ranking information for the given tournament stage
    # Returns empty rankings in case of API error
    def getRanking(self, stage):

        responseJSON = {}

        # Either reads ranking info from API or existing CSV file
        if self.enableAPI:
            requestURL = f'https://api.toornament.com/viewer/v2/tournaments/{self.tournamentID}/stages/{stage.id}/ranking-items'
            if not groupID == '':
                requestURL += f'?group_ids={stage.groupID}'

            response = requests.get(url = requestURL, headers = self.headers)

            if(response.status_code == 206):
                responseJSON = response.json()
            else:
                return Ranking(stage)
        else:
            try:
                csvFile = open(f'{self.baseFolder}{stage.id}_{stage.groupID}.csv', 'r')

                ranking = Ranking(stage)
                for csvLine in csvFile:
                    team = Team()
                    team.fromCSV(csvLine)
                    teamInfo = self.getTeam(team.name)
                    team.emote = teamInfo.emote
                    if not teamInfo.nickname == '':
                        team.name = teamInfo.nickname
                    ranking.teams += [team]

                csvFile.close()
                return ranking
            except:
                return Ranking(stage)

            # with open(f'{stage.id}_{stage.groupID}.json', 'r') as jsonFile:
            #     responseJSON = json.load(jsonFile)
            #     ranking = Ranking(stage)

        # Reads ranking information for every team in response
        for teamJSON in responseJSON:
            nextTeam = Team()

            teamInfo = self.getTeam(teamJSON['participant']['name'])
            nextTeam.name = teamInfo.name
            nextTeam.emote = teamInfo.emote
            if not teamInfo.nickname == '':
                nextTeam.name = teamInfo.nickname

            nextTeam.position = teamJSON['position']
            nextTeam.rank = teamJSON['rank']
            nextTeam.points = teamJSON['points']

            props = teamJSON['properties']
            nextTeam.wins = props['wins']
            nextTeam.losses = props['losses']
            nextTeam.played = props['played']
            nextTeam.forfeits = props['forfeits']
            nextTeam.gamesWon = props['score_for']
            nextTeam.gamesLost = props['score_against']
            nextTeam.gameDifference = props['score_difference']

            ranking.teams += [nextTeam]
        
        # Sort team by toornament display order (based on ranking)
        ranking.teams = sorted(ranking.teams, key = lambda team: team.position)

        return ranking


    # Returns the fixtures of the given week in the given stage
    # Returns empty list for API errors
    def getMatches(self, stage, week):

        responseJSON = {}
        matches = []

        # Either reads match data from toornament API or manually reported CSV file
        if self.enableAPI:
            requestURL = f'https://api.toornament.com/viewer/v2/tournaments/{self.tournamentID}/matches?round_numbers={week}&stage_ids={stage.id}'
            if not groupID == '':
                requestURL += f'&group_ids={stage.groupID}'

            response = requests.get(url = requestURL, headers = self.headers)

            if response.status_code == 206:
                responseJSON = response.json()
            else:
                return []
        else:
            try:
                csvFile = open(f'{self.baseFolder}{stage.id}_{stage.groupID}_week{week}.csv', 'r')
                
                for csvLine in csvFile:
                    match = Match()
                    match.fromCSV(csvLine)
                    homeTeamInfo = self.getTeam(match.homeTeamName)
                    awayTeamInfo = self.getTeam(match.awayTeamName)
                    match.homeTeamEmote = homeTeamInfo.emote
                    match.awayTeamEmote = awayTeamInfo.emote
                    if not homeTeamInfo.nickname == '':
                        match.homeTeamName = homeTeamInfo.nickname
                    if not awayTeamInfo.nickname == '':
                        match.awayTeamName = awayTeamInfo.nickname
                    matches += [match]

                csvFile.close()
                return matches
            except:
                return Ranking(stage)

            # with open(f'{stage.id}_{stage.groupID}_week{week}.json', 'r') as jsonFile:
            #     responseJSON = json.load(jsonFile)

        # Reads match information for every match
        for matchJSON in responseJSON:
            nextMatch = Match()
            nextMatch.number = matchJSON['number']

            opponents = matchJSON['opponents']
            homeTeam = opponents[0]
            awayTeam = opponents[1]

            homeInfo = self.getTeam(homeTeam['participant']['name'])
            nextMatch.homeTeamName = homeInfo.name
            nextMatch.homeTeamEmote = homeInfo.emote
            if not homeInfo.nickname == '':
                nextMatch.homeTeamName = homeInfo.nickname

            awayInfo = self.getTeam(awayTeam['participant']['name'])
            nextMatch.awayTeamName = awayInfo.name
            nextMatch.awayTeamEmote = awayInfo.emote
            if not awayInfo.nickname == '':
                nextMatch.awayTeamName = awayInfo.nickname
            
            if matchJSON['status'] == 'completed':
                nextMatch.pending = False
                nextMatch.homeScore = homeTeam['score']
                nextMatch.awayScore = awayTeam['score']

            matches += [nextMatch]
        
        return matches
    
    # Writes the standings provided as text into a CSV file so they can be loaded later on
    def reportStandings(self, stageName, standingStr):
        
        stage = self.getStage(stageName)
        teams = []

        standingInfos = re.split('\n', standingStr)

        infoBlockSize = 12
        standingInfoCount = len(standingInfos)
        infoBlockCount = math.floor(standingInfoCount / infoBlockSize)

        for blockIndex in range(0, infoBlockCount):
            lineIndex = blockIndex * infoBlockSize
            nextTeam = Team()

            nextTeam.position = blockIndex + 1
            nextTeam.rank = standingInfos[lineIndex]
            nextTeam.name = standingInfos[lineIndex+2]
            nextTeam.played = standingInfos[lineIndex+3]
            nextTeam.wins = standingInfos[lineIndex+4]
            nextTeam.losses = standingInfos[lineIndex+6]
            nextTeam.forfeits = standingInfos[lineIndex+7]
            nextTeam.gamesWon = standingInfos[lineIndex+8]
            nextTeam.gamesLost = standingInfos[lineIndex+9]
            nextTeam.gameDifference = standingInfos[lineIndex+10]
            nextTeam.points = standingInfos[lineIndex+11]
            nextTeam.emote = self.getTeam(nextTeam.name).emote

            teams += [nextTeam]
        
        try:
            rankFile = open(f'{self.baseFolder}{stage.id}_{stage.groupID}.csv', 'w')

            for team in teams:
                rankFile.write(team.toCSV() + '\n')

            rankFile.close()
            return True
        except:
            return False
        

    # Checks if string can be converted to an int
    def isInt(self, text):
        try:
            int(text)
            return True
        except ValueError:
            return False

    # Writes the fixtures provided as text to a CSV file so they can be loaded later on
    def reportFixtures(self, stageName, weekNumber, matchesStr):

        stage = self.getStage(stageName)
        matches = []

        matchInfos = re.split('\n', matchesStr)
        infoCount = len(matchInfos)
        currentMatch = Match()

        # Uses a state machine to determine which line belongs to which attribute
        state = 0
        lineIndex = 0
        matchCounter = 1
        while lineIndex < infoCount:

            line = matchInfos[lineIndex]

            # State 0: Retrieves home team name
            if state == 0:
                currentMatch.homeTeamName = line
                lineIndex += 2
                state = 1
            
            # State 1: Retrieves either home score or skips this state
            elif state == 1:
                if self.isInt(line):
                    currentMatch.homeScore = int(line)
                    lineIndex += 1
                    state = 2
                else:
                    currentMatch.homeScore = 0
                    state = 2
            
            # State 2: Retrieves away team name
            elif state == 2:
                currentMatch.awayTeamName = line
                lineIndex += 2
                state = 3

            # State 3: Retrieves either away score or skipts this state
            elif state == 3:
                if self.isInt(line):
                    currentMatch.awayScore = int(line)
                    currentMatch.pending = False
                    lineIndex += 1
                    state = 4
                else:
                    currentMatch.pending = True
                    currentMatch.awayScore = 0

                    if line == ' ':
                        lineIndex += 1
                    else:
                        lineIndex += 2
                    state = 4
            
            # Checks if final state was reached, saves match info and resets the state machine
            if state == 4:
                currentMatch.number = matchCounter
                matchCounter += 1
                matches += [currentMatch]
                currentMatch = Match()
                state = 0

        # Writes all matches to CSV file
        try:
            matchesFile = open(f'{self.baseFolder}{stage.id}_{stage.groupID}_week{weekNumber}.csv', 'w')

            for match in matches:
                matchesFile.write(match.toCSV() + '\n')

            matchesFile.close()
            return True
        except:
            return False


# Stores information of a game week like upcoming matches and standings
class Week:
    def __init__(self):
        self.matches = []
        self.standings = {}

    # Returns a text containing all upcoming, unplayed fixtures including team emotes
    def getMatchesText(self):

        # Gets list of upcoming matches sorted to match toornament ordering
        self.matches = sorted(self.matches, key = lambda match: match.number)
        
        # Adds all match string of pending games to the string
        msg = ''
        for match in self.matches:
            if match.pending:
                msg += match.toString() + '\n'

        return msg


# Stores information on a specific match
class Match:

    def __init__(self, number = 0, homeTeamName = '', awayTeamName = '', homeTeamEmote = '', awayTeamEmote = '', homeScore = -1, awayScore = -1, pending = True):
        self.number = number
        self.homeTeamName = homeTeamName
        self.awayTeamName = awayTeamName
        self.homeTeamEmote = homeTeamEmote
        self.awayTeamEmote = awayTeamEmote
        self.homeScore = homeScore,
        self.awayScore = awayScore,
        self.pending = pending

    # Converts match information to a string containing the team names and emotes
    def toString(self):
        return self.homeTeamName + ' ' + self.homeTeamEmote + ' vs ' + self.awayTeamEmote + ' ' + self.awayTeamName
    
    # Writes match details to CSV for serialization
    def toCSV(self):
        return f'{self.number};{self.homeTeamName};{self.homeScore};{self.awayTeamName};{self.awayScore};{self.pending}'

    def fromCSV(self, csvLine):
        columns = re.split(';', csvLine)
        self.number = int(columns[0])
        self.homeTeamName = columns[1]
        self.homeTeamScore = int(columns[2])
        self.awayTeamName = columns[3]
        self.awayTeamScore = int(columns[4])
        self.pending = bool(columns[5])

        
# Complete standings of all teams in a stage
class Ranking:

    def __init__(self, stage):
        self.stage = stage
        self.week = 1
        self.teams = []

    # Returns how many characters wide the rank column of the standings table must be
    def getRankPadding(self) -> int:
        maxRank = 1
        for team in self.teams:
            if team.rank > maxRank:
                maxRank = team.rank
        
        return len(str(maxRank))
    
    # Returns how many characters wide the name column of the standings table must be
    def getNamePadding(self):
        maxNameLength = len('Team')
        for team in self.teams:
            if len(team.name) > maxNameLength:
                maxNameLength = len(team.name)
        
        return maxNameLength
    
    # Returns how many characters wide the win/loss column of the standings table must be
    def getWinLossPadding(self):
        maxWLLength = len('0-0')

        for team in self.teams:
            length = len(str(team.wins) + '-' + str(team.losses))
            if length > maxWLLength:
                maxWLLength = length

        return maxWLLength 

    # Generates the standings table out of text and returns it
    def getRankingText(self):

        rankPadding = self.getRankPadding()
        namePadding = self.getNamePadding()
        wlPadding = self.getWinLossPadding()

        # Generates table header
        rankHeader = '#'
        if len(rankHeader) < rankPadding:
            rankHeader += ' ' * (rankPadding - len(rankHeader))
        
        teamHeader = 'Team'
        if len(teamHeader) < namePadding:
            teamHeader += ' ' * (namePadding - len(teamHeader))

        wlHeader = 'W-L'
        if len(wlHeader) < wlPadding:
            wlHeader += ' ' * (wlPadding - len(wlHeader))
        
        diffHeader = '+/-'
        tableHeader = rankHeader + ' | ' + teamHeader + ' | ' + wlHeader + ' | ' + diffHeader

        # Generates separator between header and table content
        headerSeparator = '-'*(len(rankHeader)+1) + '+' + '-'*(len(teamHeader)+2) + '+' + '-'*(len(wlHeader)+2) + '+' + '-'*(len(diffHeader)+2)

        msg = tableHeader + '\n' + headerSeparator + '\n'

        # Generates standing information line for every team and adds it to the content
        for team in self.teams:

            rankStr = str(team.rank)
            if len(rankStr) < rankPadding:
                rankStr += ' ' * (rankPadding - len(rankStr))

            nameStr = team.name
            if len(nameStr) < namePadding:
                nameStr += ' ' * (namePadding - len(nameStr))

            wlStr = str(team.wins) + '-' + str(team.losses + team.forfeits)
            if len(wlStr) < wlPadding:
                wlStr += ' ' * (wlPadding - len(wlStr))

            diffStr = str(team.gameDifference)
            if team.gameDifference > 0:
                diffStr = '+' + diffStr

            msg += rankStr + ' | ' + nameStr + ' | ' + wlStr + ' | ' + diffStr + '\n'
        
        return msg


# Ranking information for a single team
class Team:

    def __init__(self):
        self.name = ''
        self.emote = ''
        self.position = -1
        self.rank = -1
        self.points = 0
        self.wins = 0
        self.losses = 0
        self.played = 0
        self.forfeits = 0
        self.gamesWon = 0
        self.gamesLost = 0
        self.gameDifference = 0

    def toCSV(self):
        return f'{self.name};{self.position};{self.rank};{self.points};{self.wins};{self.losses};{self.played};{self.forfeits};{self.gamesWon};{self.gamesLost};{self.gameDifference}'

    def fromCSV(self, csvLine):
        columns = re.split(';', csvLine)
        self.name = columns[0]
        self.position = int(columns[1])
        self.rank = int(columns[2])
        self.points = int(columns[3])
        self.wins = int(columns[4])
        self.losses = int(columns[5])
        self.played = int(columns[6])
        self.forfeits = int(columns[7])
        self.gamesWon = int(columns[8])
        self.gamesLost = int(columns[9])
        self.gameDifference = int(columns[10])

# Information on a certain stage
class Stage:

    def __init__(self, name = '', id = '', groupID = '', logoURL = '', colour = 'FFFFFF', alias = ''):
        self.name = name
        self.id = id
        self.groupID = groupID
        self.logoURL = logoURL
        self.alias = alias

        # Converts colour hex string to RGB values
        self.colourStr = colour
        r = int(colour[:2], 16)
        g = int(colour[2:4], 16)
        b = int(colour[4:], 16)
        self.colour = Colour.from_rgb(r, g, b)

    # Returns stage information as valid CSV-line
    def toCSV(self):
        return f'{self.name};{self.id};{self.groupID};{self.logoURL};{self.colourStr};{self.alias}'


# Information on a certain team
class TeamInfo:

    def __init__(self, name = '', emote = '', nickname = ''):
        self.name = name
        self.emote = emote
        self.nickname = nickname

    # Returns team information as valid CSV-line
    def toCSV(self):
        return f'{self.name};{self.emote};{self.nickname}'
