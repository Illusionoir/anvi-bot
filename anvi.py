import discord
import random
import requests
import json
import os
import io
import aiohttp
from discord.ext import commands 
from discord import app_commands
from PIL import Image, ImageDraw, ImageFont, ImageSequence
from io import BytesIO
from difflib import get_close_matches
from datetime import datetime, timedelta, timezone
from discord.ui import View, Select, select  # For dropdowns
from discord import Interaction, Embed  # For type hints and responses
from flask import Flask
from threading import Thread

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.presences = True
intents.members = True
intents.typing = True
intents.guilds = True
intents.reactions = True
client = commands.Bot(command_prefix=",", intents=intents)




app = Flask(__name__)

@app.route("/")
def home():
    return "Anvi is alive!"

def run_web():
    app.run(host="0.0.0.0", port=8080)

Thread(target=run_web).start()

BOT_OWNER_ID = 1082009804874199150 
#===================================== BOT READY INFO =====================================

# Event handler for when the bot is ready
@client.event
async def on_ready():
    await client.tree.sync()
    print(f'[+] Logged in as {client.user} (ID: {client.user.id})')
    print(f"Registered commands: {[cmd.name for cmd in await client.tree.fetch_commands()]}")
    print("[+] Slash commands synced.")
    print('------')


#==================================== Data Helper =====================================


# Load data
def load_data(file_name):
    if not os.path.exists(file_name):
        return {}
    with open(file_name, "r") as f:
        return json.load(f)

# Save data
def save_data(file_name, data):
    with open(file_name, "w") as f:
        json.dump(data, f, indent=4)

#===================================== ERROR INFO =====================================


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        command = ctx.message.content.split()[0][1:]
        commands_list = [(cmd.name, cmd.help) for cmd in client.commands]
        similar_commands = get_close_matches(command, [cmd[0] for cmd in commands_list])

        if similar_commands:
            suggestion = similar_commands[0]
            suggestion_help = next((cmd[1] for cmd in commands_list if cmd[0] == suggestion), None)
            if suggestion_help:
                await ctx.send(f"Oops! Command `{command}` does not exist. Did you mean `{suggestion}`? Here's a brief description: {suggestion_help}")
            else:
                await ctx.send(f"Oops! Command `{command}` does not exist. Did you mean `{suggestion}`?")
        else:
            await ctx.send(f"Error 404: Oops! Command `{command}` does not exist.")

    elif isinstance(error, commands.BadArgument):
        await ctx.send("Invalid argument provided. Please check your input and try again.")

    elif isinstance(error, commands.MissingRequiredArgument):
        command_name = ctx.message.content.split()[0][1:]
        command = next((cmd for cmd in client.commands if cmd.name == command_name), None)
        if command:
            await ctx.send(f"Missing required argument. Usage: `{command_name} {command.signature}`")
        else:
            await ctx.send("Missing required argument.")



@client.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    try:
        await interaction.response.send_message(f"❌ Slash command error: {error}", ephemeral=True)
    except discord.InteractionResponded:
        await interaction.followup.send(f"❌ Slash command error: {error}", ephemeral=True)    




#===================================== INFO =====================================


@client.hybrid_command(name="info", description="Show the bot's  info")
async def info(ctx):
    guild = ctx.guild
    bot_invite_time = client.user.created_at.strftime('%Y-%m-%d %H:%M:%S')
    bot_additional_roles = ', '.join([
        role.mention for role in guild.me.roles
        if role != guild.default_role
    ])
    embed = discord.Embed(title=f"✨ {client.user.name}'s Info",
                          color=discord.Color.magenta())
    embed.set_thumbnail(url=client.user.display_avatar.url)
    embed.add_field(name="🌸 Nickname in Server",
                    value=f'`{guild.me.display_name}`',
                    inline=False)
    embed.add_field(name="🔸 Prefix", value=f'`,`', inline=False)
    embed.add_field(name="🎨 Creator", value="`Illusion`", inline=True)
    embed.add_field(name="🦋 Co-creator", value="`ChatGPT`", inline=True)
    embed.add_field(name="🕒 Bot Invite Time",
                    value=f'`{bot_invite_time}`',
                    inline=False)
    embed.add_field(name="⚡ Ping",
                    value=f"`{round(client.latency * 1000)}ms`",
                    inline=False)
    embed.add_field(name="🎗️ Additional Roles",
                    value=bot_additional_roles or "None",
                    inline=False)
    embed.set_image(url="https://media.tenor.com/kSEgsqdEAa8AAAAj/ui-shigure-shigure-ui.gif")
    embed.set_footer(text="Made with 💟")

    await ctx.reply(embed=embed)
info.category = "Utility"

#=========================== PING ============================


@client.hybrid_command(name="ping", description="Show bot latency")
async def ping(ctx):
    latency = round(client.latency * 1000)
    await ctx.send(f"🏓 Pong! Latency is `{latency}ms`.")
ping.category = "Utility"

#=========================== Help ============================

class HelpDropdown(discord.ui.Select):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        options = [
            discord.SelectOption(label="Moderation", description="Commands for managing the server"),
            discord.SelectOption(label="Economy", description="Currency and games commands"),
            discord.SelectOption(label="Fun", description="Fun image and interaction commands"),
            discord.SelectOption(label="Utility", description="some basic utility commands"),
        ]
        super().__init__(placeholder="Choose a command category...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0].lower()
        embed = discord.Embed(
            title=f"{category.title()} Commands",
            description=f"Here are the available **{category.title()}** commands:",
            color=discord.Color.random()
        )

        for cmd in self.bot.commands:
            if not isinstance(cmd, commands.Command):
                continue

            cmd_category = getattr(cmd, "category", None)
            if cmd_category and cmd_category.lower() == category:
                aliases = ", ".join(cmd.aliases) if hasattr(cmd, "aliases") else "None"
                embed.add_field(
                    name=f"`/{cmd.name}`",
                    value=f"**Description:** {cmd.description or 'No description'}\n"
                          f"**Aliases:** {aliases}",
                    inline=False
                )

        await interaction.response.edit_message(embed=embed, view=self.view)


class HelpView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=60)
        self.add_item(HelpDropdown(bot))


client.remove_command("help")

@client.hybrid_command(name="help", description="Show the help menu with all commands.")
async def help_command(ctx):
    embed = discord.Embed(
        title="📬 Help Menu",
        description="Choose a category below to see related commands.",
        color=discord.Color.blurple()
    )
    embed.set_footer(text="Use /command_name for help on specific commands.")

    view = HelpView(client)

    try:
        await ctx.author.send(embed=embed, view=view)
        if ctx.guild:
            await ctx.reply("📬 I've sent you a DM with all my commands!", ephemeral=True)
    except discord.Forbidden:
        await ctx.reply("❌ I couldn't send you a DM. Here's the help menu instead:", embed=embed, view=view)

help_command.category = "Utility"




#===================================== LEVELING SYSTEM =====================================


LEVELS_FILE = "level.json"

# XP required to level up formula
def get_level_xp_required(level):
    return 100 + (level - 1) * 50


# Add XP and handle level-up
async def add_xp(user_id, xp_to_add, channel):
    data = load_data(LEVELS_FILE)
    str_uid = str(user_id)

    if str_uid not in data:
        data[str_uid] = {"xp": 0, "level": 1}

    user_data = data[str_uid]
    user_data["xp"] += xp_to_add

    xp_needed = get_level_xp_required(user_data["level"])
    leveled_up = False

    while user_data["xp"] >= xp_needed:
        user_data["xp"] -= xp_needed
        user_data["level"] += 1
        xp_needed = get_level_xp_required(user_data["level"])
        leveled_up = True

    save_data(LEVELS_FILE, data)

    if leveled_up:
        await channel.send(f"🎉 <@{user_id}> just leveled up to **Level {user_data['level']}**!")

# Triggered after any prefix command
@client.listen()
async def on_command_completion(ctx):
    await add_xp(ctx.author.id, xp_to_add=10, channel=ctx.channel)

# Triggered after any slash command
@client.listen()
async def on_app_command_completion(interaction):
    await add_xp(interaction.user.id, xp_to_add=10, channel=interaction.channel)





# ==== CONFIG ====
FONT_PATH = "dejavu-sans.book.ttf"
BACKGROUND_FOLDER = "/home/container/background"
BADGES_FILE = "badges.json"
BADGES_FOLDER = "/home/container/badges"


# ==== BADGE LOGIC ====
def get_user_badges(user_id, level, balance, leaderboard, all_data):
    user_id = str(user_id)
    badges = set()

    # Load permanent badge and bank data
    badge_data = load_data(BADGES_FILE)
    bank_data = load_data("bank.json")

    # Add permanent badges (like OG, Tester, Dev)
    badges.update(badge_data.get(user_id, []))

    # Dynamic badge: Veteran
    if level >= 100:
        badges.add("veteran")

    if level <= 10:
        badges.add("newbie")

    # Dynamic badge: Millionaire (based on bank balance)
    balance = bank_data.get(user_id, {}).get("balance", 0)
    if balance >= 1_000_000:
        badges.add("millionaire")

    # Dynamic badge: Top 10 leaderboard
    if user_id in leaderboard[:10]:
        badges.add("top10")

    return list(badges)


# ==== /level COMMAND ====
@client.hybrid_command(name="level", description="Show your rank card.", aliases=['lvl'])
async def level(ctx, member: discord.Member = None):
    member = member or ctx.author
    levels = load_data(LEVELS_FILE)
    str_uid = str(member.id)

    if str_uid not in levels:
        await ctx.send(f"{member.mention} has no XP yet.")
        return

    user_data = levels[str_uid]
    level_num = user_data["level"]
    xp = user_data["xp"]
    xp_needed = get_level_xp_required(level_num)

    balance = load_data("balance.json").get(str_uid, 0)
    sorted_levels = sorted(levels.items(), key=lambda x: (x[1]["level"], x[1]["xp"]), reverse=True)
    leaderboard = [uid for uid, _ in sorted_levels]

    try:
        file = await generate_rank_card(member, level_num, xp, xp_needed, balance, leaderboard, levels)
        await ctx.send(file=file)
    except Exception as e:
        await ctx.send(f"Error generating card: `{e}`")
level.category = "Utility"




# ==== RANK CARD GENERATOR ====
async def generate_rank_card(member, level, xp, xp_required, balance, leaderboard, all_data):
    try:
        avatar_url = member.display_avatar.replace(static_format="png").url

        # === Get Random Background from Folder ===
        background_files = [file for file in os.listdir(BACKGROUND_FOLDER) if file.lower().endswith((".png", ".jpg", ".jpeg"))]
        if not background_files:
            raise FileNotFoundError("No background images found in folder.")
        selected_background = os.path.join(BACKGROUND_FOLDER, random.choice(background_files))
        

        async with aiohttp.ClientSession() as session:
            async with session.get(avatar_url) as resp:
                avatar_bytes = await resp.read()

        avatar = Image.open(BytesIO(avatar_bytes)).convert("RGBA").resize((96, 96))
        mask = Image.new("L", avatar.size, 0)
        ImageDraw.Draw(mask).ellipse((0, 0, 96, 96), fill=255)
        avatar.putalpha(mask)

        # Create pink border
        border = Image.new("RGBA", (108, 108), (0, 0, 0, 0))
        draw_border = ImageDraw.Draw(border)
        draw_border.ellipse((0, 0, 108, 108), fill=(255, 182, 193, 255))
        border.paste(avatar, (6, 6), avatar)

        bg = Image.open(selected_background).convert("RGBA").resize((600, 220))
        dim_layer = Image.new("RGBA", bg.size, (0, 0, 0, 90))
        bg = Image.alpha_composite(bg, dim_layer)

        draw = ImageDraw.Draw(bg)
        font_large = ImageFont.truetype(FONT_PATH, 26)
        font_small = ImageFont.truetype(FONT_PATH, 18)
        font_tiny = ImageFont.truetype(FONT_PATH, 14)

        bg.paste(border, (20, 52), border)

        def draw_text_with_shadow(text, pos, font, main_color=(255, 255, 255), shadow_color=(0, 0, 0)):
            x, y = pos
            draw.text((x+2, y+2), text, font=font, fill=shadow_color)
            draw.text((x, y), text, font=font, fill=main_color)

        display_name = member.display_name
        username = f"@{member.name}"
        draw_text_with_shadow(display_name, (130, 40), font_large)
        draw_text_with_shadow(username, (130, 70), font_small, main_color=(200, 200, 200))
        draw_text_with_shadow(f"Level: {level}", (130, 100), font_small)

        def format_xp(n):
            if n >= 1_000_000:
                return f"{n/1_000_000:.1f}M"
            elif n >= 1_000:
                return f"{n/1_000:.1f}K"
            return str(n)

        draw_text_with_shadow(f"XP: {format_xp(xp)} / {format_xp(xp_required)}", (440, 100), font_small)

        bar_x, bar_y = 130, 130
        bar_w, bar_h = 420, 18
        filled = int((xp / xp_required) * bar_w)
        draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], radius=9, fill=(248, 200, 220, 255))
        draw.rounded_rectangle([bar_x, bar_y, bar_x + filled, bar_y + bar_h], radius=9, fill=(255, 105, 180, 255))

        str_uid = str(member.id)
        global_rank = leaderboard.index(str_uid) + 1 if str_uid in leaderboard else "??"
        draw_text_with_shadow(f"#{global_rank}", (bg.width - 70, 20), font_large, main_color=(255, 215, 0))

        # === Badges ===
        badges = get_user_badges(member.id, level, balance, leaderboard, all_data)  # Pass correct number of arguments
        badge_start_x = 130
        badge_y = 165
        badge_size = 32
        spacing = 8

        for idx, badge in enumerate(badges):
            badge_path = os.path.join(BADGES_FOLDER, f"{badge}.png")
            if os.path.exists(badge_path):
                try:
                    badge_img = Image.open(badge_path).convert("RGBA").resize((badge_size, badge_size))
                    x_pos = badge_start_x + idx * (badge_size + spacing)
                    bg.paste(badge_img, (x_pos, badge_y), badge_img)
                except Exception as e:
                    print(f"[ERROR] Failed to draw badge '{badge}': {e}")
            else:
                print(f"[WARN] Badge image not found: {badge_path}")

        buffer = BytesIO()
        bg.save(buffer, format="PNG")
        buffer.seek(0)
        return discord.File(fp=buffer, filename="rank_card.png")

    except Exception as e:
        print(f"[ERROR] Error generating rank card: {e}")
        return None




# ==== /givebadge COMMAND ====

# ==== /givebadge COMMAND ====
@client.hybrid_command(name="givebadge", description="Give a permanent badge to a user.", aliases=['gb'])
@app_commands.describe(member="User to give the badge to", badge="Badge name (e.g., og, tester, dev)")
async def givebadge(ctx, member: discord.Member, badge: str):
    
    
    if ctx.author.id != OWNER_ID:
        await ctx.send("❌ You are not authorized to use this command.", ephemeral=True)
        return

    badge = badge.lower()
    valid_badges = {"og", "tester", "dev", "veteran", "millionaire", "top10", "owner"}
    

    if badge not in valid_badges:
        await ctx.send(f"❌ Invalid badge: `{badge}`.\nValid badges: {', '.join(valid_badges)}")
        return

    try:
        data = load_data(BADGES_FILE)
    except Exception as e:
        await ctx.send("⚠️ Error loading badge data.")
        return

    user_id = str(member.id)

    if user_id not in data:
        data[user_id] = []
        
    if badge not in data[user_id]:
        data[user_id].append(badge)
        try:
            save_data(BADGES_FILE, data)
        except Exception as e:
            await ctx.send("⚠️ Error saving badge data.")
            return

        await ctx.send(f"✅ Gave `{badge}` badge to {member.mention}.")
    else:
        await ctx.send(f"⚠️ {member.mention} already has the `{badge}` badge.")

givebadge.category = "Utility"



BADGE_EMOJIS = {
    "veteran": "🎖️",
    "millionaire": "💰",
    "top10": "🏆",
    "og": "🔥",
    "tester": "🧪",
    "dev": "🛠️",
    "newbie": "🐥",
    "owner":"👑"
}

@client.hybrid_command(name="badgelist", description="Show your badge collection.", aliases=['bgl'])
@app_commands.describe(member="Whose badges to view (default: you)")
async def badgelist(ctx, member: discord.Member = None):
    member = member or ctx.author
    user_id = str(member.id)
    data = load_data(BADGES_FILE)
    user_badges = data.get(user_id, [])

    if not user_badges:
        embed = discord.Embed(
            title=f"🎖️ {member.name}'s Badges",
            description="This user has no badges yet.",
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        return

    badge_display = ""
    for badge in user_badges:
        emoji = BADGE_EMOJIS.get(badge, "🎖️")
        badge_display += f"{emoji} **{badge.title()}**\n"

    embed = discord.Embed(
        title=f"🎖️ {member.name}'s Badges",
        description=badge_display,
        color=discord.Color.green()
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    await ctx.send(embed=embed)

badgelist.category = "Utility"





#================================= Leaderboard =====================================



@client.hybrid_command(name="leaderboard", description="Show the global top 10 users by level.", aliases=['lb'])
async def leaderboard(ctx):
    data = load_data(LEVELS_FILE)
    if not data:
        await ctx.send("📉 No data yet!")
        return

    sorted_data = sorted(data.items(), key=lambda x: (x[1]["level"], x[1]["xp"]), reverse=True)
    embed = discord.Embed(title="🏆 Global Leaderboard", color=discord.Color.gold())

    for i, (user_id, stats) in enumerate(sorted_data[:10], start=1):
        user = await client.fetch_user(int(user_id))
        embed.add_field(
            name=f"{i}. {user.name}",
            value=f"Level: {stats['level']} | XP: {stats['xp']}",
            inline=False
        )

    await ctx.send(embed=embed)
leaderboard.category = "Utility"





#===================================== SERVER INFO =====================================


@client.hybrid_command(name="server", description="Show information about the current server",aliases=['sv'])
async def server(ctx):
    guild = ctx.guild
    created_date = guild.created_at.strftime('%d/%m/%y')
    thumbnail = guild.icon.url if guild.icon else None
    color = discord.Color(random.randint(0, 0xFFFFFF))
    text_channels = len(guild.text_channels)
    voice_channels = len(guild.voice_channels)
    categories = len(guild.categories)
    custom_image_path = "stats-main.png"

    with open(custom_image_path, "rb") as file:
        custom_image = discord.File(file, filename="stats.png")
        embed = discord.Embed(title="ℹ️ Server Information", color=color)
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        embed.add_field(name="🛸 Server Name", value=guild.name, inline=False)
        embed.add_field(name="🆔 Server ID", value=guild.id, inline=False)
        embed.add_field(name="👑 Owner", value=guild.owner, inline=False)
        embed.add_field(name="📅 Server Created", value=created_date, inline=False)
        embed.add_field(name="👥 Members", value=guild.member_count, inline=True)
        embed.add_field(name="🍀 Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="💬 Text Channels", value=text_channels, inline=True)
        embed.add_field(name="📚 Categories", value=categories, inline=True)
        embed.add_field(name="🔊 Voice Channels", value=voice_channels, inline=True)
        embed.set_image(url="attachment://stats.png")
        embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed, file=custom_image)
info.category = "Utility"

#============================Add Role=================================

@client.hybrid_command(name= "addrole", description="Add a role to a member! Usage: ,addrole @member role_name or ,ar @member role_name", aliases=['ar'])
async def addrole(ctx, member: discord.Member, *, role_arg):
    if ctx.author.guild_permissions.manage_roles:
        try:
            role_arg_lower = role_arg.lower()  # Convert role_arg to lowercase
            
            # Find the role by comparing lowercase names
            role = discord.utils.find(lambda r: r.name.lower() == role_arg_lower, ctx.guild.roles)
            if not role:
                # If role not found by name, try finding it by mention
                role = discord.utils.get(ctx.message.role_mentions)
                if not role:
                    await ctx.send(f"❌ Role '{role_arg}' not found.")
                    return

            await member.add_roles(role)
            await ctx.message.delete()

            # Random color for the embed
            color = random.randint(0, 0xFFFFFF)
            embed = discord.Embed(
                title="Role Added",
                description=f"✅ {ctx.author.mention} added the role **{role.name}** to {member.mention}.",
                color=color
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("❌ I don't have permission to add roles to that member.")
    else:
        await ctx.send("❌ You don't have permission to manage roles.")

addrole.category = "Moderation"

#===========================Role List================================= 

@client.hybrid_command(name="rolelist", description="Displays a list of all roles in the server",aliases=['rl'])
async def rolelist(ctx):
    roles = ctx.guild.roles
    role_names = [role.name for role in roles]

    # Creating an embed
    embed = discord.Embed(title="List of Roles", color=discord.Color.blue())

    # Adding role names to the embed's description
    embed.description = "\n".join(role_names)

    await ctx.send(embed=embed)
rolelist.category = "Utility"

#============================Role Info=================================       
@client.hybrid_command(name="roleinfo", description="info abt a role. use : ,roleifo role name or ,ri rolename", aliases=['ri'] )
async def roleinfo(ctx, *, role_name: str):
    try:
        # Convert the role name to lowercase for case-insensitive comparison
        role_name_lower = role_name.lower()
        role = None
        
        for r in ctx.guild.roles:
            if r.name.lower() == role_name_lower:
                role = r
                break
        
        if role is None:
            await ctx.send(f"Role '{role_name}' does not exist.")
            return
        
        embed_color = role.color if role.color.value != 0 else discord.Color.random()
        embed = discord.Embed(title=role.name, color=embed_color)
        
        if role.icon:
            embed.set_thumbnail(url=role.icon.url)
        else:
            embed.set_thumbnail(url=ctx.guild.icon.url)
            
        embed.add_field(name="Role Color", value=str(role.color), inline=False)
        embed.add_field(name="Members", value=str(len(role.members)), inline=False)
        embed.add_field(name="Permissions", value=', '.join([perm.replace("_", " ").title() for perm, value in role.permissions if value]), inline=False)
        embed.set_footer(text="Sent with 💟 ")
        await ctx.send(embed=embed)
    
    except Exception as e:
        await ctx.send(f"An error occurred: {str(e)}")   

roleinfo.category = "Utility"          

#================================================ USER INFO =================================================  



# Set profile GIF
@client.hybrid_command(name="setprofilegif", description="Set your custom profile GIF", aliases=["spg"])
async def setprofilegif(ctx, gif_link: str):
    if not gif_link.endswith(".gif") or not gif_link.startswith("http"):
        await ctx.send("Please provide a valid .gif URL.")
        return

    user_id = str(ctx.author.id)
    data = load_data("profile_gifs.json")
    if user_id not in data:
        data[user_id] = {}
    data[user_id]["gif_url"] = gif_link
    save_data("profile_gifs.json", data)

    await ctx.send("✅ Your custom profile GIF has been saved!")
setprofilegif.category = "Utility"


# Remove profile GIF
@client.hybrid_command(name="removeprofilegif", description="Remove your custom profile GIF", aliases=["rpg"])
async def removeprofilegif(ctx):
    user_id = str(ctx.author.id)
    data = load_data("profile_gifs.json")
    if user_id in data and "gif_url" in data[user_id]:
        del data[user_id]["gif_url"]
        save_data("profile_gifs.json", data)
        await ctx.send("✅ Your custom profile GIF has been removed.")
    else:
        await ctx.send("No custom GIF found for your profile.")
removeprofilegif.category = "Utility"

# Profile command
@client.hybrid_command(name="profile", description="Display profile info with custom gif")
async def profile(ctx, member: discord.Member = None):
    member = member or ctx.author
    colored_roles = [r for r in member.roles if r != ctx.guild.default_role and r.color != discord.Color.default()]
    roles = [r for r in member.roles if r != ctx.guild.default_role]
    role_color = colored_roles[-1].color if colored_roles else discord.Color.blue()

    embed = discord.Embed(title=f"ℹ️ {member.name}'s Info", color=role_color)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="", value=member.mention, inline=False)
    embed.add_field(name="🏷️ Roles:", value=', '.join(f"<@&{r.id}>" for r in roles), inline=False)
    embed.add_field(
        name="🧭 Joined Server & Account Created:",
        value=f"Joined: `{member.joined_at.strftime('%Y-%m-%d %H:%M:%S')}`\nCreated: `{member.created_at.strftime('%Y-%m-%d %H:%M:%S')}`",
        inline=False)

    important_perms = [
        'administrator', 'manage_guild', 'manage_roles', 'manage_channels',
        'manage_messages', 'manage_webhooks', 'manage_nicknames',
        'manage_emojis', 'kick_members', 'ban_members',
        'mention_everyone', 'mute_members', 'create_instant_invite']

    enabled = [perm.replace('_', ' ').title() for perm, val in member.guild_permissions if val and perm in important_perms]
    embed.add_field(name="🔐 Key Permissions:", value=', '.join(enabled) or "`None`", inline=False)

    acknowledgements = []
    if member == ctx.guild.owner:
        acknowledgements.append("*Server Owner* 👑")
    if ctx.guild.me.guild_permissions.administrator and member.guild_permissions.administrator:
        acknowledgements.append("*Server Admin* 🛡️")
    if acknowledgements:
        embed.add_field(name="📜 Acknowledgements:", value='\n'.join(acknowledgements), inline=False)

    data = load_data("profile_gifs.json")
    gif_url = data.get(str(member.id), {}).get("gif_url")
    if gif_url:
        embed.set_image(url=gif_url)
    else:
        embed.add_field(name="🎞️ Custom GIF", value="No custom GIF set.", inline=False)

    embed.set_footer(text=f"🆔 User ID: {member.id} | Sent with 💟")
    await ctx.send(embed=embed)
profile.category = "Utility"




#=========================================== User Profile Picture =========================================== 


@client.hybrid_command(name="av", description="Display profile picture of a user")
async def av(ctx, user: discord.Member = None):
    if user is None:
        user = ctx.author

    color = discord.Color(random.randint(0, 0xFFFFFF))
    embed = discord.Embed(title=f"Avatar of {user.display_name}", color=color)
    embed.set_image(url=user.display_avatar.url)
    embed.set_footer(text=f"Requested by {ctx.author}", icon_url=ctx.author.display_avatar.url)
    await ctx.send(embed=embed)
av.category = "Utility"

#=================================Change Nickname====================================

@client.hybrid_command(name="nickname" , description= "Change a nickname of user in server", aliases=['nick'])
@commands.has_permissions(manage_nicknames=True)
async def nickname(ctx, member: discord.Member, *, new_nickname: str):
    try:
        await member.edit(nick=new_nickname)
        await ctx.send(f'Nickname changed for {member.mention} to {new_nickname}')
    except discord.Forbidden:
        await ctx.send('I do not have permission to change nicknames for this user.')
    except discord.HTTPException as e:
        await ctx.send(f'Failed to change nickname: {e}')
nickname.category = "Utility"

@nickname.error
async def nickname_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send('You do not have permission to use this command.')





#=========================================== AFK =========================================== 


AFK_FILE = "afk.json"
AFK_PINGS_FILE = "afk_pings.json"

# Load AFK status from a file
def load_afk_status():
    if os.path.exists(AFK_FILE):
        try:
            with open(AFK_FILE, "r") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    return {}

# Save AFK status to a file
def save_afk_status(afk_status):
    with open(AFK_FILE, "w") as file:
        json.dump(afk_status, file, indent=4)

# Load AFK pings from a file
def load_afk_pings():
    if os.path.exists(AFK_PINGS_FILE):
        try:
            with open(AFK_PINGS_FILE, "r") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    return {}

# Save AFK pings to a file
def save_afk_pings(afk_pings):
    with open(AFK_PINGS_FILE, "w") as file:
        json.dump(afk_pings, file, indent=4)

# Load the AFK status and pings
afk_status = load_afk_status()
afk_pings = load_afk_pings()

@client.hybrid_command(name="afk", description="Set your AFK status", aliases=['al'])
async def afk(ctx, *, reason: str = "AFK"):
    server_id = str(ctx.guild.id)
    user_id = str(ctx.author.id)
    nickname = ctx.author.nick if ctx.author.nick else ctx.author.name

    if server_id not in afk_status:
        afk_status[server_id] = {}

    afk_status[server_id][user_id] = reason
    save_afk_status(afk_status)

    if server_id not in afk_pings:
        afk_pings[server_id] = {}
    afk_pings[server_id][user_id] = []
    save_afk_pings(afk_pings)

    try:
        await ctx.author.edit(nick=f"[AFK] {nickname}")
        confirmation_message = await ctx.send(f'**{ctx.author.name}.exe has stopped responding....**: {reason}')
    except discord.Forbidden:
        await ctx.send("AFK status set but I don't have permission to change your nickname. Please ensure my role is higher than yours.")
        return
    except discord.HTTPException as e:
        await ctx.send(f"Failed to change nickname: {e}")
        return

    try:
        await ctx.message.delete()
    except discord.Forbidden:
        await confirmation_message.edit(content=f'{ctx.author.name} is now AFK: {reason} \n Note: I couldn’t delete your command message due to missing permissions.')
    except discord.HTTPException as e:
        await confirmation_message.edit(content=f'{ctx.author.name} is now AFK: {reason} \n Note: Failed to delete your command message: {e}')

@client.hybrid_command(name="afklist", description="Sent a list of all afk users", aliases=['alist'])
async def afklist(ctx):
    server_id = str(ctx.guild.id)

    if server_id not in afk_status or not afk_status[server_id]:
        await ctx.send("No one is AFK in this server.")
        return

    embed = discord.Embed(title="AFK User List", color=discord.Color.green())

    for user_id, reason in afk_status[server_id].items():
        member = ctx.guild.get_member(int(user_id))
        if member:
            embed.add_field(name=f"**{member.name}**", value=f"(ID: {user_id}): {reason}", inline=False)

    embed.set_footer(text="Sent with 💟")
    await ctx.send(embed=embed)

@client.event
async def on_message(message):
    if message.guild:
        server_id = str(message.guild.id)
        user_id = str(message.author.id)

        # Remove AFK status if the user sends a message
        if server_id in afk_status and user_id in afk_status[server_id]:
            reason = afk_status[server_id].pop(user_id)
            pings = afk_pings.get(server_id, {}).pop(user_id, [])
            if not afk_status[server_id]:
                afk_status.pop(server_id)
            if not afk_pings.get(server_id):
                afk_pings.pop(server_id)
            save_afk_status(afk_status)
            save_afk_pings(afk_pings)

            nickname = message.author.nick
            if nickname and nickname.startswith("[AFK]"):
                new_nick = nickname[6:]
                try:
                    await message.author.edit(nick=new_nick)
                except discord.Forbidden:
                    await message.channel.send("I don't have permission to change your nickname.")
                except discord.HTTPException as e:
                    await message.channel.send(f"Failed to change nickname: {e}")

            embed = discord.Embed(
                title=f"Welcome back {message.author.display_name}!",
                description="Your AFK status has been removed.",
                color=discord.Color.green()
            )

            if pings:
                for idx, ping in enumerate(pings, 1):
                    embed.add_field(
                        name=f"Ping #{idx}",
                        value=f"[{ping['author_name']}]({ping['jump_url']}) said: {ping['content'][:100]}...",
                        inline=False
                    )

            await message.channel.send(embed=embed)

        users_to_notify = set(message.mentions)

        if message.reference:
            try:
                ref_message = await message.channel.fetch_message(message.reference.message_id)
                if ref_message.author.id in afk_status.get(server_id, {}):
                    users_to_notify.add(ref_message.author)
            except discord.NotFound:
                pass

        for user in users_to_notify:
            if (server_id in afk_status) and (str(user.id) in afk_status[server_id]):
                reason = afk_status[server_id][str(user.id)]
                embed = discord.Embed(
                    title=f"{user.name}.exe has stopped responding......",
                    description=f"Reason: {reason}",
                    color=discord.Color.random()
                )
                await message.channel.send(embed=embed)

                if server_id not in afk_pings:
                    afk_pings[server_id] = {}
                if str(user.id) not in afk_pings[server_id]:
                    afk_pings[server_id][str(user.id)] = []
                afk_pings[server_id][str(user.id)].append({
                    "author_name": message.author.name,
                    "content": message.content,
                    "jump_url": message.jump_url
                })
                save_afk_pings(afk_pings)

    await client.process_commands(message)

@client.event
async def on_member_update(before, after):
    if before.nick != after.nick and before.nick and after.nick:
        if before.nick.startswith("[AFK]") and not after.nick.startswith("[AFK]"):
            server_id = str(after.guild.id)
            user_id = str(after.id)
            if server_id in afk_status and user_id in afk_status[server_id]:
                afk_status[server_id].pop(user_id, None)
                if not afk_status[server_id]:
                    afk_status.pop(server_id)
                afk_pings[server_id].pop(user_id, None)
                if not afk_pings.get(server_id):
                    afk_pings.pop(server_id)
                save_afk_status(afk_status)
                save_afk_pings(afk_pings)





#====================================================== FUN =========================================================== 



#=================================== Waifu Pics ================================= 


# Unified image fetcher
def fetch_waifu_image(category, nsfw=False):
    base = "https://api.waifu.pics/nsfw" if nsfw else "https://api.waifu.pics/sfw"
    url = f"{base}/{category}"
    res = requests.get(url)
    return res.json().get("url")

@client.hybrid_command(name="waifu", description="Get a random waifu image (SFW)",aliases=['w'])
async def waifu(ctx):
    try:
        category = random.choice(["waifu", "neko", "shinobu", "megumin"])
        image_url = fetch_waifu_image(category)
        embed = discord.Embed(color=discord.Color.random())
        embed.set_image(url=image_url)
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")
waifu.category = "Fun"


@client.hybrid_command(name="nsfw", description="Get a random waifu image (NSFW)")
async def nsfw(ctx):
    if not ctx.channel.is_nsfw():
        await ctx.send("🚫 This command can only be used in NSFW channels.")
        return

    try:
        category = random.choice(["waifu", "neko", "trap", "blowjob"])
        image_url = fetch_waifu_image(category, nsfw=True)
        embed = discord.Embed(color=discord.Color.random())
        embed.set_image(url=image_url)
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"An error occurred: {e}")
nsfw.category = "Fun"


# Generic hybrid action command factory
def make_action_command(name, emoji, categories):
    @client.hybrid_command(name=name, description=f"{name.title()} someone")
    async def _action(ctx, user: discord.User):
        image_url = fetch_waifu_image(random.choice(categories))
        embed = discord.Embed(description=f"{ctx.author.mention} {name}s {user.mention} {emoji}", color=discord.Color.random())
        embed.set_image(url=image_url)
        embed.set_footer(text=f"Requested by {ctx.author.display_name}")
        await ctx.send(embed=embed)

    _action.__name__ = name
    return _action  # ⬅️ return the command

make_action_command("lick", "😳😳", ["lick"]).category = "Fun"
make_action_command("kiss", "😚😘", ["kiss"]).category = "Fun"
make_action_command("bully", "😈", ["bully"]).category = "Fun"
make_action_command("cuddle", "🥰", ["cuddle"]).category = "Fun"
make_action_command("hug", "🫂", ["hug", "glomp"]).category = "Fun"
make_action_command("pat", "🥰", ["pat"]).category = "Fun"
make_action_command("bonk", "🥴", ["bonk"]).category = "Fun"
make_action_command("yeet", "😵", ["yeet"]).category = "Fun"
make_action_command("wave", "👋", ["wave"]).category = "Fun"
make_action_command("highfive", "😄", ["highfive"]).category = "Fun"
make_action_command("handhold", "🫣", ["handhold"]).category = "Fun"
make_action_command("bite", "🫢", ["bite"]).category = "Fun"
make_action_command("slap", "🥶", ["slap"]).category = "Fun"
make_action_command("kill", "😮", ["kill"]).category = "Fun"
make_action_command("kicks", "😱", ["kick"]).category = "Fun"

#===================================== 8-BALL =====================================


@client.hybrid_command(name="8ball", description="Ask the Magic 8-Ball a question.",aliases=['8b'])
async def _8ball(ctx, *, question: str):
    icon_url = 'https://i.imgur.com/XhNqADi.png'
    responses = [
        'It is certain.', 'It is decidedly so.', 'Without a doubt.', 'Yes - definitely.',
        'You may rely on it.', 'As I see it, yes.', 'Most likely.', 'Outlook good.', 'Yes.', 'Signs point to yes.',
        'Reply hazy, try again.', 'Ask again later.', 'Better not tell you now.', 'Cannot predict now.', 'Concentrate and ask again.',
        'Do not count on it.', 'My reply is no.', 'My sources say no.', 'Outlook not so good.', 'no... (╯°□°）╯︵ ┻━┻',
        'senpai, pls no ;-;', 'no... baka', 'Very doubtful.'
    ]
    fortune = random.choice(responses)
    embed = discord.Embed(colour=discord.Colour.purple())
    embed.set_author(name='Magic 8-Ball', icon_url=icon_url)
    embed.add_field(name=f'{ctx.author.name} asks:', value=f'"{question}"', inline=False)
    embed.add_field(name="The Magic 8-Ball says:", value=f'**{fortune}**', inline=False)
    await ctx.send(embed=embed)
_8ball.category = "Fun"


#==========================================Gaydaar========================================


@client.hybrid_command(name="gaydar", description="Measure someone's gayness! Just for fun!")
async def gaydar(ctx, member: discord.Member = None):
    member = member or ctx.author
    percentage = random.randint(0, 100)
    embed = discord.Embed(
        title="Gaydar",
        description=f"`{member.display_name}` is **{percentage}%** gay!",
        color=random.randint(0, 0xFFFFFF)
    )
    embed.set_thumbnail(url="https://static01.nyt.com/images/2013/05/27/booming/27mystory-booming-gaydar1/27mystory-booming-gaydar1-superJumbo.jpg")
    await ctx.send(embed=embed)
gaydar.category = "Fun"

#==========================================femboy========================================

    
@client.hybrid_command(name="femboy", description="Are you an femboy ??")
async def femboy(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author

    percentage = random.randint(0, 100)
    embed = discord.Embed(title="Femboy Rating", description=f"`{member.display_name}` is **{percentage}%** femboy!", color=random.randint(0, 0xFFFFFF))
    embed.set_thumbnail(url=member.display_avatar.url)
    
    await ctx.send(embed=embed)
femboy.category = "Fun"


#==========================================roast========================================


with open('roasts.json', 'r') as file:
    insults = file.readlines()

async def generate_insult():
    return random.choice(insults).strip()

@client.hybrid_command(name="roast", description="Roast a user")
async def roast(ctx, target: discord.Member):
    insult_message = await generate_insult()
    await ctx.send(f"{target.mention}, {insult_message}")
roast.category = "Fun"

#==========================================Pickup========================================


with open('lines.json', 'r') as file:
    pickup_lines = file.readlines()

async def generate_pickup():
    return random.choice(pickup_lines).strip()

@client.hybrid_command(name="pickup", description="you looks delicious")
async def pickup(ctx, target: discord.Member):
    pick_message = await generate_pickup()
    await ctx.send(f"{target.mention}, {pick_message}")
pickup.category = "Fun"



#========================================== Roll dice ========================================


@client.hybrid_command(name="roll_dice", description="Roll two dice",aliases=['roll'])
async def roll_dice(ctx):
    icon_url = 'https://i.imgur.com/rkfXx3q.png'
    die1 = random.randint(1, 6)
    die2 = random.randint(1, 6)
    total = die1 + die2

    embed = discord.Embed(colour=discord.Colour.blue())
    embed.set_author(name='Dice Roller', icon_url=icon_url)
    embed.add_field(
        name=f'*{ctx.author.name} rolls the dice...*',
        value=f'**{die1}** and **{die2}** for a total of **{total}**'
    )
    await ctx.send(embed=embed)
roll_dice.category = "Fun"

#========================================== Coin Flip========================================


@client.hybrid_command(name="coin", description="Flip a coin")
async def coin(ctx):
    icon_url = 'https://cdn-0.emojis.wiki/emoji-pics/whatsapp/coin-whatsapp.png'
    faces = ['Heads!', 'Tails!']
    outcome = random.choice(faces)

    embed = discord.Embed(colour=discord.Colour.blue())
    embed.set_author(name='Coin Flip', icon_url=icon_url)
    embed.add_field(name=f'*{ctx.author.name}, the coin lands...*', value=f'**{outcome}**')
    await ctx.send(embed=embed)
coin.category = "Fun"



#==================================================== ECONOMY ========================================================


# Helpers

def get_balance(user_id):
    data = load_data("balances.json")
    return data.get(user_id, {}).get("balance", 0)

def update_balance(user_id, amount):
    data = load_data("balances.json")
    user = data.get(user_id, {})
    user["balance"] = user.get("balance", 0) + amount
    data[user_id] = user
    save_data("balances.json", data)

def set_balance(user_id, amount):
    data = load_data("balances.json")
    user = data.get(user_id, {})
    user["balance"] = amount
    data[user_id] = user
    save_data("balances.json", data)

def get_last_daily(user_id):
    data = load_data("balances.json")
    ts = data.get(user_id, {}).get("last_daily")
    return datetime.fromisoformat(ts) if ts else None

def set_last_daily(user_id):
    data = load_data("balances.json")
    user = data.get(user_id, {})
    user["last_daily"] = datetime.now(timezone.utc).isoformat()
    data[user_id] = user
    save_data("balances.json", data)


#===================================== Balance=====================================

@client.hybrid_command(name="balance", description="Check your or another user's balance", aliases=['bal'])
async def balance(ctx, user: discord.Member = None):
    user = user or ctx.author
    bal = get_balance(str(user.id))
    await ctx.send(f"💰 {user.display_name}'s balance: `{bal}` Quarks")
balance.category = "Economy"



@client.hybrid_command(name="daily", description="Claim your daily reward")
async def daily(ctx):
    user_id = str(ctx.author.id)
    now = datetime.now(timezone.utc)
    last = get_last_daily(user_id)

    if last and now - last < timedelta(hours=24):
        next_time = last + timedelta(hours=24)
        remain = next_time - now
        hours, minutes = divmod(remain.seconds, 3600)[0], (remain.seconds % 3600) // 60
        await ctx.send(f"🕒 Already claimed. Try again in `{hours}h {minutes}m`.")
    else:
        reward = 500
        update_balance(user_id, reward)
        set_last_daily(user_id)
        await ctx.send(f"🎉 You claimed your daily `{reward}` Quarks!")
daily.category = "Economy"


#===================================== Give =====================================

@client.hybrid_command(name="give", description="Send coins to another user")
async def give(ctx, member: discord.Member, amount: int):
    if amount <= 0:
        return await ctx.send("Amount must be greater than 0.")

    sender_id, recipient_id = str(ctx.author.id), str(member.id)
    if sender_id == recipient_id:
        return await ctx.send("You cannot pay yourself.")

    if get_balance(sender_id) < amount:
        return await ctx.send("💸 Not enough Quarks.")

    update_balance(sender_id, -amount)
    update_balance(recipient_id, amount)
    await ctx.send(f"✅ {ctx.author.display_name} paid `{amount}` Quarks to {member.display_name}!")
give.category = "Economy"


#===================================== Gamble =====================================


@client.hybrid_command(name="gamble", description="Try your luck to double your coins")
async def gamble(ctx, amount: int):
    user_id = str(ctx.author.id)
    if amount <= 0:
        return await ctx.send("Enter a valid amount greater than 0.")

    if get_balance(user_id) < amount:
        return await ctx.send("💸 Not enough coins to gamble.")

    if random.choice([True, False]):
        update_balance(user_id, amount)
        await ctx.send(f"🎉 You won `{amount}` Quarks!")
    else:
        update_balance(user_id, -amount)
        await ctx.send(f"💀 You lost `{amount}` Quarks.")
gamble.category = "Economy"

#===================================== Slot =====================================


@client.hybrid_command(name="slot", description="Spin the slot machine for a chance to win!")
async def slot(ctx, amount: int):
    user_id = str(ctx.author.id)
    if amount <= 0:
        return await ctx.send("Enter a valid amount greater than 0.")

    if get_balance(user_id) < amount:
        return await ctx.send("💸 Not enough Quarks.")

    symbols = ["🍒", "🍋", "🍉", "💎", "⭐"]
    spin = [random.choice(symbols) for _ in range(3)]
    result = " ".join(spin)

    if spin.count(spin[0]) == 3:
        winnings = amount * 3
        update_balance(user_id, winnings)
        msg = f"🎰 `{result}` — Jackpot! You win {winnings} Quarks!"
    elif len(set(spin)) == 2:
        winnings = amount * 2
        update_balance(user_id, winnings)
        msg = f"🎰 `{result}` — Nice! You win {winnings} Quarks."
    else:
        update_balance(user_id, -amount)
        msg = f"🎰 `{result}` — Unlucky! You lost {amount} Quarks."

    await ctx.send(msg)
slot.category = "Economy"


#===================================== Roulette =====================================


@client.hybrid_command(name="roulette", description="Bet on red, black, or green and try your luck!", aliases=['rol'])
async def roulette(ctx, amount: int, color: str):
    user_id = str(ctx.author.id)
    color = color.lower()
    if amount <= 0:
        return await ctx.send("Enter a valid amount greater than 0.")
    if color not in ["red", "black", "green"]:
        return await ctx.send("Choose a valid color: `red`, `black`, or `green`.")
    if get_balance(user_id) < amount:
        return await ctx.send("💸 Not enough Quarks.")

    spin_result = random.choices(["red", "black", "green"], weights=[20, 75, 5])[0]
    color_emojis = {"red": "🔴", "black": "⚫", "green": "🟢"}
    hex_colors = {
        "red": 0xFF0000,
        "black": 0x2F3136,
        "green": 0x00FF00
    }

    embed = discord.Embed(
        title="🎡 Roulette Spin!",
        description=f"**Landed on:** {color_emojis[spin_result]} {spin_result.title()}",
        color=hex_colors[spin_result]
    )
    embed.set_thumbnail(url="https://napoleons-casinos.co.uk/wp-content/uploads/2020/02/IMG-1366Victoria-Greensmith-Photography-min-scaled.jpg")


    if spin_result == color:
        multiplier = 2 if color != "green" else 10
        winnings = amount * multiplier
        update_balance(user_id, winnings)
        embed.add_field(name="Result", value=f"🎉 You won `{winnings}` Quarks!", inline=False)
    else:
        update_balance(user_id, -amount)
        embed.add_field(name="Result", value=f"💀 You lost `{amount}` Quarks.", inline=False)

    embed.add_field(
        name="🎲 Odds",
        value="🔴 Red — 20% ×2\n⚫ Black — 75% Lose\n🟢 Green — 5% ×10",
        inline=False
    )
    

    await ctx.send(embed=embed)
roulette.category = "Economy"




#===================================== Russian Roulette =====================================



# ------- Views -------- #

class RouletteView(discord.ui.View):
    def __init__(self, author, target, amount, timeout=30):
        super().__init__(timeout=timeout)
        self.author = author
        self.target = target
        self.amount = amount
        self.result = None

    @discord.ui.button(label="✅ Accept", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target.id:
            await interaction.response.send_message("❌ You're not the challenged user!", ephemeral=True)
            return
        self.result = "accepted"
        self.stop()

    @discord.ui.button(label="❌ Decline", style=discord.ButtonStyle.red)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target.id:
            await interaction.response.send_message("❌ You're not the challenged user!", ephemeral=True)
            return
        self.result = "declined"
        self.stop()


class RematchView(discord.ui.View):
    def __init__(self, loser, winner, amount, ctx, timeout=30):
        super().__init__(timeout=timeout)
        self.loser = loser
        self.winner = winner
        self.amount = amount
        self.ctx = ctx
        self.triggered = False

    @discord.ui.button(label="🔁 Rematch", style=discord.ButtonStyle.blurple)
    async def rematch(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.loser.id:
            await interaction.response.send_message("Only the loser can request a rematch.", ephemeral=True)
            return
        self.triggered = True
        self.stop()

# ------- Duel Logic -------- #

async def start_roulette_duel(ctx, author, user, amount):
    author_id = str(author.id)
    user_id = str(user.id)

    update_balance(author_id, -amount)
    update_balance(user_id, -amount)

    winner = random.choice([author, user])
    loser = user if winner == author else author

    update_balance(str(winner.id), amount * 2)

    result_embed = discord.Embed(
        title="💥 Bang! Russian Roulette Result",
        description=(
            f"🎯 {winner.mention} survived and wins 💰 **{amount * 2}** quarks!\n"
            f"☠️ {loser.mention} lost the duel."
        ),
        color=discord.Color.green()
    )

    view = RematchView(loser, winner, amount, ctx)
    await ctx.send(embed=result_embed, view=view)
    await view.wait()

    if view.triggered:
        await ctx.send(f"🔁 {loser.mention} has challenged for a rematch!")
        await asyncio.sleep(1)
        await start_roulette_duel(ctx, loser, winner, amount)
    else:
        await ctx.send("⏹️ Rematch window closed.")


# ------- Command -------- #

@client.hybrid_command(name="duel", description="Challenge someone to Russian Roulette and win double the money!", aliases =['d'])
@app_commands.describe(user="The user you want to challenge", amount="Amount to bet")
async def duel(ctx, user: discord.Member, amount: int):
    author = ctx.author

    if user.bot:
        await ctx.send("🤖 You can't challenge bots!")
        return

    if user == author:
        await ctx.send("😅 You can't challenge yourself!")
        return

    if amount <= 0:
        await ctx.send("🚫 Invalid bet amount.")
        return

    author_balance = get_balance(str(author.id))
    user_balance = get_balance(str(user.id))

    if author_balance < amount:
        await ctx.send("💸 You don't have enough money to place that bet.")
        return

    if user_balance < amount:
        await ctx.send(f"💸 {user.display_name} doesn't have enough money to accept the challenge.")
        return

    embed = discord.Embed(
        title="🎯 Duel!",
        description=f"{user.mention}, you’ve been challenged by {author.mention} for 💰 **{amount}** quarks!\n"
                    f"Do you accept this duel?",
        color=discord.Color.red()
    )
    embed.set_footer(text="You have 30 seconds to respond.")

    view = RouletteView(author, user, amount)
    await ctx.send(f"{user.mention}", embed=embed, view=view)

    await view.wait()

    if view.result == "accepted":
        await start_roulette_duel(ctx, author, user, amount)
    elif view.result == "declined":
        await ctx.send(f"{user.mention} declined the duel ❌.")
    else:
        await ctx.send("⌛ Duel request timed out!")
duel.category = "Economy"



#===================================== slot snipe =====================================

@client.hybrid_command(name="slotsnipe", description="Guess bullet-free slots and win big!", aliases=['ss'])
@app_commands.describe(level="Difficulty level (1 to 5)", amount="Bet amount")
async def slotsnipe(ctx, level: int, amount: int):
    author = ctx.author
    user_id = str(author.id)

    if amount <= 0:
        await ctx.send("🚫 Bet amount must be greater than 0.")
        return

    if get_balance(user_id) < amount:
        await ctx.send("💸 You don't have enough balance!")
        return

    # Define game modes
    levels = {
        1: {"bullets": 1, "guesses": 3, "reward": 2},
        2: {"bullets": 2, "guesses": 3, "reward": 3},
        3: {"bullets": 3, "guesses": 3, "reward": 5},
        4: {"bullets": 4, "guesses": 1, "reward": 3},
        5: {"bullets": 5, "guesses": 1, "reward": 10},
    }

    if level not in levels:
        await ctx.send("❌ Invalid level. Choose between 1 and 5.")
        return

    config = levels[level]
    bullet_count = config["bullets"]
    total_slots = 6
    guesses_left = config["guesses"]
    reward_multiplier = config["reward"]

    bullet_slots = random.sample(range(1, total_slots + 1), bullet_count)
    safe_guesses = []

    update_balance(user_id, -amount)

    def check(msg):
        return msg.author == author and msg.channel == ctx.channel and msg.content.isdigit()

    status_text = (
        f"🎮 **Slotsnipe Started!**\n"
        f"💣 Bullets: `{bullet_count}` | 🎯 Guesses: `{guesses_left}` | 💰 Bet: `{amount}`\n"
        f"Pick a number between **1 and 6**."
    )
    status_message = await ctx.send(status_text)

    while guesses_left > 0:
        try:
            guess_msg = await client.wait_for("message", timeout=30.0, check=check)
            guess = int(guess_msg.content)
            await guess_msg.delete()

            if guess < 1 or guess > 6:
                await status_message.edit(
                    content=status_text + f"\n⚠️ `{guess}` is invalid. Please choose between 1 and 6."
                )
                continue

            if guess in bullet_slots:
                await status_message.edit(
                    content=(
                        f"💥 **BOOM!** You picked slot `{guess}` and hit a bullet!\n"
                        f"☠️ You lost **{amount}** quarks. Game over."
                    )
                )
                return

            safe_guesses.append(guess)
            guesses_left -= 1
            status_text = (
                f"🎮 **Slotsnipe Progress**\n"
                f"✅ Safe guesses: `{', '.join(map(str, safe_guesses))}`\n"
                f"💣 Bullets: `{bullet_count}` | 🎯 Guesses left: `{guesses_left}`\n"
                f"Pick another number between **1 and 6**."
            )
            await status_message.edit(content=status_text)

        except asyncio.TimeoutError:
            await status_message.edit(content="⌛ Timed out. Game cancelled. Bet refunded.")
            update_balance(user_id, amount)
            return

    # Success!
    reward = amount * reward_multiplier
    update_balance(user_id, reward)

    final_text = (
        f"🎉 **Victory!** You survived all your guesses.\n"
        f"✅ Safe slots: `{', '.join(map(str, safe_guesses))}`\n"
        f"💰 You won **{reward}** quarks (x{reward_multiplier})!"
    )
    await status_message.edit(content=final_text)
slotsnipe.category = "Economy"


#===================================== BEG =====================================



@client.hybrid_command(name="beg", description="Beg for some coins!")
@commands.cooldown(1, 60, commands.BucketType.user)
async def beg(ctx):
    if random.random() < 0.7:
        await ctx.send("😔 You begged, but everyone ignored you...")
    else:
        amount = random.randint(50, 150)
        update_balance(str(ctx.author.id), amount)
        await ctx.send(f"🙏 A kind soul gave you `{amount}` Quarks!")
beg.category = "Economy"

@beg.error
async def beg_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        retry = timedelta(seconds=round(error.retry_after))
        minutes = retry.seconds // 60
        seconds = retry.seconds % 60
        await ctx.send(f"⌛ You need to wait `{minutes}m {seconds}s` before trying to beg again.")
    else:
        raise error


#===================================== HUNT =====================================



@client.hybrid_command(name="hunt", description="Go on a hunt to earn coins!")
@commands.cooldown(1, 60, commands.BucketType.user)
async def hunt(ctx):
    animals = ["rabbit", "deer", "boar", "duck"]
    animal = random.choice(animals)
    reward = random.randint(0, 200)
    update_balance(str(ctx.author.id), reward)
    await ctx.send(f"🏹 You hunted a {animal} and earned `{reward}` Quarks!")
hunt.category = "Economy"

@hunt.error
async def hunt_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        retry = timedelta(seconds=round(error.retry_after))
        minutes = retry.seconds // 60
        seconds = retry.seconds % 60
        await ctx.send(f"⌛ You need to wait `{minutes}m {seconds}s` before trying to hunt again.")
    else:
        raise error



#===================================== ADVENTURE =====================================


@client.hybrid_command(name="adventure", description="Go on a hunt to earn coins!", aliases=['adv'])
@commands.cooldown(1, 3600, commands.BucketType.user)
async def adventure(ctx):
    outcomes = [
        ("treasure", 500, "💰 You found a hidden treasure and earned `{}` Quarks!"),
        ("enemy", -200, "⚔️ You were attacked by a wild beast and lost `{}` Quarks!"),
        ("nothing", 0, "🌲 You wandered the forest but found nothing of value.")
    ]
    outcome = random.choice(outcomes)
    update_balance(str(ctx.author.id), outcome[1])
    await ctx.send(outcome[2].format(abs(outcome[1])))
adventure.category = "Economy"

@adventure.error
async def adventure_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        retry = timedelta(seconds=round(error.retry_after))
        minutes = retry.seconds // 60
        seconds = retry.seconds % 60
        await ctx.send(f"⌛ You need to wait `{minutes}m {seconds}s` before u can go on an adventure again.")
    else:
        raise error


#===================================== FISH =====================================


@client.hybrid_command(name="fish", description="Go fishing and earn coins!")
@commands.cooldown(1, 60, commands.BucketType.user)
async def fish(ctx):
    results = [
        ("Common fish", 50, "🐟 You caught a common fish and earned `{}` Quarks!"),
        ("Rare fish", 150, "🌟 You reeled in a rare fish and earned `{}` Quarks!"),
        ("Trash", 0, "🗑️ You fished up some trash. Better luck next time."),
        ("Shark bite", -100, "🦈 A shark bit your line and you lost `{}` Quarks!")
    ]
    result = random.choice(results)
    update_balance(str(ctx.author.id), result[1])
    await ctx.send(result[2].format(abs(result[1])))
fish.category = "Economy"


@fish.error
async def fish_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        retry = timedelta(seconds=round(error.retry_after))
        minutes = retry.seconds // 60
        seconds = retry.seconds % 60
        await ctx.send(f"⌛ You need to wait `{minutes}m {seconds}s` before trying to fish again.")
    else:
        raise error





# ======================== Bank ==============================

def apply_bank_interest(user_id, rate=0.02):
    data = load_data("bank.json")
    user = data.get(user_id, {})
    now = datetime.now(timezone.utc)
    
    last_str = user.get("last_interest")
    last_time = datetime.fromisoformat(last_str) if last_str else None

    if not last_time or (now - last_time) >= timedelta(hours=24):
        balance = user.get("balance", 0)
        interest = int(balance * rate)
        user["balance"] = balance + interest
        user["last_interest"] = now.isoformat()
        data[user_id] = user
        save_data("bank.json", data)
        return interest
    return 0

# ======================== Bank ==========================

@client.hybrid_command(name="bank", description="Check your banked Quarks")
async def bank(ctx):
    user_id = str(ctx.author.id)
    apply_bank_interest(user_id)
    data = load_data("bank.json")
    balance = data.get(user_id, {}).get("balance", 0)

    embed = discord.Embed(title="\U0001F3E6 Bank Account", color=discord.Color.teal())
    embed.add_field(name="\U0001F4B0 Vault Balance", value=f"`{balance}` Quarks", inline=False)
    embed.set_footer(text="Use /deposit and /withdraw to manage funds.")
    await ctx.send(embed=embed)
bank.category = "Economy"


# ======================== Deposit ==========================


@client.hybrid_command(name="deposit", description="Deposit coins into your bank")
async def deposit(ctx, amount: str):
    user_id = str(ctx.author.id)
    apply_bank_interest(user_id)
    bank_data = load_data("bank.json")
    wallet = get_balance(user_id)

    if amount.lower() == "all":
        amount = wallet
    else:
        try:
            amount = int(amount)
        except ValueError:
            return await ctx.send("Enter a number or `all`.")

    if amount <= 0:
        return await ctx.send("Deposit amount must be positive.")
    if wallet < amount:
        return await ctx.send("\U0001F4B8 Not enough Quarks in wallet.")

    update_balance(user_id, -amount)
    user = bank_data.get(user_id, {})
    user["balance"] = user.get("balance", 0) + amount
    bank_data[user_id] = user
    save_data("bank.json", bank_data)

    await ctx.send(f"✅ Deposited `{amount}` Quarks into your bank.")
deposit.category = "Economy"


# ======================== Withdraw ==========================

@client.hybrid_command(name="withdraw", description="Withdraw coins from your bank")
async def withdraw(ctx, amount: str):
    user_id = str(ctx.author.id)
    apply_bank_interest(user_id)
    bank_data = load_data("bank.json")
    user = bank_data.get(user_id, {"balance": 0})
    vault = user["balance"]

    if amount.lower() == "all":
        amount = vault
    else:
        try:
            amount = int(amount)
        except ValueError:
            return await ctx.send("Enter a number or `all`.")

    if amount <= 0:
        return await ctx.send("Withdraw amount must be positive.")
    if vault < amount:
        return await ctx.send("\U0001F3E6 Not enough Quarks in bank.")

    user["balance"] -= amount
    bank_data[user_id] = user
    save_data("bank.json", bank_data)
    update_balance(user_id, amount)

    await ctx.send(f"\U0001F4B5 Withdrew `{amount}` Quarks from your bank.")
withdraw.category = "Economy"



#===================================== Steal =====================================



@client.hybrid_command(name="steal", description="Try to steal Quarks from another user's wallet")
@commands.cooldown(1, 3600, commands.BucketType.user)  # 1 use per hour
async def steal(ctx, target: discord.Member):
    if target.id == ctx.author.id:
        return await ctx.send("You can't steal from yourself.")

    thief_id = str(ctx.author.id)
    target_id = str(target.id)

    target_balance = get_balance(target_id)
    thief_balance = get_balance(thief_id)

    if target_balance < 100:
        return await ctx.send("That user doesn't have enough Quarks to steal from.")

    success = random.random() < 0.4  # 40% success chance
    if success:
        percent = random.uniform(0.2, 0.5)
        amount = int(target_balance * percent)
        update_balance(target_id, -amount)
        update_balance(thief_id, amount)
        await ctx.send(f"🕵️ {ctx.author.mention} successfully stole `{amount}` Quarks from {target.mention}!")
        try:
            await target.send(f"⚠️ Someone tried to steal from you and succeeded! `{amount}` Quarks were stolen by {ctx.author.display_name}.")
        except:
            pass
    else:
        percent = random.uniform(0.2, 0.5)
        fine = int(thief_balance * percent)
        update_balance(thief_id, -fine)
        update_balance(target_id, fine)
        await ctx.send(f"🚓 You got caught! You were fined `{fine}` Quarks and it was given to {target.mention}.")
        try:
            await target.send(f"🚨 {ctx.author.display_name} tried to steal from you but failed. You received `{fine}` Quarks as compensation.")
        except:
            pass
steal.category = "Economy"

@steal.error
async def steal_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        retry = timedelta(seconds=round(error.retry_after))
        minutes = retry.seconds // 60
        seconds = retry.seconds % 60
        await ctx.send(f"⌛ You need to wait `{minutes}m {seconds}s` before trying to steal again.")
    else:
        raise error




#===================================== Richest =====================================



@client.hybrid_command(name="richest", description="Show top richest users", aliases=['top'])
async def richest(ctx):
    wallet_data = load_data("balances.json")
    bank_data = load_data("bank.json")

    combined = {}
    for user_id in set(wallet_data.keys()) | set(bank_data.keys()):
        wallet = wallet_data.get(user_id, {}).get("balance", 0)
        bank = bank_data.get(user_id, {}).get("balance", 0)
        combined[user_id] = wallet + bank

    sorted_users = sorted(combined.items(), key=lambda x: x[1], reverse=True)[:10]
    embed = discord.Embed(title="\U0001F3C6 Leaderboard – Top 10 Richest Users", color=discord.Color.gold())
    for i, (user_id, total) in enumerate(sorted_users, 1):
        user = ctx.guild.get_member(int(user_id)) or f"<@{user_id}>"
        name = user.display_name if isinstance(user, discord.Member) else str(user)
        embed.add_field(name=f"#{i} {name}", value=f"💰 `{total}` Quarks (wallet+bank)", inline=False)
    await ctx.send(embed=embed)
richest.category = "Economy"


#===================================== THE END =====================================


#Run the bot 

client.run(os.getenv("DISCORD_TOKEN"))

