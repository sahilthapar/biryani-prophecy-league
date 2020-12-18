import arrow
import logging
from discord import Status, Game
from discord.ext import commands
from fpl import get_events, bootstrap, calculate_live_scores, get_discord_token

bot = commands.Bot(command_prefix='$')
bot.teams = {}
logging.basicConfig(filename='../log/bot.log', level=logging.INFO, format='%(asctime)s %(message)s')


@bot.event
async def on_ready():
    bot.start_gw = 12
    bot.base_padding = 0
    bootstrap(bot)
    await bot.change_presence(status=Status.idle, activity=Game("Alfred"))
    logging.info('Bot is now online!')
    logging.info('Current Gameweek: %s', str(bot.gameweek_id))


@bot.command(aliases=['sf', 'show_fixtures'],
             brief="Display Fixtures",
             help="A command that displays this week's fixtures")
async def fixtures(ctx):
    logging.info('Command: fixture, User: %s', ctx.message.author.name)
    response = '\n'.join([x.get_short_name() for x in bot.fixtures])
    await ctx.send(response)


@bot.command(aliases=['af', 'add_fixtures'],
             brief='Add fixtures to Google Sheets',
             help='A command that adds all fixtures for this gameweek to all'
                  ' sheets - individual and main')
async def add(ctx):
    logging.info('Command: add, User: %s', ctx.message.author.name)
    put_fixtures = [[x.team_h.short_name, x.team_a.short_name] for x in bot.fixtures]
    for name, sheet in bot.sheets:
        print(name, sheet.spreadsheet_id)
        sheet.put_data('Fixtures', '!A{}:B{}'.format(bot.start, bot.end), put_fixtures)
    await ctx.send('Fixtures for Gameweek: ' + str(bot.gameweek_id) + ' have been updated in all sheets')


@bot.command(aliases=['up', 'update_predictions'],
             brief='Update predictions in main sheet',
             help='Update the predictions for the current gameweek in the main sheet')
@commands.has_permissions(administrator=True)
async def predict(ctx):
    logging.info('Command: predict, User: %s', ctx.message.author.name)
    for i, (name, sheet) in enumerate(bot.sheets[:-1]):
        player_predictions = sheet.get_data('Fixtures', '!C{}:C{}'.format(bot.start, bot.end))
        col = chr(ord('C') + (i if i <= 2 else i+1))
        bot.primary_sheet.put_data('Fixtures',
                                   '!{col}{start}:col{end}'.format(col=col, start=bot.start, end=bot.end),
                                   player_predictions)
    await ctx.send('Predictions for Gameweek: ' + str(bot.gameweek_id) + ' have been updated in the main sheet')


@predict.error
async def predict_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        msg = "You're an average joe {}, you don't have permissions to do this".format(ctx.message.author.mention)
        await ctx.send(msg)


@bot.command(aliases=['live_standings', 'ls'],
             brief="Show live standings",
             help="Calculate the scores and show live standings based on current scores")
async def live(ctx):
    logging.info('Command: live, User: %s', ctx.message.author.name)
    # Update results
    bot.fixtures = get_events(gameweek=bot.gameweek_id, teams=bot.teams)
    live_games = filter(lambda i: i.team_h_score is not None, bot.fixtures)
    live_scores = [
        '{f.team_h.short_name} {f.team_h_score} {f.team_a_score} {f.team_a.short_name}'.format(f=f) for f in live_games
    ]
    put_results = [[x.scoreline] for x in bot.fixtures]
    bot.primary_sheet.put_data('Fixtures', '!H{}:H{}'.format(bot.start, bot.end), put_results)
    await ctx.send('\n'.join(live_scores))
    # Calculate Live standings
    standings = calculate_live_scores(bot)
    put_standings = []
    msg = ', '.join(['Name', 'Points', 'Results', 'Scorelines', 'Away', 'Home\n'])
    for x in standings:
        p = [x.name, x.points, x.correct_results, x.correct_scorelines, x.correct_a_score, x.correct_h_score]
        put_standings.append(p)
        msg += ', '.join([str(i) for i in p])
        msg += '\n'
    bot.primary_sheet.put_data('Live Scores', '!A2:F6', put_standings)
    await ctx.send(msg)


@bot.command(aliases=['fs', 'final_standings'],
             brief="Update points table",
             help="A command that calculates the live scores and updates the points table")
@commands.has_permissions(administrator=True)
async def final(ctx):
    # Update results
    logging.info('Command: final, User: %s', ctx.message.author.name)
    bot.fixtures = get_events(gameweek=bot.gameweek_id, teams=bot.teams)
    # Calculate Live standings
    standings = calculate_live_scores(bot)
    put_standings = []
    msg = ', '.join(['Name', 'Points', 'Results', 'Scorelines', 'Away', 'Home\n'])
    for x in standings:
        p = [x.name, x.points, x.correct_results, x.correct_scorelines, x.correct_a_score, x.correct_h_score]
        put_standings.append(p)
        msg += ', '.join([str(i) for i in p])
        msg += '\n'
    bot.primary_sheet.put_data('POINTS TABLE', '!A2:F6', put_standings)
    await ctx.send(msg)


@final.error
async def final_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        msg = "You're an average joe {}, you don't have permissions to do this".format(ctx.message.author.mention)
        await ctx.send(msg)


@bot.command(brief="clear messages in this channel",
             help="A command that clears the messages in this channel")
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    logging.info('Command: clear, User: %s', ctx.message.author.name)
    await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"{amount} message(s) got deleted")


@bot.command(aliases=['dday'],
             brief="Show deadlines",
             help="A command that shows the various deadlines")
async def deadline(ctx):
    logging.info('Command: deadline, User: %s', ctx.message.author.name)
    deadline_utc = arrow.get(bot.gameweek['deadline_time'])
    msg = '''
        Gameweek {gw}
        Draft Waiver: {time_left_a}
            IST: {ist_a} 
            PST: {pst_a}
        Draft Team & BPL: {time_left_b}
            IST: {ist_b}
            PST: {pst_b}
    '''.format(gw=bot.gameweek_id,
               time_left_a=deadline_utc.shift(hours=-24).humanize(granularity=['day', 'hour', 'minute']),
               ist_a=deadline_utc.shift(hours=-24).to('Asia/Kolkata').format('ddd Do MMM hh:mm A'),
               pst_a=deadline_utc.shift(hours=-24).to('US/Pacific').format('ddd Do MMM hh:mm A'),
               time_left_b=deadline_utc.humanize(granularity=['day', 'hour', 'minute']),
               ist_b=deadline_utc.to('Asia/Kolkata').format('ddd Do MMM hh:mm A'),
               pst_b=deadline_utc.to('US/Pacific').format('ddd Do MMM hh:mm A')
               )
    await ctx.send(msg)

token = get_discord_token()
bot.run(token)
