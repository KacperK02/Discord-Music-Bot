import random
import discord
import os
import nextcord
import wavelink
import datetime
from nextcord.ext import commands

bot = commands.Bot(command_prefix='$', intents=discord.Intents.all())

channels = []
channels_path = os.path.join("files", "channels.txt")
file = open(channels_path, "r")
for channel in file:
    channels.append(channel.split())
file.close()


async def random_champion_for_role(ctx, name_of_file, text):
    champions = []
    path = os.path.join("files", name_of_file)
    f = open(path, "r")
    for line in f:
        champions.append(line)
    f.close()
    await ctx.send(text + " " + random.choice(champions))


@bot.event
async def on_message(message):
    for i in range(len(channels)):
        if message.channel.name in channels[i]:
            if len(message.attachments) > 0:
                await message.add_reaction('\N{THUMBS UP SIGN}')
    await bot.process_commands(message)


@bot.event
async def on_ready():
    print("Bot is ready")
    bot.loop.create_task(node_connect())


@bot.event
async def on_wavelink_node_ready(node: wavelink.Node):
    print(f'Node {node.identifier} is ready')


async def node_connect():
    await bot.wait_until_ready()
    await wavelink.NodePool.create_node(bot=bot, host='lavalinkinc.ml', port=443, password='incognito', https=True)


@bot.event
async def on_wavelink_track_end(player: wavelink.Player, track: wavelink.Track, reason):
    ctx = player.ctx
    vc: player = ctx.voice_client
    if vc.loop:
        return await vc.play(track)

    next_song = vc.queue.get()
    await vc.play(next_song)
    em = nextcord.Embed(title=f"Now playing: {next_song.title}", description="")
    await ctx.send(embed=em)


@bot.command()
async def play(ctx, *, songs):
    if ctx.author.voice is None:
        return await ctx.send("Firstly, you must join to the voice channel, ok?")
    if not ctx.voice_client:
        vc: wavelink.Player = await ctx.author.voice.channel.connect(cls=wavelink.Player)
    else:
        vc: wavelink.Player = ctx.voice_client

    songs_list = []
    previous = 0
    for i in range(len(songs)):
        if songs[i] == ';':
            songs_list.append(songs[previous:i].lstrip())
            previous = i + 1
    songs_list.append(songs[previous:len(songs)].lstrip())
    
    for i in range(len(songs_list)):
        if songs_list[i] != '':
            search = await wavelink.YouTubeTrack.search(query=songs_list[i])
            if vc.queue.is_empty and not vc.is_playing():
                em = nextcord.Embed(title=f"{search[0].title}", description=f"Added to queue")
                await ctx.send(embed=em)
            if vc.queue.is_empty and not vc.is_playing():
                await vc.play(search[0])
                em = nextcord.Embed(title=f"Now playing: {search[0].title}", description="")
                await ctx.send(embed=em)
            else:
                await vc.queue.put_wait(search[0])
                em = nextcord.Embed(title=f"{search[0].title}", description=f"Added to queue")
                await ctx.send(embed=em)
            vc.ctx = ctx
            setattr(vc, "loop", False)


@bot.command()
async def pause(ctx):
    if ctx.author.voice is None:
        return await ctx.send("Firstly, you must join to the voice channel, ok?")
    if not ctx.voice_client:
        return await ctx.send("Nothing is currently playing")
    else:
        vc: wavelink.Player = ctx.voice_client
    await vc.pause()
    await ctx.send("Music has been paused")


@bot.command()
async def resume(ctx):
    if ctx.author.voice is None:
        return await ctx.send("Firstly, you must join to the voice channel, ok?")
    if not ctx.voice_client:
        return await ctx.send("Nothing is currently playing")
    else:
        vc: wavelink.Player = ctx.voice_client
    await vc.resume()
    await ctx.send("Let's play")


@bot.command()
async def skip(ctx):
    if ctx.author.voice is None:
        return await ctx.send("Firstly, you must join to the voice channel, ok?")
    if not ctx.voice_client:
        return await ctx.send("Nothing is currently playing")
    else:
        vc: wavelink.Player = ctx.voice_client

    if vc.is_paused():
        pass
    elif not vc.is_playing():
        return

    await vc.stop()
    await ctx.send("Ok, let's move on to the next track")


@bot.command()
async def stop(ctx):
    if ctx.author.voice is None:
        return await ctx.send("Firstly, you must join to the voice channel, ok?")
    if not ctx.voice_client:
        return await ctx.send("Nothing is currently playing")
    else:
        vc: wavelink.Player = ctx.voice_client
    await vc.disconnect()
    await ctx.send("Bye")


@bot.command()
async def queue(ctx):
    if not ctx.voice_client:
        return await ctx.send("Nothing is currently playing")
    else:
        vc: wavelink.Player = ctx.voice_client

    if vc.queue.is_empty:
        return await ctx.send("Queue is empty")

    em = nextcord.Embed(title="Queue")
    queue = vc.queue.copy()
    song_count = 0
    em.add_field(name="Now playing: ", value=vc.track.title + ' (' + str(datetime.timedelta(seconds=vc.track.length)) + ')')
    for song in queue:
        song_count += 1
        em.add_field(name=f'{song_count}. ', value=f'{song.title}')
    return await ctx.send(embed=em)


@bot.command()
async def remove(ctx, pos):
    if ctx.author.voice is None:
        return await ctx.send("Firstly, you must join to the voice channel, ok?")
    if not ctx.voice_client:
        return await ctx.send("Nothing is currently playing")
    else:
        vc: wavelink.Player = ctx.voice_client

    try:
        vc.queue.__delitem__(int(pos) - 1)
        return await ctx.send("Track has been removed from queue")
    except:
        return await ctx.send("There's no such number")


@bot.command()
async def nowplaying(ctx):
    if ctx.author.voice is None:
        return await ctx.send("Firstly, you must join to the voice channel, ok?")
    if not ctx.voice_client:
        return await ctx.send("Nothing is currently playing")
    else:
        vc: wavelink.Player = ctx.voice_client

    em = nextcord.Embed(title=f"Now playing: {vc.track.title}", description=f"Artist: {vc.track.author}")
    em.add_field(name="Duration:", value=str(datetime.timedelta(seconds=vc.track.length)))
    em.add_field(name="Link:", value=str(vc.track.uri))
    return await ctx.send(embed=em)


@bot.command()
async def question(ctx):
    answers = ["Yes, of course", "I have no doubt", "Probably yes", "It's hard to say",
               "It's uncertain", "Probably np", "Not completely", "Of course not"]
    await ctx.reply(random.choice(answers))


@bot.command()
async def randomnumber(ctx, number1, number2):
    random.seed()
    await ctx.send(random.randint(int(number1), int(number2)))


@bot.command()
async def count(ctx, equation):
    await ctx.reply(eval(equation))


@bot.command()
async def randomchampion(ctx):
    champions = []
    path = os.path.join("files", "allchampions.txt")
    f = open(path, "r")
    for line in f:
        champions.append(line)
    f.close()
    await ctx.send(random.choice(champions))


@bot.command()
async def randomtop(ctx):
    await random_champion_for_role(ctx, "top.txt", "Top:")


@bot.command()
async def randomjg(ctx):
    await random_champion_for_role(ctx, "jg.txt", "Jungle:")


@bot.command()
async def randommid(ctx):
    await random_champion_for_role(ctx, "mid.txt", "Mid:")


@bot.command()
async def randomadc(ctx):
    await random_champion_for_role(ctx, "adc.txt", "Adc:")


@bot.command()
async def randomsupp(ctx):
    await random_champion_for_role(ctx, "supp.txt", "Supp:")


@bot.command()
async def randomchampionfor(ctx, *, user):
    champions = []
    path = os.path.join("files", user + ".txt")
    if not os.path.isfile(path):
        await ctx.send("This file has not exist")
        return
    f = open(path, "r")
    for line in f:
        champions.append(line)
    f.close()
    await ctx.send(random.choice(champions))


@bot.command()
async def createchampionbase(ctx, *, name):
    path = os.path.join("files", name + ".txt")
    if os.path.isfile(path):
        await ctx.send("This file is exist")
        return
    f = open(path, "w")
    await ctx.send("File has been created")
    f.close()


@bot.command()
async def addchampion(ctx, file, *, name):
    path = os.path.join("files", file + ".txt")
    if not os.path.isfile(path):
        await ctx.send("This file is exist")
        return
    with open(path, "a") as f:
        f.write(name + '\n')
    f.close()
    await ctx.send("Added champion " + name + " to the " + file + "'s pool")


@bot.command()
async def champions(ctx, *, file):
    path = os.path.join("files", file + ".txt")
    if not os.path.isfile(path):
        await ctx.send("This file is exist")
        return
    f = open(path, "r")
    for line in f:
        await ctx.send(line)


@bot.command()
async def deletechampion(ctx, file, name):
    path = os.path.join("files", file + ".txt")
    if not os.path.isfile(path):
        await ctx.send("This file isn't exist")
        return
    f = open(path, "r")
    lines = f.readlines()
    f.close()
    f = open(path, "w")
    for line in lines:
        if line != name + "\n":
            f.write(line)
    await ctx.send("Champion has been removed")


@bot.command()
async def randomteam(ctx):
    await randomtop(ctx)
    await randomjg(ctx)
    await randommid(ctx)
    await randomadc(ctx)
    await randomsupp(ctx)


path = os.path.join("files", "token.txt")
f = open(path, "r")
token = f.readline()
f.close()

bot.run(token)
