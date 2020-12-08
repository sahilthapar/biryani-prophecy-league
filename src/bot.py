from discord.ext import commands
from util import get_discord_token
from fpl import get_events, get_teams

bot = commands.Bot(command_prefix='$')
bot.teams = {}


@bot.event
async def on_ready():
    bot.teams = get_teams()

    print('Bot is ready')
# @bot.command()
# async def help(ctx):
#     await ctx.send('Hello and welcome to the Biryani Prophecy League!')
#     await ctx.send('What would you like help with today?')


@bot.command(aliases=['sf', 'fixtures'])
async def show_fixtures(ctx, *, gw: int):
    events = get_events(gameweek=str(gw), teams=bot.teams)
    response = '\n'.join([x.get_short_name() for x in events])
    await ctx.send(response)


# @bot.command('add_fixtures', 'af')
# async def add_fixtures(ctz, *, gw: int):
#     events = get_events(gameweek=gw, teams=bot.teams)
#     put_fixtures = [[x.team_h.short_name, x.team_a.short_name] for x in events]
#     for name, sheet in all_sheets:
#         print(name, sheet.spreadsheet_id)
#         sheet.put_data('Fixtures', '!A{}:B{}'.format(start, end), put_fixtures)


@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"{amount} message(s) got deleted")



token = get_discord_token()
bot.run(token)
