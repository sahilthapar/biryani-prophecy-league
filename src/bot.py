from discord.ext import commands
from fpl import get_events, get_teams, get_sheets, get_discord_token, get_interval

bot = commands.Bot(command_prefix='$')
bot.teams = {}


@bot.event
async def on_ready():
    bot.sheets = get_sheets()
    bot.teams = get_teams()
    bot.start_gw = 12
    bot.base_padding = 0
    print('Bot is ready')
# @bot.command()
# async def help(ctx):
#     await ctx.send('Hello and welcome to the Biryani Prophecy League!')
#     await ctx.send('What would you like help with today?')


@bot.command(aliases=['sf'])
async def show_fixtures(ctx, *, gw: int):
    events = get_events(gameweek=str(gw), teams=bot.teams)
    response = '\n'.join([x.get_short_name() for x in events])
    await ctx.send(response)


@bot.command(aliases=['af'])
async def add_fixtures(ctx, *, gw: int):
    events = get_events(gameweek=str(gw), teams=bot.teams)
    start, end = get_interval(fixtures=events, gameweek=gw, start_gw=bot.start_gw, base_padding=bot.base_padding)
    put_fixtures = [[x.team_h.short_name, x.team_a.short_name] for x in events]
    for name, sheet in bot.sheets:
        print(name, sheet.spreadsheet_id)
        sheet.put_data('Fixtures', '!A{}:B{}'.format(start, end), put_fixtures)
    await ctx.send('Fixtures for Gameweek: ' + str(gw) + ' have been updated in the sheets')


@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"{amount} message(s) got deleted")



token = get_discord_token()
bot.run(token)
