import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import json
import asyncio

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv('TOKEN')

# Set up intents
intents = discord.Intents.default()
intents.message_content = True

# Create bot instance with command prefix
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} guilds')

#Test command if the bot is working or not 
@bot.command(name='ping')
async def ping(ctx):
    """Responds with Pong! to check if the bot is responsive."""
    await ctx.send('Pong!')

#vvvFEATURES AND COMMANDS START FROM HERE vvv


#!setup command which 
@bot.command()
async def setup(ctx : commands.Context):
    guild_id = ctx.guild.id

    directory_path = "database"
    file_name = f"{guild_id}.json"
    file_path = os.path.join(directory_path, file_name)

    guild_file = os.path.exists(file_path)
    timeout_msg = "You took too long to respond"

    if guild_file == False:
        open(file_path, "w")
        data={
            "guild_name" : ctx.guild.name,
            'guild_id' : guild_id,
            'tickets_category_id' : None,
            'staff_rold_id' : None,
            "transcript_channel_id": None,
            "log_channel_id": None,
            "welcome_message": None,
            "ticket_counter": 0         
        }#Basic stucture for our database
        with open(file_path , "w") as f:
            json.dump(data, f, indent=4)
        
        await ctx.send("Created config file for your guild. Run the command")
    
    await ctx.send("Lets start the ticket setup process")
    await ctx.send("Please enter the name for the ticket category")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    try:
        category_name = await bot.wait_for('message', check=check, timeout=60.0)
    except asyncio.TimeoutError:
        ctx.send(timeout_msg)
        return
    
    category_content = category_name.content

    await ctx.guild.create_category(category_content)

    category = discord.utils.get(ctx.guild.categories, name=category_content)  

    with open(file_path, "r") as f:
        data = json.load(f)

    data["tickets_category_id"] = category.id

    await ctx.send(f"Created category : {category_content}")
    await ctx.send("Please @mention the staff role that should have access to tickets")
            
    try:
        s_role_id = await bot.wait_for('message', check=check, timeout=60.0)
    except asyncio.TimeoutError:
        await ctx.send(timeout_msg)
        return

    staff_role = s_role_id.role_mentions[0]#role name

    data["staff_rold_id"] = staff_role.id#Error if a user mentions a @user not a @role Need to fix it

    await ctx.send(f"Set Staff role to : {staff_role}")
    await ctx.send("What channel should be the transcript channel")

    try:
        ts_channel_name = await bot.wait_for('message', check=check, timeout=60.0)
    except asyncio.TimeoutError:
        await ctx.send(timeout_msg)
        return
    
    transcript_channel = ts_channel_name.channel_mentions[0]
    channel_id = transcript_channel.id

    data["transcript_channel_id"] = channel_id

    await ctx.send(f"Set Tanscript Channel to : {transcript_channel.name}")
    await ctx.send("Please mention the channel we should send ticket logs to?")

    try:
        log_channel_name = await bot.wait_for('message', check=check, timeout=60.0)
    except asyncio.TimeoutError:
        await ctx.send(timeout_msg)
        return
    
    log_channel = log_channel_name.channel_mentions[0]

    data["log_channel_id"] = log_channel.id

    await ctx.send(f"We have set the log channel to {log_channel.name}")
    await ctx.send("Please type out the welcome message we should send when a user creates a ticket")

    try:
        wc_msg = await bot.wait_for('message', check=check, timeout=60.0)
    except asyncio.TimeoutError:
        await ctx.send(timeout_msg)
        return
    
    data["welcome_message"] = wc_msg.content

    await ctx.send("You have configured the server :D")


    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)






# RUNNING THE BOT 
if __name__ == '__main__':
    if not TOKEN:
        raise ValueError("No Discord token found in .env file")
    bot.run(TOKEN)