import discord
from discord import Colour, Embed
from discord.ext import commands
import sys
import re
from toornament import Toornament
from toornament import Ranking
from toornament import Team
from toornament import Stage
from toornament import Week

# TODO:
# - Add help command
# - Add manual CSV support
# - Fix emotes not displaying correctly


# Initialized Toornament endpoint
toornament = Toornament('toornament.token', 'Teams.csv', 'Stages.csv', enableAPI = False)

# Reads Discord bot token from token file
try:
    discordTokenFile = open('Discord.token', 'r')
    discordToken = discordTokenFile.read()
    discordTokenFile.close()
except:
    print('Could not read Discord token file')
    sys.exit('Invalid Discord token file or data')

# Initializes Bot
bot = commands.Bot(command_prefix='!too ')


#### HELPER FUNCTIONS ####

# Function to generate embed for one stage group
def generateEmbed(week, stageName):
    stage = toornament.getStage(stageName)
    weekInfo = toornament.getWeekInfo(stage, int(week)+1)

    embed = Embed(
        title = stage.name,
        type = 'rich',
        url = toornament.getStageURL(stage),
        colour = stage.colour
    )

    embed.set_thumbnail(url = stage.logoURL)
    embed.set_footer(text = toornament.tournamentName, icon_url = 'https://i.imgur.com/u2HPdEi.png')

    standingsText = '```' + weekInfo.standings.getRankingText() + '```'  
    embed.add_field(name = f'Standings (Week {week})', value = standingsText, inline = False)

    matchesText = weekInfo.getMatchesText()
    embed.add_field(name = f'Upcoming fixtures (Week {int(week)+1})', value = matchesText, inline = False)

    return embed


#### COMMANDS ####

# Simple ping command to see if bot is running
@bot.command()
async def ping(ctx):
    await ctx.send('pong')

# Update command to post ranking and upcoming fixtures for one specific stage group in channel
@bot.command()
async def update(ctx, week, stageName):

    await ctx.send(embed = generateEmbed(week, stageName))
    await ctx.message.delete()

# Update command to post ranking and upcoming fixtures for all stage groups given
@bot.command()
async def updateall(ctx, week, stageNames):

    stageNameList = re.split(';', stageNames)
    for stageName in stageNameList:
        await ctx.send(embed = generateEmbed(week, stageName))
    await ctx.message.delete()

# Command to add a new team to the database
@bot.command()
async def addteam(ctx, teamName, emoteID, nickname = ''):
    if emoteID.startswith('\\'):
        emoteID = emoteID[1:]

    success = toornament.addTeam(teamName, emoteID, nickname)

    if success:
        await ctx.send(f'Added team {teamName}!')
    else:
        await ctx.send(f"Couldn't add team {teamName}.")

# Command to delete all entries of a team from the database
@bot.command()
async def removeteam(ctx, teamName):
    success = toornament.removeTeam(teamName)

    if success:
        await ctx.send(f'Deleted team {teamName}!')
    else:
        await ctx.send(f"Error deleting team {teamName}. Maybe it got deleted but the changes couldn't be saved.")

# Command to add a new tournament stage group to the database
@bot.command()
async def addstage(ctx, fullName, stageID, groupID, logoURL, colour, alias = ''):
    success = toornament.addStage(fullName, stageID, groupID, logoURL, colour, alias)

    if success:
        await ctx.send(f'Added stage {fullName}!')
    else:
        await ctx.send(f"Couldn't add stage {fullName}.")

# Command to delete all entries of a tournament group from the database
@bot.command()
async def removestage(ctx, stageName):
    success = toornament.removeStage(stageName)

    if success:
        await ctx.send(f'Deleted stage {stageName}!')
    else:
        await ctx.send(f"Error deleting stage {stageName}. Maybe it got deleted but the changes couldn't be saved.")

# Command to manually report standings for a stage
@bot.command()
async def table(ctx, stageName, tableStr):
    success = toornament.reportStandings(stageName, tableStr)
    
    if success:
        await ctx.send(f'Reported standings for {stageName}!')
    else:
        await ctx.send(f'Error reporting standings for {stageName}.')

# Command to manually report fixtures for a certain week and stage
@bot.command()
async def matches(ctx, weekNumber, stageName, matchesStr):
    success = toornament.reportFixtures(stageName, weekNumber, matchesStr)

    if success:
        await ctx.send(f'Reported fixtures for {stageName} (Week {weekNumber})!')
    else:
        await ctx.send(f'Error reporting fixtures for {stageName} (Week {weekNumber}).')

# Starts Discord bot
print('Starting bot...')
bot.run(discordToken)
