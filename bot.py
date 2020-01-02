import random
import os
import asyncio
import dotenv
import discord
from datetime import datetime, timedelta
import json
import calendar

loop = asyncio.get_event_loop()

client = discord.Client()
data = json.loads(open("data.json", 'r').read())


async def new_holiday_check():
    day = getDay()
    # if its the first of the month, prepare the new month roles and send update messages
    # also process the role for previous month
    if day == 1:
        print("FIRST OF THE MONTH! Sending new messages to guilds!")
        for guild in client.guilds:
            # handle previous month
            prev_month = getPreviousMonth()
            prev_month_data = data[prev_month]
            prev_month_roles = prev_month_data["ROLES"]
            prev_roles = []
            for prev_month_role in prev_month_roles:
                if prev_month_role["NAME"] in [role.name for role in guild.roles]:
                    # exists
                    print("role found")
                    role = next(x for x in guild.roles if x.name == prev_month_role["NAME"])
                    prev_roles.append(role)
                    print(f"Appended role {role.name}")

            for role in prev_roles:
                try:
                    year = getYear() - 1 if prev_month == "DECEMBER" else getYear()
                    await role.edit(name=f"{role.name} {year}", color=discord.Color.default())
                except discord.Forbidden:
                    print(f"Forbidden editing role {role.name}")
                except discord.HTTPException:
                    print(f"Failed to edit role {role.name}")
                print(f"Updated prev role {role.name} for guild {guild.name}")

            # handle new month
            config = json.loads(open("config.json", 'r').read())
            channel_id = config[str(guild.id)]["CHANNEL_ID"] if config[str(guild.id)] else None
            if channel_id:
                channel = guild.get_channel(channel_id)
                month = getMonth()
                month_data = data[month]
                holiday = month_data["HOLIDAY"]
                month_roles = month_data["ROLES"]
                emojis = month_data["EMOJIS"]
                words = month_data["WORDS"]

                roles = []
                for month_role in month_roles:
                    if month_role["NAME"] in [role.name for role in guild.roles]:
                        # exists
                        print("role found")
                        role = next(x for x in guild.roles if x.name == month_role["NAME"])
                        roles.append(role)
                        print(f"Appended role {role.name}")
                    else:
                        # not found, create
                        role = await create_roles(guild, month_role["NAME"], month_role["COLOR"])
                        roles.append(role)

                role_format = f"the {roles[0].mention} role" if len(
                    roles) == 1 else f"{','.join([role.mention for role in roles])} roles"

                embed = discord.Embed(title=f"New Holiday: ``{holiday}``",
                                      description=f"Hello! It's a new month and there is a new holiday role available!\n\nServer nicknames must include one of the following:\nEmojis: ``{','.join(emojis)}``\nor\nWords: ``{','.join(words)}``\n\nYou can gain {role_format} for {getYear()}!\n\n*Remember: These roles are permanent and cannot be changed!*",
                                      color=discord.Color.red(), timestamp=datetime.utcnow())
                embed.set_footer(text=client.user.display_name)

                try:
                    await channel.send(content=None, embed=embed)
                except discord.Forbidden:
                    print("Forbidden sending message")
                except discord.HTTPException:
                    print("Failed to send message")


async def new_holiday_check_guild(message: discord.Message):
    day = getDay()
    # if its the first of the month, prepare the new month roles and send update messages
    # also process the role for previous month
    if day == 1:
        print(f"guild requested force update: {message.guild.name}")
        # handle previous month
        prev_month = getPreviousMonth()
        prev_month_data = data[prev_month]
        prev_month_roles = prev_month_data["ROLES"]
        prev_roles = []
        for prev_month_role in prev_month_roles:
            if prev_month_role["NAME"] in [role.name for role in message.guild.roles]:
                # exists
                print("role found")
                role = next(x for x in message.guild.roles if x.name == prev_month_role["NAME"])
                prev_roles.append(role)
                print(f"Appended role {role.name}")

        for role in prev_roles:
            try:
                year = getYear() - 1 if prev_month == "DECEMBER" else getYear()
                await role.edit(name=f"{role.name} {year}", color=discord.Color.default())
            except discord.Forbidden:
                print(f"Forbidden editing role {role.name}")
            except discord.HTTPException:
                print(f"Failed to edit role {role.name}")
            print(f"Updated prev role {role.name} for guild {message.guild.name}")

        # handle new month
        config = json.loads(open("config.json", 'r').read())
        channel_id = config[str(message.guild.id)]["CHANNEL_ID"] if config[str(message.guild.id)] else None
        if channel_id:
            channel = message.guild.get_channel(channel_id)
            month = getMonth()
            month_data = data[month]
            holiday = month_data["HOLIDAY"]
            month_roles = month_data["ROLES"]
            emojis = month_data["EMOJIS"]
            words = month_data["WORDS"]

            roles = []
            for month_role in month_roles:
                if month_role["NAME"] in [role.name for role in message.guild.roles]:
                    # exists
                    print("role found")
                    role = next(x for x in message.guild.roles if x.name == month_role["NAME"])
                    roles.append(role)
                    print(f"Appended role {role.name}")
                else:
                    # not found, create
                    print("role not found, creating")
                    role = await create_roles(message.guild, month_role["NAME"], month_role["COLOR"])
                    roles.append(role)

            role_format = f"the {roles[0].mention} role" if len(
                roles) == 1 else f"{','.join([role.mention for role in roles])} roles"

            embed = discord.Embed(title=f"New Holiday: ``{holiday}``",
                                  description=f"Hello! It's a new month and there is a new holiday role available!\n\nServer nicknames must include one of the following:\nEmojis: ``{','.join(emojis)}``\nor\nWords: ``{','.join(words)}``\n\nYou can gain {role_format} for {getYear()}!\n\n*Remember: These roles are permanent and cannot be changed!*",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=client.user.display_name)

            try:
                await channel.send(content=None, embed=embed)
            except discord.Forbidden:
                print("Forbidden sending message")
            except discord.HTTPException:
                print("Failed to send message")

    await message.channel.send("Force update complete!")


@client.event
async def on_ready():
    print(f"Logged in as {client.user}, Serving {len(client.guilds)} guilds and {len(client.users)} users!")
    timer = TaskTimer(new_holiday_check)


# event used for when a member updates nickname
# ignores bots
@client.event
async def on_member_update(before: discord.Member, after: discord.Member):
    if before.bot:
        return
    if before.nick == after.nick:
        return
    if not after.nick:
        return

    month = getMonth()
    month_data = data[month]
    holiday = month_data["HOLIDAY"]
    use_random_role = month_data["RANDOM_ROLE"]
    month_roles = month_data["ROLES"]
    emojis = month_data["EMOJIS"]
    words = month_data["WORDS"]
    required = emojis + words

    if any(x in after.nick.lower() for x in required):
        roles = []
        for month_role in month_roles:
            if month_role["NAME"] in [role.name for role in after.guild.roles]:
                # exists
                print("role found")
                role = next(x for x in after.guild.roles if x.name == month_role["NAME"])
                roles.append(role)
                print(f"Appended role {role.name}")
            else:
                # not found, create
                print("role not found")
                try:
                    role = await after.guild.create_role(name=month_role["NAME"],
                                                         color=discord.Colour(month_role["COLOR"]))
                    print(f"Created role {role.name}")
                    roles.append(role)
                except discord.Forbidden:
                    try:
                        await before.guild.owner.send(
                            "Sorry to bother you but it seems that I am missing permission to create the proper roles!")
                        print("Missing permission to create roles, owner notified.")
                    except (discord.Forbidden, discord.HTTPException):
                        print("Missing permission to create roles, failed to notify owner.")
                except discord.HTTPException:
                    try:
                        await before.guild.owner.send(
                            "Sorry to bother you but it seems that I failed to create the proper roles!")
                        print("Failed to create roles, owner notified.")
                    except (discord.Forbidden, discord.HTTPException):
                        print("Failed to create roles, failed to notify owner.")

        # add roles to member
        await addRole(after, roles, use_random_role)


@client.event
async def on_guild_join(guild: discord.Guild):
    month = getMonth()
    month_data = data[month]
    month_roles = month_data["ROLES"]

    for month_role in month_roles:
        if not month_role["NAME"] in [role.name for role in guild.roles]:
            # not found, create
            print("role not found, creating")
            await create_roles(guild, month_role["NAME"], month_role["COLOR"])


@client.event
async def on_message(message):
    if message.author.bot:
        return
    if not message.content.startswith('!'):
        return
    command = message.content[1::].split(" ")[0]
    args = message.content[1::].split(" ")[1::]
    # if command.lower() == "settimezone":
    #     if not len(args) == 1:
    #         return await message.channel.send("too many or not enough args")
    #     config = json.loads(open("config.json", 'r').read())
    #     config[message.guild.id] = {
    #         "TIMEZONE": args[0].upper()
    #     }
    #     file = open("config.json", 'w')
    #     file.write(json.dumps(config))
    #     file.close()
    #     print("config updated")
    #     return await message.channel.send(f"Timezone set to {args[0].upper()}")
    if command.lower() == "setupdatechannel":
        if not len(args) == 1:
            return await message.channel.send("too many or not enough args")
        channel = client.get_channel(int(args[0]))
        if channel:
            config = json.loads(open("config.json", 'r').read())
            config[message.guild.id] = {
                "CHANNEL_ID": channel.id
            }
            file = open("config.json", 'w')
            file.write(json.dumps(config))
            file.close()
            print("config updated")
            return await message.channel.send(f"Channel set to {channel.mention}")
        else:
            return await message.channel.send(f"Channel with id {args[0]} not found!")

    if command.lower() == "forceupdate":
        if not len(args) == 0:
            return await message.channel.send("too many or not enough args")

        await message.channel.send("Force Updating guild...")
        month = getMonth()
        month_data = data[month]
        holiday = month_data["HOLIDAY"]
        month_roles = month_data["ROLES"]
        emojis = month_data["EMOJIS"]
        words = month_data["WORDS"]

        roles = []
        for month_role in month_roles:
            if month_role["NAME"] in [role.name for role in message.guild.roles]:
                # exists
                print("role found")
                role = next(x for x in message.guild.roles if x.name == month_role["NAME"])
                roles.append(role)
                print(f"Appended role {role.name}")
            else:
                # not found, create
                print("role not found, creating")
                role = await create_roles(message.guild, month_role["NAME"], month_role["COLOR"])
                print(role.id)
                print(role.name)
                roles.append(role)
                print(f"Appended role {role.name}")

        role_format = f"the {roles[0].mention} role" if len(
            roles) == 1 else f"{','.join([role.mention for role in roles])} roles"

        embed = discord.Embed(title=f"New Holiday: ``{holiday}``",
                              description=f"Hello! It's a new month and there is a new holiday role available!\n\nServer nicknames must include one of the following:\nEmojis: ``{','.join(emojis)}``\nor\nWords: ``{','.join(words)}``\n\nYou can gain {role_format} for {getYear()}!\n\n*Remember: These roles are permanent and cannot be changed!*",
                              color=discord.Color.red(), timestamp=datetime.utcnow())
        embed.set_footer(text=client.user.display_name)

    if command.lower() == "resendlatest":
        if not len(args) == 0:
            return await message.channel.send("too many or not enough args")

        await message.channel.send("Resending latest holiday message!")
        config = json.loads(open("config.json", 'r').read())
        channel_id = config[str(message.guild.id)]["CHANNEL_ID"] if config[str(message.guild.id)] else None
        if channel_id:
            channel = message.guild.get_channel(channel_id)
            month = getMonth()
            month_data = data[month]
            holiday = month_data["HOLIDAY"]
            month_roles = month_data["ROLES"]
            emojis = month_data["EMOJIS"]
            words = month_data["WORDS"]

            roles = []
            for month_role in month_roles:
                if month_role["NAME"] in [role.name for role in message.guild.roles]:
                    # exists
                    print("role found")
                    role = next(x for x in message.guild.roles if x.name == month_role["NAME"])
                    roles.append(role)
                    print(f"Appended role {role.name}")
                else:
                    # not found, create
                    print("role not found, creating")
                    role = await create_roles(message.guild, month_role["NAME"], month_role["COLOR"])
                    print(role.id)
                    print(role.name)
                    roles.append(role)
                    print(f"Appended role {role.name}")

            role_format = f"the {roles[0].mention} role" if len(
                roles) == 1 else f"{','.join([role.mention for role in roles])} roles"

            embed = discord.Embed(title=f"New Holiday: ``{holiday}``",
                                  description=f"Hello! It's a new month and there is a new holiday role available!\n\nServer nicknames must include one of the following:\nEmojis: ``{','.join(emojis)}``\nor\nWords: ``{','.join(words)}``\n\nYou can gain {role_format} for {getYear()}!\n\n*Remember: These roles are permanent and cannot be changed!*",
                                  color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.set_footer(text=client.user.display_name)

            try:
                await channel.send(content=None, embed=embed)
            except discord.Forbidden:
                await message.channel.send(f"Missing permissions to send message! Channel: {channel.mention}")
            except discord.HTTPException:
                await message.channel.send(f"Failed to send message! Channel: {channel.mention}")

    if command.lower() == "help":
        if not len(args) == 0:
            return await message.channel.send("too many or not enough args")

        await message.channel.send(
            "Hello! Current commands:\nsetupdatechannel <channel id> - set a channel for message to be sent every month that has a new role\nforceupdate - force recheck for new holidays/roles\nresendlatest - send the latest role information to the update channel (requires setting update channel!)\n\nHolidayRoleBot by Puyodead1#0001\nSupport server: <https://discord.gg/tMzrSxQ>\n*__This version is in development! Please report any issues!__*")

    if command.lower() == "leaveguild" and message.author.id == 213247101314924545:
        if not len(args) == 1:
            return await message.channel.send("too many or not enough args")
        guild = client.get_guild(args[0])
        await guild.leave()
        await message.channel.send("Guild left!")

    if command.lower() == "guilds" and message.author.id == 213247101314924545:
        if not len(args) == 0:
            return await message.channel.send("too many or not enough args")
        guilds = [f"{guild.name} ({guild.id})" for guild in client.guilds]
        msg = "\n".join(guilds)
        print(msg)
        await message.channel.send(content=msg)


async def addRole(member: discord.Member, roles: [], use_random_role: bool):
    """
    Function for adding role a role to a user
    member: discord.Member
    roles: array of roles to add
    """
    if use_random_role:
        print("using random role")
        role = random.choice(roles)
        if role in member.roles:
            print(f"{member.name} ({member.id}) already has role {role.name}")
            return
        else:
            try:
                await member.add_roles(role)
                print(f"Added role {role.name} to {member.name} ({member.id})")
            except discord.Forbidden:
                # TODO: send message to general or have a channel setup to set messages?
                print(f"Missing permission to add role {role.name} to user {member.display_name} ({member.id})")
            except discord.HTTPException:
                # TODO: send message to general or have a channel setup to set messages?
                print(f"Failed to add role {role.name} to user {member.display_name} ({member.id})")
    else:
        print("adding all roles")
        for role in roles:
            # make sure the member doesnt already have the role
            if role in member.roles:
                print(f"{member.name} ({member.id}) already has role {role.name}")
                return
            else:
                try:
                    await member.add_roles(role)
                    print(f"Added role {role.name} to {member.name} ({member.id})")
                except discord.Forbidden:
                    # TODO: send message to general or have a channel setup to set messages?
                    print(f"Missing permission to add role {role.name} to user {member.display_name} ({member.id})")
                except discord.HTTPException:
                    # TODO: send message to general or have a channel setup to set messages?
                    print(f"Failed to add role {role.name} to user {member.display_name} ({member.id})")


def getMonth():
    date = datetime.now()
    return date.strftime("%B").upper()


def getDay():
    return datetime.now().day


def getYear():
    return datetime.now().year


def getPreviousMonth():
    today = datetime.today()
    first = today.replace(day=1)
    last_month = first - timedelta(days=1)
    return last_month.strftime("%B").upper()


async def create_roles(guild: discord.Guild, name: str, color: int):
    try:
        role = await guild.create_role(name=name, color=discord.Colour(color))
        print(f"Created role {role.name}")
        return role
    except discord.Forbidden:
        try:
            await guild.owner.send(
                "Sorry to bother you but it seems that I am missing permission to create the proper roles!")
            print("Missing permission to create roles, owner notified.")
        except (discord.Forbidden, discord.HTTPException):
            print("Missing permission to create roles, failed to notify owner.")
    except discord.HTTPException:
        try:
            await guild.owner.send(
                "Sorry to bother you but it seems that I failed to create the proper roles!")
            print("Failed to create roles, owner notified.")
        except (discord.Forbidden, discord.HTTPException):
            print("Failed to create roles, failed to notify owner.")


class TaskTimer:
    def __init__(self, func):
        # self.time = 3600.0
        self.time = 3600.0
        self.function = func
        self.task = asyncio.ensure_future(self.job())

    async def job(self):
        await asyncio.sleep(self.time)
        await self.function()

    def cancel(self):
        self.task.cancel()


if __name__ == "__main__":
    dotenv.load_dotenv()

client.run(os.getenv("TOKEN"))
