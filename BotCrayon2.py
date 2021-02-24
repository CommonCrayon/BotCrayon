import requests
import time
from time import sleep
import sqlite3
import asyncio
from datetime import datetime
import discord
from discord.ext import tasks
from discord.ext.commands import Bot

client = discord.Client()

# Logging Channel ID
log_channel_file = open("log_channel.txt")
channel_log = int(log_channel_file.read())

# Creating the database for the Map list.
def create_database():
    try:
        conn = sqlite3.connect("maplist.db")
        c = conn.cursor()
        c.execute(
            """CREATE TABLE IF NOT EXISTS maplist
                    (userid text, mapid text, updatetime integer)"""
        )
        conn.commit()
        c.close()
        print("Created maplist.db, if it didn't exist.")
    except:
        print("Failed to Create maplist.db.")
    print("\n")


# Getting the time_updated to check whether the map has been updated or not.
def check_time(workshopid, stored_update):
    try:
        payload = {"itemcount": 1, "publishedfileids[0]": [str(workshopid)]}
        r = requests.post(
            "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/",
            data=payload,
        )
        data = r.json()
        time_updated = data["response"]["publishedfiledetails"][0]["time_updated"]
        return time_updated
    except:
        print("Failed to check_time of " + str(workshopid))
        time_updated = stored_update
        return time_updated


# Retriving Map Information.
def get_mapinfo(workshopid):
    try:
        payload = {"itemcount": 1, "publishedfileids[0]": [str(workshopid)]}
        r = requests.post(
            "https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/",
            data=payload,
        )
        data = r.json()
        name = data["response"]["publishedfiledetails"][0]["title"]
        filename = data["response"]["publishedfiledetails"][0]["filename"]
        filename = filename.split("/")[-1]
        mapid = data["response"]["publishedfiledetails"][0]["publishedfileid"]
        time_created = data["response"]["publishedfiledetails"][0]["time_created"]
        upload = time.strftime(
            "%A, %d %B, %Y - %H:%M:%S UTC", time.gmtime(time_created)
        )
        time_updated = data["response"]["publishedfiledetails"][0]["time_updated"]
        update = time.strftime(
            "%A, %d %B, %Y - %H:%M:%S UTC", time.gmtime(time_updated)
        )
        preview_url = data["response"]["publishedfiledetails"][0]["preview_url"]
        thumbnail = preview_url + "/?ima=fit"
        workshop_link = "https://steamcommunity.com/sharedfiles/filedetails/?id=" + str(
            workshopid
        )
        return (
            name,
            workshop_link,
            upload,
            update,
            thumbnail,
            mapid,
            filename,
            time_updated,
        )
    except:
        print("Failed to Get Map Data of " + str(workshopid))


# Retriving Changelog.
def get_changelog(workshopid):
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(
            requests.get(
                "https://steamcommunity.com/sharedfiles/filedetails/changelog/"
                + str(workshopid)
            ).content,
            "html.parser",
        )
        announcements = soup.find(
            "div",
            class_="workshopAnnouncement",
        )
        changelog = announcements.find("p").get_text("\n")
        changelog = changelog[0:1023]
        return changelog
    except:
        print("Failed to Get Changelog of " + str(workshopid))


# Update Database after Map Update.
def update_record(time_updated, userid, mapid):
    try:
        conn = sqlite3.connect("maplist.db")
        c = conn.cursor()
        print("Connected to SQLite")

        update = c.execute(
            "UPDATE maplist SET updatetime=? WHERE userid=? AND mapid=?",
            (time_updated, userid, mapid),
        )
        conn.commit()
        print("Record updated successfully ")
        c.close()

    except sqlite3.Error as error:
        print("Failed to update record from sqlite table", error)
    finally:
        if conn:
            conn.close()
            print("Closed SQLite Connection.")
    print("\n")


# Deleting a record when $remove is used.
def deleteRecord(userid, workshopid):
    try:
        conn = sqlite3.connect("maplist.db")
        c = conn.cursor()
        print("Connected to SQLite")

        delete = c.execute(
            "DELETE FROM maplist WHERE userid=? AND mapid=?",
            (
                userid,
                workshopid,
            ),
        )
        conn.commit()
        print("Record deleted successfully ")
        c.close()

    except sqlite3.Error as error:
        print("Failed to delete record from sqlite table", error)
    finally:
        if conn:
            conn.close()
            print("the sqlite connection is closed")


# Initiating the BotCrayon.
@client.event
async def on_ready():
    print("We have logged in as {0.user}".format(client))
    print("\n")
    game = discord.Game("$help")
    await client.change_presence(status=discord.Status.online, activity=game)


# Checking Updates every 10 minutes.
@tasks.loop(minutes=10.0)
async def check_update():
    try:
        conn = sqlite3.connect("maplist.db")
        c = conn.cursor()
        sqlite_select_query = """SELECT * from maplist"""
        c.execute(sqlite_select_query)
        records = c.fetchall()
        print("Rows: " + str(len(records)) + " Check at: " + str(datetime.now()))

        for row in records:
            userid = row[0]
            workshopid = row[1]
            stored_update = row[2]
            time_updated = check_time(workshopid, stored_update)

            if stored_update == time_updated:
                pass

            else:

                try:
                    (
                        name,
                        workshop_link,
                        upload,
                        update,
                        thumbnail,
                        mapid,
                        filename,
                        time_updated,
                    ) = get_mapinfo(workshopid)
                    changelog = get_changelog(workshopid)

                    embed = discord.Embed(title=name + " Updated!", color=0xFF6F00)
                    embed.url = workshop_link
                    embed.add_field(name="Time Uploaded:", value=upload, inline=False)
                    embed.add_field(name="Time Updated:", value=update, inline=False)
                    embed.add_field(name="Change Log", value=changelog, inline=False)
                    embed.set_image(url=thumbnail)
                    embed.set_footer(
                        text="Map ID: " + mapid + "     " + "File Name: " + filename
                    )

                    user = await client.fetch_user(userid)
                    await user.send(embed=embed)

                    channel = client.get_channel(channel_log)
                    await channel.send(str(name) + " Updated for " + str(userid))

                    print(
                        str(name)
                        + " Updated! Checked on: "
                        + str(datetime.now())
                        + " for "
                        + userid
                    )

                except:
                    print("Failed to send embed update")

                update_record(time_updated, userid, mapid)
        print("Finished Check at: " + str(datetime.now()))
        c.close()

    except:
        print("Failed 10 Minute Update Check.")


# User Commands.
@client.event
async def on_message(message):

    if message.author == client.user:
        return

    # User asking for help.
    if message.content.startswith("$help"):

        userid = message.author.id
        username = message.author

        embed = discord.Embed(
            title="BotCrayon",
            description="I am the Bot of CommonCrayon."
            + "\n"
            + "My main current function is to check for map updates on the CSGO Steam Workshop."
            + "\n"
            + " Please contact CommonCrayon#9275 if you have any issues",
            color=0xFF6F00,
        )
        embed.set_thumbnail(url="https://i.imgur.com/laJnwhg.png")
        embed.add_field(
            name="$add [WorkshopID]",
            value="Adds a workshop map to your update checker list.",
            inline=False,
        )
        embed.add_field(
            name="$remove [WorkshopID]",
            value="Removes a workshop map from your update checker list.",
            inline=False,
        )
        embed.add_field(
            name="$list",
            value="Displays the list of maps you have on your update checker.",
            inline=False,
        )
        embed.add_field(
            name="$search [WorkshopID]",
            value="Searches for a workshop map.",
            inline=False,
        )
        embed.add_field(
            name="$changelog [WorkshopID]",
            value="Displays only the changelog for a workshop map."
            + "\n"
            + "(Can not be larger than 1024 characters)",
            inline=False,
        )
        embed.set_footer(
            text="BotCrayon made by CommonCrayon. Special thanks to Fluffy & Squidski"
        )

        user = await client.fetch_user(userid)
        await user.send(embed=embed)

        channel = client.get_channel(channel_log)
        await channel.send(str(username) + " requested help.")
        print(str(username) + " requested help.")

    # Adding to  Map List.
    if message.content.startswith("$add"):

        workshopid = message.content.strip("$add ")
        userid = message.author.id
        username = message.author

        # Tries to add a map to the list.
        try:
            (
                name,
                workshop_link,
                upload,
                update,
                thumbnail,
                mapid,
                filename,
                time_updated,
            ) = get_mapinfo(workshopid)
            conn = sqlite3.connect("maplist.db")
            c = conn.cursor()
            c.execute(
                "INSERT INTO maplist (userid, mapid, updatetime) VALUES (?, ?, ?)",
                (userid, mapid, time_updated),
            )
            conn.commit()
            conn.close()

            # Tell user that the map was added.
            embed = discord.Embed(title=name + " Added!", color=0xFF6F00)
            print(str(name) + " added by " + str(username))

            # Logs to Dev Channel in Discord.
            channel = client.get_channel(channel_log)
            await channel.send(str(username) + " Added " + str(name))

        except:
            # Tells user that adding the map failed.
            embed = discord.Embed(
                title="Failed to add.",
                description="Incorrect WorkshopID or Try Again.",
                color=0xFF6F00,
            )
            print("Failed to add " + str(workshopid) + " by " + str(username))

            # Logs to Dev Channel in Discord.
            channel = client.get_channel(channel_log)
            await channel.send(str(username) + " Failed to Add " + str(workshopid))

        # Sends the message the user.
        user = await client.fetch_user(userid)
        await user.send(embed=embed)
        print("\n")

    # Removing from Map List.
    if message.content.startswith("$remove"):

        workshopid = message.content.strip("$remove ")
        userid = message.author.id
        username = message.author

        # Tries to remove a map from the list.
        try:
            # Validates whether the WorkshopID exists.
            (
                name,
                workshop_link,
                upload,
                update,
                thumbnail,
                mapid,
                filename,
                time_updated,
            ) = get_mapinfo(workshopid)

            # Sends Confirmation of Removal.
            embed = discord.Embed(title=name + " Removed.", color=0xFF6F00)

            # Removes the record off the database.
            deleteRecord(userid, workshopid)

            # Logs Removal of Map.
            print(str(name) + " removed by " + str(username))
            channel = client.get_channel(channel_log)
            await channel.send(str(username) + " Removed " + str(workshopid))
        except:
            embed = discord.Embed(
                title="Failed to Remove.",
                description="Incorrect WorkshopID or Try Again.",
                color=0xFF6F00,
            )
            print("Failed removal of " + str(workshopid) + " " + str(username))
            channel = client.get_channel(channel_log)
            await channel.send(str(username) + " Failed to Remove  " + str(workshopid))

        # Sends message to user.
        user = await client.fetch_user(userid)
        await user.send(embed=embed)

    # Displays User's Map Update Checker List.
    if message.content.startswith("$list"):

        userid = message.author.id
        username = message.author
        maps = []

        # Getting the List of Maps for the User.
        async def get_list():
            try:
                conn = sqlite3.connect("maplist.db")
                c = conn.cursor()
                sqlite_select_query = """SELECT * from maplist"""
                c.execute(sqlite_select_query)
                records = c.fetchall()

                for row in records:
                    testid = row[0]
                    if int(userid) == int(testid):
                        workshopid = row[1]
                        (
                            name,
                            workshop_link,
                            upload,
                            update,
                            thumbnail,
                            mapid,
                            filename,
                            time_updated,
                        ) = get_mapinfo(workshopid)
                        maps.append(name + " = " + workshopid)
                c.close()

            except sqlite3.Error as error:
                # Incase there's an error.
                print("Failed to read data from sqlite table", error)
            finally:
                if conn:
                    conn.close()
                    print("The SQLite connection is closed")

        await get_list()

        # Creating Message and Embed.
        try:
            # Putting all the maps in a list.
            user_list = ""
            for map in maps:
                user_list += f"{map}\n"

            # Creating Embed.
            embed = discord.Embed(title="Update Checker List", color=0xFF6F00)
            embed.add_field(name="Your List", value=user_list, inline=False)

            # Logs the Retreival of the List.
            print(str(username) + " requested list, containing: ")
            print(maps)
            channel = client.get_channel(channel_log)
            await channel.send(str(username) + " requested list, containing: ")
            await channel.send(str(user_list))

        except:
            # Informs user of error.
            embed = discord.Embed(
                title="List Empty or Failed to Retrieve.", color=0xFF6F00
            )

            # Logs Error.
            print(str(username) + " failed list request.")
            channel = client.get_channel(channel_log)
            await channel.send(str(username) + " failed list request.")

        # Sends message to user.
        user = await client.fetch_user(userid)
        await user.send(embed=embed)

    # Displays only the changelog of the workshopid entered.
    if message.content.startswith("$changelog"):

        workshopid = message.content.strip("$changelog ")
        userid = message.author.id
        username = message.author

        try:
            # Getting Map information and Changelog.
            (
                name,
                workshop_link,
                upload,
                update,
                thumbnail,
                mapid,
                filename,
                time_updated,
            ) = get_mapinfo(workshopid)
            changelog = get_changelog(workshopid)

            # Creating Embed.
            embed = discord.Embed(title=name + " Updated!", color=0xFF6F00)
            embed.url = workshop_link
            embed.add_field(name="Change Log", value=changelog, inline=True)
            embed.set_thumbnail(url=thumbnail)
            embed.set_footer(text="Time Updated: " + update)

            # Logs the use of Changelog.
            print(name + " changelog by " + str(username))
            channel = client.get_channel(channel_log)
            await channel.send(
                "Retrieving Changelog of  " + str(name) + " by " + str(username)
            )

        except:
            # Informs user of error.
            embed = discord.Embed(
                title="Error Retrieving Changelog",
                description="Incorrect WorkshopID or Try Again.",
                color=0xFF6F00,
            )

            # Logs Error.
            print("Failed changelog of " + str(workshopid) + " " + str(username))
            channel = client.get_channel(channel_log)
            await channel.send(
                "Failed Retrieving Changelog of  "
                + str(workshopid)
                + " by "
                + str(username)
            )

        # Sends message to user.
        user = await client.fetch_user(userid)
        await user.send(embed=embed)

    # Searches for Maps using WorkshopID.
    if message.content.startswith("$search"):

        workshopid = message.content.strip("$search ")
        userid = message.author.id
        username = message.author

        try:
            # Getting Map information and Changelog.
            (
                name,
                workshop_link,
                upload,
                update,
                thumbnail,
                mapid,
                filename,
                time_updated,
            ) = get_mapinfo(workshopid)
            changelog = get_changelog(workshopid)

            # Creating Embed.
            embed = discord.Embed(title=name, color=0xFF6F00)
            embed.url = workshop_link
            embed.add_field(name="Time Uploaded:", value=upload, inline=False)
            embed.add_field(name="Time Updated:", value=update, inline=False)
            embed.add_field(name="Change Log", value=changelog, inline=False)
            embed.set_image(url=thumbnail)
            embed.set_footer(
                text="Map ID: " + mapid + "     " + "File Name: " + filename
            )

            # Logs the Search.
            print(str(name) + " Searched by " + str(username))
            channel = client.get_channel(channel_log)
            await channel.send(str(name) + " Searched by " + str(username))

        except:
            # Informs user of error.
            embed = discord.Embed(
                title="Error Searching",
                description="Incorrect WorkshopID or Try Again.",
                color=0xFF6F00,
            )

            # Logs Error.
            print("Error Searching " + str(workshopid) + " by " + str(username))
            channel = client.get_channel(channel_log)
            await channel.send(
                "Error Searching  " + str(workshopid) + " by " + str(username)
            )

        # Sends message to user.
        user = await client.fetch_user(userid)
        await user.send(embed=embed)


# Executing BotCrayon.
create_database()
check_update.start()

# Bot Token
token_file = open("bot_token.txt")
token = token_file.read()
client.run(token)