import os
import discord
from discord.ext import commands
from discord.ui import button, View
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
    
    # Add all buttons to make it persistent view
    bot.add_view(TicketView())


#Test command if the bot is working or not 
@bot.command(name='ping')
async def ping(ctx):
    """Responds with Pong! to check if the bot is responsive."""
    await ctx.send('Pong!')

#vvvFEATURES AND COMMANDS START FROM HERE vvv


#!setup command which creates config file for the server and asks for all the variables 
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

    staff_role = s_role_id.role_mentions[0]

    data["staff_rold_id"] = staff_role.id#ERROR : if a user mentions a @user not a @role Need to fix it

    await ctx.send(f"Set Staff role to : {staff_role.mention}")
    await ctx.send("What channel should be the transcript channel")

    try:
        ts_channel_name = await bot.wait_for('message', check=check, timeout=60.0)
    except asyncio.TimeoutError:
        await ctx.send(timeout_msg)
        return
    
    transcript_channel = ts_channel_name.channel_mentions[0]
    channel_id = transcript_channel.id

    data["transcript_channel_id"] = channel_id

    await ctx.send(f"Set Tanscript Channel to : {transcript_channel.mention}")
    await ctx.send("Please mention the channel we should send ticket logs to?")

    try:
        log_channel_name = await bot.wait_for('message', check=check, timeout=60.0)
    except asyncio.TimeoutError:
        await ctx.send(timeout_msg)
        return
    
    log_channel = log_channel_name.channel_mentions[0]

    data["log_channel_id"] = log_channel.id

    await ctx.send(f"We have set the log channel to : {log_channel.mention}")
    await ctx.send("Please type out the welcome message we should send when a user creates a ticket")

    try:
        wc_msg = await bot.wait_for('message', check=check, timeout=60.0)
    except asyncio.TimeoutError:
        await ctx.send(timeout_msg)
        return
    
    data["welcome_message"] = wc_msg.content

    await ctx.send("You have configured the server :D")
    await ctx.send("Run !ticketpanel in the desired channel")


    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

class TicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # Make the view persistent
    @discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.green, custom_id="create_ticket")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Process ticket creation
        directory_path = "database"
        file_name = f"{interaction.guild.id}.json"
        file_path = os.path.join(directory_path, file_name)
        
        try:
            # Acknowledge the interaction immediately to prevent timeout
            await interaction.response.defer(ephemeral=True)
            
            with open(file_path, "r") as f:
                data = json.load(f)

            category_id = data["tickets_category_id"]
            counter = data["ticket_counter"]
            category = interaction.guild.get_channel(category_id)

            # Create the ticket channel
            ticket_channel = await interaction.guild.create_text_channel(f"ticket-{counter}", category=category)
            #ERROR : make a limit that a user can open 3 tickets at a time
            #ERROR : make that when creating a ticket need to check that the category exisits
            data["ticket_counter"] += 1
            
            # Set permissions
            staff_role_id = data["staff_rold_id"]
            staff_role = interaction.guild.get_role(staff_role_id)
            
            await ticket_channel.set_permissions(interaction.guild.default_role, view_channel=False)
            await ticket_channel.set_permissions(interaction.user, view_channel=True, send_messages=True)
            await ticket_channel.set_permissions(staff_role, view_channel=True, send_messages=True)
            
            # Send welcome message
            welcome_msg = data["welcome_message"]
            ticket_embed = discord.Embed(
                title=f"Ticket no : {counter}",
                description=f"{interaction.user.mention} {welcome_msg}",
                color=discord.Colour.green()
            )

            await ticket_channel.send(embed=ticket_embed, view=CloseTicketView())##### ADD close button here #####
            
            # Use followup instead of response since we already deferred
            await interaction.followup.send(f"Ticket created! {ticket_channel.mention}", ephemeral=True)

            # Save updated counter
            with open(file_path, "w") as f:
                json.dump(data, f, indent=4)
                
        except Exception as e:
            # Use try/except in case the initial response failed
            try:
                await interaction.followup.send(f"Error creating ticket: {str(e)}", ephemeral=True)
            except:
                try:
                    await interaction.response.send_message(f"Error creating ticket: {str(e)}", ephemeral=True)
                except:
                    print(f"Failed to respond to interaction: {str(e)}")

#CLose button View
class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # Make the view persistent
    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.channel.send("Deleteing the channel in about 5 secs...")
        await interaction.channel.delete()



#!ticket panel command which sends the ticketpanel embed msg from which users can create a ticket
@bot.command()
async def ticketpanel(ctx : commands.Context):
    directory_path = "database"
    file_name = f"{ctx.guild.id}.json"
    file_path = os.path.join(directory_path, file_name)

    guild_file = os.path.exists(file_path)

    if not guild_file:
        await ctx.send("Run the command !setup before sending the ticketpanel")
        return
    
    try:
        with open(file_path, "r") as f:
            data = json.load(f)
    except Exception as e:
        await ctx.send(f"Error loading configuration: {str(e)}")
        return
    
    create_ticket_embed = discord.Embed(
        title="Create ticket!",
        description="If you have any problem, sort it out by creating a ticket",
        color=discord.Colour.green()
    )

    # Send embed with the persistent view
    await ctx.channel.send(embed=create_ticket_embed, view=TicketView())
        





# RUNNING THE BOT 
if __name__ == '__main__':
    if not TOKEN:
        raise ValueError("No Discord token found in .env file")
    bot.run(TOKEN)