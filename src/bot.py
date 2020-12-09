from discord.ext import commands
from fpl import get_events, get_teams, get_sheets, get_discord_token, get_interval

bot = commands.Bot(command_prefix='$')
bot.teams = {}


@bot.event
async def on_ready():
    bot.sheets = get_sheets()
    bot.primary_sheet = bot.sheets[-1][-1]
    bot.teams = get_teams()
    bot.start_gw = 12
    bot.base_padding = 0
    print('Bot is ready')


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


@bot.command(aliases=['up'])
@commands.has_permissions(administrator=True)
async def update_predictions(ctx, *, gw: int):
    events = get_events(gameweek=str(gw), teams=bot.teams)
    start, end = get_interval(fixtures=events, gameweek=gw, start_gw=bot.start_gw, base_padding=bot.base_padding)
    for i, (name, sheet) in enumerate(bot.sheets):
        player_predictions = sheet.get_data('Fixtures', '!C{}:C{}'.format(start, end))
        col = chr(ord('C') + (i if i <= 2 else i+1))
        bot.primary_sheet.put_data('Fixtures',
                                   '!{col}{start}:col{end}'.format(col=col, start=start, end=end),
                                   player_predictions)


@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"{amount} message(s) got deleted")

token = get_discord_token()
bot.run(token)
