import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import json

# Load environment variables from .env file
load_dotenv()

# Get the Discord token from environment variables
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

@bot.command(name='ping')
async def ping(ctx):
    """Responds with Pong! to check if the bot is responsive."""
    await ctx.send('Pong!')


####################################################################################################
# Add more commands here

@bot.command()
async def setup(ctx : commands.Context):
    guild_id = ctx.guild.id

    directory_path = "database"
    file_name = f"{guild_id}.json"
    file_path = os.path.join(directory_path, file_name)

    guild_file = os.path.exists(file_path)

    if guild_file == False:
        open(file_path, "w")
        data={
            'id' : guild_id,
            'tickets_category_id' : None,
            'staff_rold_id' : None,
            "transcript_channel_id": None,
            "log_channel_id": None,
            "welcome_message": None,
            "ticket_counter": 0         
        }
        with open(file_path , "w") as f:
            json.dump(data, f, indent=4)
        
        await ctx.send("Created config file for your guild. Run the command")

    
    elif guild_file == True:
        await ctx.send("Lets start the ticket setup process")
        await ctx.send("Please enter the name for the ticket category")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        category_name = await bot.wait_for('message', check=check, timeout=60.0)
        category_content = category_name.content

        await ctx.guild.create_category(category_name.content)

        category = discord.utils.get(ctx.guild.categories, name=category_content)  

        with open(file_path, "r") as f:
            data = json.load(f)

        data["tickets_category_id"] = category.id

        await ctx.send(f"Created category : {category_content}")
        await ctx.send("Please @mention the staff role that should have access to tickets")
            
        s_role_id = await bot.wait_for('message', check=check, timeout=60.0)
        role_content = s_role_id.content
        staff_role = s_role_id.role_mentions[0]

        data["staff_rold_id"] = staff_role.id




        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)




####################################################################################################

# Run the bot
if __name__ == '__main__':
    if not TOKEN:
        raise ValueError("No Discord token found in .env file")
    bot.run(TOKEN)