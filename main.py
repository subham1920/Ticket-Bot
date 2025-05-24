import os
import discord
from discord.ext import commands
from discord.ui import button, View
from dotenv import load_dotenv
import json
import asyncio
import datetime
import io

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
    bot.add_view(CloseTicketView())


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
        global create_ticket_user
        create_ticket_user = interaction.user
        
        try:
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
            
            staff_role_id = data["staff_rold_id"]
            staff_role = interaction.guild.get_role(staff_role_id)
            
            await ticket_channel.set_permissions(interaction.guild.default_role, view_channel=False)
            await ticket_channel.set_permissions(interaction.user, view_channel=True, send_messages=True)
            await ticket_channel.set_permissions(staff_role, view_channel=True, send_messages=True)
            
            welcome_msg = data["welcome_message"]
            ticket_embed = discord.Embed(
                title=f"Ticket no : {counter}",
                description=f"{interaction.user.mention} {welcome_msg}",
                color=discord.Colour.green()
            )

            await ticket_channel.send(embed=ticket_embed, view=CloseTicketView())
            await interaction.followup.send(f"Ticket created! {ticket_channel.mention}", ephemeral=True)

            # Save updated counter
            with open(file_path, "w") as f:
                json.dump(data, f, indent=4)
                
        except Exception as e:
            try:
                await interaction.followup.send(f"Error creating ticket: {str(e)}", ephemeral=True)
            except:
                try:
                    await interaction.response.send_message(f"Error creating ticket: {str(e)}", ephemeral=True)
                except:
                    print(f"Failed to respond to interaction: {str(e)}")

#Close button View
class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # Make the view persistent
    
    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        
        try:
            directory_path = "database"
            file_name = f"{interaction.guild.id}.json"
            file_path = os.path.join(directory_path, file_name)
            
            with open(file_path, "r") as f:
                data = json.load(f)
            
            transcript_channel_id = data["transcript_channel_id"]
            transcript_channel = interaction.guild.get_channel(transcript_channel_id)
            
            if not transcript_channel:
                await interaction.followup.send("Transcript channel not found! Deleting channel without transcript.", ephemeral=True)
                await asyncio.sleep(3)
                await interaction.channel.delete()
                return
            
            await interaction.followup.send("Creating transcript...", ephemeral=True)
            
            messages = []
            async for message in interaction.channel.history(limit=None, oldest_first=True):
                timestamp = message.created_at.strftime("%Y-%m-%d %H:%M:%S UTC")
                content = message.content or "[No text content]"
                
                attachments = ""
                if message.attachments:
                    attachments = " [Attachments: " + ", ".join([att.filename for att in message.attachments]) + "]"
                
                embeds_info = ""
                if message.embeds:
                    embeds_info = f" [Embeds: {len(message.embeds)} embed(s)]"
                
                messages.append(f"[{timestamp}] {message.author.display_name}: {content}{attachments}{embeds_info}")
            
            transcript_text = f"=== TICKET TRANSCRIPT ===\n"
            transcript_text += f"Channel: {interaction.channel.name}\n"
            transcript_text += f"Ticket created by {create_ticket_user} ({create_ticket_user.id})"
            transcript_text += f"Closed by: {interaction.user.display_name} ({interaction.user.id})\n"
            transcript_text += f"Closed at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
            transcript_text += f"Total messages: {len(messages)}\n"
            transcript_text += "=" * 50 + "\n\n"
            transcript_text += "\n".join(messages)
            
            transcript_file = discord.File(
                io.StringIO(transcript_text),
                filename=f"transcript-{interaction.channel.name}-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}.txt"
            )
            
            embed = discord.Embed(
                title=f"🎫 Ticket Transcript: {interaction.channel.name}",
                description=f"Ticket created by : {create_ticket_user.mention}",
                description=f"Closed by {interaction.user.mention}\nTotal messages: {len(messages)}",
                color=discord.Color.blue(),
                timestamp=datetime.datetime.now()
            )
            embed.add_field(name="Channel ID", value=interaction.channel.id, inline=True)
            embed.add_field(name="Guild", value=interaction.guild.name, inline=True)
            
            await transcript_channel.send(embed=embed, file=transcript_file)
            await asyncio.sleep(2)
            await interaction.channel.delete()
            
        except Exception as e:
            try:
                await interaction.followup.send(f"Error creating transcript: {str(e)}\nDeleting channel anyway...", ephemeral=True)
                await asyncio.sleep(3)
                await interaction.channel.delete()
            except:
                print(f"Failed to delete channel or send error message: {str(e)}")



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