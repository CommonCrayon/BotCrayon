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

# Steam Api Key
steamkey_file = open("steamkey.txt")
SteamApiKey = str(steamkey_file.read())



# Creating the database for the Map list.
def create_database():
    try:
        conn = sqlite3.connect("maplist.db")
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS maplist (userid text, mapid text, updatetime integer)""")
        conn.commit()
        c.close()
        print("Created maplist.db, if it didn't exist.")
    except:
        print("Failed to Create maplist.db.")



# Getting the time_updated to check whether the map has been updated or not.
def check_time(workshopid, stored_update):
    try:
        payload = {"itemcount": 1, "publishedfileids[0]": [str(workshopid)]}
        r = requests.post("https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/", data=payload)
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
        r = requests.post("https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/", data=payload)
        data = r.json()

        name = data["response"]["publishedfiledetails"][0]["title"]

        filename = data["response"]["publishedfiledetails"][0]["filename"]
        filename = filename.split("/")[-1]

        mapid = data["response"]["publishedfiledetails"][0]["publishedfileid"]

        time_created = data["response"]["publishedfiledetails"][0]["time_created"]
        upload = time.strftime("%A, %d %B, %Y - %H:%M:%S UTC", time.gmtime(time_created))

        time_updated = data["response"]["publishedfiledetails"][0]["time_updated"]
        update = time.strftime("%A, %d %B, %Y - %H:%M:%S UTC", time.gmtime(time_updated))

        preview_url = data["response"]["publishedfiledetails"][0]["preview_url"]
        thumbnail = preview_url + "/?ima=fit"

        workshop_link = "https://steamcommunity.com/sharedfiles/filedetails/?id=" + str(workshopid)

        return (name, workshop_link, upload, update, thumbnail, mapid, filename, time_updated)
    except:
        print("Failed to Get Map Data of " + str(workshopid))



# Retriving Changelog.
def get_changelog(workshopid):
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(requests.get("https://steamcommunity.com/sharedfiles/filedetails/changelog/"+ str(workshopid)).content,"html.parser")
        announcements = soup.find("div", class_="workshopAnnouncement")

        changelog = announcements.find("p").get_text("\n")
        changelog = changelog[0:1023]

        if changelog == "":
            changelog = str("Changelog was empty.")
        
        return changelog
    except:
        print("Failed to get changelog of " + str(workshopid))



# Update Database after Map Update.
def update_record(time_updated, userid, mapid):
    try:
        conn = sqlite3.connect("maplist.db")
        c = conn.cursor()
        update = c.execute("UPDATE maplist SET updatetime=? WHERE userid=? AND mapid=?",(time_updated, userid, mapid),)
        conn.commit()
        c.close()
        print("Record updated successfully.")

    except sqlite3.Error as error:
        print("Failed to update record from sqlite table", error)
    finally:
        if conn:
            conn.close()
            print("Closed SQLite Connection.")



# Deleting a record when $remove is used.
def deleteRecord(userid, workshopid):
    try:
        conn = sqlite3.connect("maplist.db")
        c = conn.cursor()
        delete = c.execute("DELETE FROM maplist WHERE userid=? AND mapid=?", (userid, workshopid,))
        conn.commit()
        c.close()
        print("Record deleted successfully.")

    except sqlite3.Error as error:
        print("Failed to delete record from sqlite table ", error)
    finally:
        if conn:
            conn.close()
            print("Closed SQLite Connection.")



# Tries to add a map to the list.
def add_workshopid(userid, username, workshopid):
    descrip = ""
    name = ""
    try:
        conn = sqlite3.connect("maplist.db")
        c = conn.cursor()
        sqlite_select_query = """SELECT * from maplist"""
        c.execute(sqlite_select_query)
        records = c.fetchall()
        redundant_value = 0

        for row in records:
            user_testid = row[0]
            map_testid = row[1]
            # Checking if the map is in the Database.
            if int(userid) == int(user_testid) and int(workshopid) == int(map_testid):
                redundant_value = 1

    except:
        print("Failed Database check on $add " + str(username))

    try:
        # If the map was not already added.
        if redundant_value == 0:
            (name, workshop_link, upload, update, thumbnail, mapid, filename, time_updated) = get_mapinfo(workshopid)
            conn = sqlite3.connect("maplist.db")
            c = conn.cursor()
            c.execute("INSERT INTO maplist (userid, mapid, updatetime) VALUES (?, ?, ?)", (userid, mapid, time_updated))
            conn.commit()
            conn.close()

            answer = (str(name) + " Added")
            log = str(name) + " Added by " + str(username)

        # If the map was already added.
        if redundant_value == 1:
            (name, workshop_link, upload, update, thumbnail, mapid, filename, time_updated) = get_mapinfo(workshopid)

            answer = (str(name) + " is already on your list.")
            log = (str(username) + " tried to add already added map " + str(name))


    except:
        # Tells user that adding the map failed.

        answer = ("Failed to add " + str(workshopid))
        descrip = "Incorrect WorkshopID or Try Again." + "\n" + "(Remember! Only Public Visibility WorkshopIDs Work!)"
        log = (str(username) + " Failed to Add " + str(workshopid))

    return(name, answer, log, descrip)


# Initiating the BotCrayon.
@client.event
async def on_ready():
    print("We have logged in as {0.user}".format(client))
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
                    (name, workshop_link, upload, update, thumbnail, mapid, filename, time_updated) = get_mapinfo(workshopid)
                    print("Api Request Successful")

                    changelog = get_changelog(workshopid)
                    print("Changelog Request Successful")

                    # Creates Embed for Update Message
                    embed = discord.Embed(title=name + " Updated!", color=0xFF6F00)
                    embed.url = (workshop_link)
                    embed.add_field(name="Time Uploaded:", value=upload, inline=False)
                    embed.add_field(name="Time Updated:", value=update, inline=False)
                    embed.add_field(name="Change Log", value=changelog, inline=False)
                    embed.set_image(url=thumbnail)
                    embed.set_footer(text="Map ID: " + mapid + "     " + "File Name: " + filename)
                    print("Embed Creation Successful")

                    # Sends Update Message to User
                    user = await client.fetch_user(userid)
                    await user.send(embed=embed)

                    # Updates Database
                    update_record(time_updated, userid, mapid)

                    # Logs Update
                    channel = client.get_channel(channel_log)
                    await channel.send(str(name) + " Updated for " + str(userid))
                    print(str(name) + " Updated! Checked on: " + str(datetime.now()) + " for " + userid)

                except:
                    print("Failed to send embed update of " + str(workshopid) + " for " + str(userid))

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

        user = await client.fetch_user(userid)
        botPending = await user.send(":gear: Processing Request, This might take a few seconds. :gear: ")

        # $help Embed.
        embed = discord.Embed(title="BotCrayon",
            description="I am the Bot of CommonCrayon." + "\n"
            + "My main current function is to check for map updates on the CSGO Steam Workshop." + "\n"
            + " Please contact CommonCrayon#9275 for issues.", color=0xFF6F00)
        embed.set_thumbnail(url="https://i.imgur.com/laJnwhg.png")

        # $add
        embed.add_field(name="$add [WorkshopID]",
            value="Adds a workshop map to your update checker list." + "\n"
            + "(Only Public Visibility WorkshopIDs Work!)", inline=False)
        
        # $remove
        embed.add_field(name="$remove [WorkshopID]", value="Removes a workshop map from your update checker list.", inline=False)

        # $purge
        embed.add_field(name="$purge", value="Removes ALL workshop maps from your update checker list.", inline=False)

        # $list
        embed.add_field(name="$list", value="Displays the list of maps you have on your update checker.", inline=False)

        # $search
        embed.add_field(name="$search [WorkshopID] or [SearchText]", value="Searches for a workshop map.", inline=False)

        # $changelog
        embed.add_field(name="$changelog [WorkshopID]", value="Displays only the changelog for a workshop map." + "\n"
            + "(Can not be larger than 1024 characters)", inline=False)
        
        # $collection
        embed.add_field(name="$collection [CollectionID]", value="Displays a whole workshop Collection." + "\n"
            + "(Collections with more than 40 maps will be trimmed.)", inline=False)

        # $collectionadd
        embed.add_field(name="$collectionadd [CollectionID]", value="Adds a whole workshop Collection to your update checker list." + "\n"
            + "(Collections with more than 20 maps will be trimmed.)", inline=False)
        
        # Footer
        embed.set_footer(text="BotCrayon made by CommonCrayon. Special thanks to Fluffy & Squidski")

        # Sends Message
        user = await client.fetch_user(userid)
        await user.send(embed=embed)
        await botPending.delete()

        # Logs Use
        channel = client.get_channel(channel_log)
        await channel.send(str(username) + " requested help.")
        print(str(username) + " requested help.")
        return



    # Adding to  Map List.
    if message.content.startswith("$add"):

        workshopid = message.content[5:]
        userid = message.author.id
        username = message.author

        user = await client.fetch_user(userid)
        botPending = await user.send(":gear: Processing Request, This might take a few seconds. :gear: ")

        (name, answer, log, descrip) = add_workshopid(userid, username, workshopid)

        embed = discord.Embed(title=answer,description=descrip, color=0xFF6F00)

        # Sends the message the user.
        user = await client.fetch_user(userid)
        await user.send(embed=embed)
        await botPending.delete()

        # Logs Process
        print(log)
        channel = client.get_channel(channel_log)
        await channel.send(log)
        return



    # Removing from Map List.
    if message.content.startswith("$remove"):

        workshopid = message.content[8:]
        userid = message.author.id
        username = message.author
        integer_check = workshopid.isdecimal()

        user = await client.fetch_user(userid)
        botPending = await user.send(":gear: Processing Request, This might take a few seconds. :gear: ")


        # Tries to remove a map from the list.
        async def get_remove():
            try:
                conn = sqlite3.connect("maplist.db")
                c = conn.cursor()
                sqlite_select_query = """SELECT * from maplist"""
                c.execute(sqlite_select_query)
                records = c.fetchall()

                # Setting this embed incase we find nothing in the database when searching.
                embed = discord.Embed(title="Failed to Remove.", description="WorkshopID is not on your List.", color=0xFF6F00)

                if integer_check == True:
                    for row in records:
                        user_testid = row[0]
                        map_testid = row[1]
                        try:
                            # Checking if the map is in the Database.
                            if int(userid) == int(user_testid) and int(workshopid) == int(map_testid):
                                # Checking if the map is Public on the Workshop.
                                try:
                                    (name, workshop_link, upload, update, thumbnail, mapid, filename, time_updated) = get_mapinfo(workshopid)

                                    # Sends Confirmation of Removal.
                                    embed = discord.Embed(title=name + " Removed.", color=0xFF6F00)

                                    # Logs Removal of Map.
                                    print(str(name) + " removed by " + str(username))
                                    channel = client.get_channel(channel_log)
                                    await channel.send(str(username) + " Removed " + str(workshopid))

                                # When the map is not Public on the Workshop.
                                except:
                                    # Sends Confirmation of Removal.
                                    embed = discord.Embed(title=workshopid + " Removed.", color=0xFF6F00)

                                    # Logs Removal of Map.
                                    print(str(workshopid) + " removed by " + str(username))
                                    channel = client.get_channel(channel_log)
                                    await channel.send(str(username) + " Removed " + str(workshopid))

                                # Removes the record off the database.
                                deleteRecord(userid, workshopid)

                        except:
                            embed = discord.Embed(title="Failed to Remove.", description="Incorrect WorkshopID or Try Again.", color=0xFF6F00)

                            print("Failed removal of " + str(workshopid) + " " + str(username))
                            channel = client.get_channel(channel_log)
                            await channel.send(str(username) + " Failed to Remove " + str(workshopid))
                else:
                    embed = discord.Embed(title="Failed to Remove.", description=str(workshopid) + " is not a WorkshopID.", color=0xFF6F00)
                    
                    print("Failed removal of " + str(workshopid) + " " + str(username))
                    channel = client.get_channel(channel_log)
                    await channel.send(str(username) + " Failed to Remove " + str(workshopid))

            except:
                print("Failed get_remove function for " + str(username))

            # Sends message to user.
            user = await client.fetch_user(userid)
            await user.send(embed=embed)
            await botPending.delete()

        await get_remove()
        return



    # Initial Purge Embed
    if message.content.startswith("$purge"):
        userid = message.author.id
        username = message.author

        embed = discord.Embed(title="Use '$confirm purge' to confirm purge",description="Remember this will remove all maps!", color=0xFF6F00)

        user = await client.fetch_user(userid)
        await user.send(embed=embed)  

        print(str(username) + " Requested Initial Purge.")
        channel = client.get_channel(channel_log)
        await channel.send(str(username) + " Requested Initial Purge.")     
        return 

        
    # Remove all the maps from the list
    if message.content.startswith("$confirm purge"):
        userid = message.author.id
        username = message.author
        empty = True
        user = await client.fetch_user(userid)
        botPending = await user.send(":gear: Processing Request, This might take a few seconds. :gear: ")

        try:
            conn = sqlite3.connect("maplist.db")
            c = conn.cursor()
            sqlite_select_query = """SELECT * from maplist"""
            c.execute(sqlite_select_query)
            records = c.fetchall()

            for row in records:
                testid = row[0]
                if int(userid) == int(testid):
                    empty = False
                        
            if empty == False:
                for row in records:
                    delete = c.execute("DELETE FROM maplist WHERE userid=?", (userid,))

                    embed = discord.Embed(title="Purged successfully", color=0xFF6F00)
        
                print(str(username) + " Purged successfully")
                channel = client.get_channel(channel_log)
                await channel.send(str(username) + " Purged successfully")

            else:
                embed = discord.Embed(title="Failed Purged",description="List is already empty!", color=0xFF6F00) 

                print(str(username) + " Tried Purge, but list is already empty")
                channel = client.get_channel(channel_log)
                await channel.send(str(username) + " Tried Purge, but list is already empty")             
            
            conn.commit()
            c.close()

        except sqlite3.Error as error:
            print(str(username) +  " Failed to delete record from sqlite table ", error)
            embed = discord.Embed(title="Failed Purged",description="Try Again!", color=0xFF6F00)

            print(str(username) + " Failed Purge.")
            channel = client.get_channel(channel_log)
            await channel.send(str(username) + " Failed Purge.")                 
        finally:
            if conn:
                conn.close()
                print("Closed SQLite Connection.")

        # Sends the message.
        user = await client.fetch_user(userid)
        await user.send(embed=embed)        
        await botPending.delete()
        return
    


    # Displays User's Map Update Checker List.
    if message.content.startswith("$list"):

        userid = message.author.id
        username = message.author
        maps = []

        user = await client.fetch_user(userid)
        botPending = await user.send(":gear: Processing Request, This might take a few seconds. :gear: ")

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
                    try:
                        if int(userid) == int(testid):
                            workshopid = row[1]
                            (name, workshop_link, upload, update, thumbnail, mapid, filename, time_updated) = get_mapinfo(workshopid)
                            maps.append(name + " = " + workshopid)
                    except:
                        maps.append("**WorkshopID is not Public = " + workshopid + "**")
                c.close()

            except sqlite3.Error as error:
                print("Failed to read data from sqlite table", error)
            finally:
                if conn:
                    conn.close()
                    print("SQLite Connection Closed")
        await get_list()

        # Creating Message and Embed.
        try:
            # Putting all the maps in a list.
            user_list = ""
            for map in maps:
                user_list += f"{map}\n"

            # Creating Embed.
            if user_list == "":
                user_list = str("Your List is Empty." + "\n" + "Add a Map by $add [WorkshopID]")

            embed = discord.Embed(title="Update Checker List", description=user_list, color=0xFF6F00)

            # Logs the Retreival of the List.
            print(str(username) + " Requested list")
            channel = client.get_channel(channel_log)
            await channel.send(str(username) + " requested list, containing: ")
            await channel.send(str(user_list))

        except:
            # Informs user of error.
            embed = discord.Embed(title="Failed to Retrieve. Try Again Later.", color=0xFF6F00)

            # Logs Error.
            print(str(username) + " failed list request.")
            channel = client.get_channel(channel_log)
            await channel.send(str(username) + " failed list request.")

        # Sends message to user.
        user = await client.fetch_user(userid)
        await user.send(embed=embed)
        await botPending.delete()
        return



    # Displays only the changelog of the workshopid entered.
    if message.content.startswith("$changelog"):

        workshopid = message.content[11:]
        userid = message.author.id
        username = message.author

        user = await client.fetch_user(userid)
        botPending = await user.send(":gear: Processing Request, This might take a few seconds. :gear: ")

        try:
            # Getting Map information and Changelog.
            (name, workshop_link, upload, update, thumbnail, mapid, filename, time_updated) = get_mapinfo(workshopid)
            changelog = get_changelog(workshopid)

            # Creating Embed.
            embed = discord.Embed(title=name, color=0xFF6F00)
            embed.url = workshop_link
            embed.add_field(name="Change Log", value=changelog, inline=True)
            embed.set_thumbnail(url=thumbnail)
            embed.set_footer(text="Time Updated: " + update)

            # Logs the use of Changelog.
            print(name + " changelog by " + str(username))
            channel = client.get_channel(channel_log)
            await channel.send("Retrieving Changelog of " + str(name) + " by " + str(username))

        except:
            # Informs user of error.
            embed = discord.Embed(title="Error Retrieving Changelog", description="Incorrect WorkshopID or Try Again.", color=0xFF6F00)

            # Logs Error.
            print("Failed changelog of " + str(workshopid) + " " + str(username))
            channel = client.get_channel(channel_log)
            await channel.send("Failed Retrieving Changelog of " + str(workshopid) + " by " + str(username))

        # Sends message to user.
        user = await client.fetch_user(userid)
        await user.send(embed=embed)
        await botPending.delete()
        return



    # Searches for Maps using WorkshopID.
    if message.content.startswith("$search"):

        workshopid = message.content[8:]
        integer_check = workshopid.isdecimal()
        userid = message.author.id
        username = message.author

        user = await client.fetch_user(userid)
        botPending = await user.send(":gear: Processing Request, This might take a few seconds. :gear: ")

        # If the search is for a workshopID
        if integer_check == True:
            try:
                # Getting Map information and Changelog.
                (name, workshop_link, upload, update, thumbnail, mapid, filename, time_updated) = get_mapinfo(workshopid)
                changelog = get_changelog(workshopid)

                # Creating Embed.
                embed = discord.Embed(title=name, color=0xFF6F00)
                embed.url = workshop_link
                embed.add_field(name="Time Uploaded:", value=upload, inline=False)
                embed.add_field(name="Time Updated:", value=update, inline=False)
                embed.add_field(name="Change Log", value=changelog, inline=False)
                embed.set_image(url=thumbnail)
                embed.set_footer(text="Map ID: " + mapid + "     " + "File Name: " + filename)

                # Logs the Search.
                print(str(name) + " Searched by " + str(username))
                channel = client.get_channel(channel_log)
                await channel.send(str(name) + " Searched by " + str(username))

            except:
                # Informs user of error.
                embed = discord.Embed(title="Error Searching", description="Incorrect WorkshopID or Try Again.", color=0xFF6F00)

                # Logs Error.
                print("Error Searching " + str(workshopid) + " by " + str(username))
                channel = client.get_channel(channel_log)
                await channel.send("Error Searching " + str(workshopid) + " by " + str(username))
        
        # If the search is for a keyword
        else:
            increment = 1
            page = 1
            end_loop = 1
            searchmaps = []
            query = ""

            try:
                # Checks total number
                url = "https://api.steampowered.com/IPublishedFileService/QueryFiles/v1/"
                payload = {"key": (SteamApiKey), "query_type": 0, "page": increment, "appid":730, "search_text": (workshopid), "totalonly": True}
                response = requests.get(url, payload)
                data = response.json()
                total = data["response"]["total"]

                if total == 0:
                    # Creates Embed
                    embed = discord.Embed(title="Results for: " + str(workshopid), description=str("No Results Found"), color=0xFF6F00)
                    embed.url = ("https://steamcommunity.com/workshop/browse/?appid=730&searchtext=" + str(workshopid))
                    
                    # Logs Search
                    print(str(username) + " Searched for " + str(workshopid))
                    channel = client.get_channel(channel_log)
                    await channel.send(str(username) + " Searched for " + str(workshopid))

                else:
                    while increment <= 3:
                        url = "https://api.steampowered.com/IPublishedFileService/QueryFiles/v1/"
                        payload = {"key": (SteamApiKey), "query_type": 0, "page": increment, "appid":730, "search_text": (workshopid)}
                        response = requests.get(url, payload)
                        data = response.json()
                        result = data["response"]["publishedfiledetails"][0]["publishedfileid"]

                        (name, workshop_link, upload, update, thumbnail, mapid, filename, time_updated) = get_mapinfo(result)
                        filename = filename[-3:]

                        if filename == "bsp":
                            searchmaps.append("**" + name  + " = "  + result + "**" + "\n" + workshop_link)
                            increment += 1

                        end_loop += 1
                        page += 1
                        if end_loop == 10:
                            increment = 4

                    for searchmap in searchmaps:
                        query += f"{searchmap}\n"

                    # Creates Embed
                    embed = discord.Embed(title="Results for: " + str(workshopid), description=str(query), color=0xFF6F00)
                    embed.url = ("https://steamcommunity.com/workshop/browse/?appid=730&searchtext=" + str(workshopid))
                    embed.set_footer(text=str(total) + " Results Found")

                    # Logs Search
                    print(str(username) + " Searched for " + str(workshopid))
                    channel = client.get_channel(channel_log)
                    await channel.send(str(username) + " Searched for " + str(workshopid))

            except:
                embed = discord.Embed(title="Failed Search For: " + str(workshopid), description="Try Again", color=0xFF6F00)

                # Logs Error
                print(str(username) + " Failed Search for " + str(workshopid))
                channel = client.get_channel(channel_log)
                await channel.send(str(username) + " Failed Search for " + str(workshopid))

        # Sends message to user.
        user = await client.fetch_user(userid)
        await user.send(embed=embed)
        await botPending.delete()
        return



    # Adds Collection to the Update Checker List using CollectionID.
    if message.content.startswith("$collectionadd"):

        collection_input = message.content[15:]
        userid = message.author.id
        username = message.author

        user = await client.fetch_user(userid)
        botPending = await user.send(":gear: Processing Request, This might take a few seconds. :gear: ")

        footer_display = False
        url_display = False
        collection_embed = []
        print("\n" + str(username) + " Adding Collection " + str(collection_input))

        # Getting Collection Name
        try:
            payload = {"itemcount": 1, "publishedfileids[0]": [str(collection_input)]}
            r = requests.post("https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/", data=payload)
            data = r.json()
            collection_name = data["response"]["publishedfiledetails"][0]["title"]
        except:
            collection_name = "Collection Map List"

        try:
            payload = {"collectioncount": 1, "publishedfileids[0]": [str(collection_input)]}
            r = requests.post("https://api.steampowered.com/ISteamRemoteStorage/GetCollectionDetails/v1/", data=payload)
            data = r.json()
            collectionmaps = data["response"]["collectiondetails"][0]["children"]
            collectionids = [child["publishedfileid"] for child in collectionmaps]
            collection = []

            url_display = True

            if len(collectionids) > 20:
                collectionids = collectionids[:20]
                footer_display = True
                
            for collectionid in collectionids:
                workshopid = collectionid
                try:
                    (name, answer, log, descrip) = add_workshopid(userid, username, workshopid)
                    collection_embed.append(answer + " " + descrip + "\n")
                    print(answer)

                except:
                    collection_embed.append("Failed to add " + str(collectionid))
     
        except:
            print(str(username) + " Failed to add collection " + str(collection_input))
            collection_name = ("Failed to add collection " + str(collection_input))
            collection_result = ("I don't know, something fucked up.")

        collection_result = ""
        for stuff in collection_embed:
            collection_result += f"{stuff}"

        if url_display == False:
            collection_result = ("Incorrect CollectionID or Try Again")

        embed = discord.Embed(title=collection_name, description=collection_result, color=0xFF6F00)

        if url_display == True:
            embed.url = ("https://steamcommunity.com/sharedfiles/filedetails/?id=" + str(collection_input))

        if footer_display == True:
            embed.set_footer(text="(Only the first 20 Maps will be added.) ")

        # Sends the message the user.
        user = await client.fetch_user(userid)
        await user.send(embed=embed)
        await botPending.delete()

        # Logs Process
        print(str(username) + " Added Collection " + str(collection_input) + "\n")
        channel = client.get_channel(channel_log)
        await channel.send(str(username) + " Attempted to Add Collection " + str(collection_input))
        return



    # Searches for Collection using WorkshopID.
    if message.content.startswith("$collection"):

        workshopid = message.content[12:]
        userid = message.author.id
        username = message.author

        user = await client.fetch_user(userid)
        botPending = await user.send(":gear: Processing Request, This might take a few seconds. :gear: ")

        try:

            payload = {"collectioncount": 1, "publishedfileids[0]": [str(workshopid)]}
            r = requests.post("https://api.steampowered.com/ISteamRemoteStorage/GetCollectionDetails/v1/", data=payload)
            data = r.json()
            collectionmaps = data["response"]["collectiondetails"][0]["children"]
            collectionids = [child["publishedfileid"] for child in collectionmaps]
            collection = []

            # Getting Collection Name
            try:
                payload = {"itemcount": 1, "publishedfileids[0]": [str(workshopid)]}
                r = requests.post("https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/", data=payload)
                data = r.json()
                collection_name = data["response"]["publishedfiledetails"][0]["title"]
            except:
                collection_name = "Collection Map List"

            i = 0
            for collectionid in collectionids:
                try:
                    (name, workshop_link, upload, update, thumbnail, mapid, filename, time_updated) = get_mapinfo(collectionids[i])
                except:
                    name = "UNKNOWN"
                collection.append(str(name) + " = "  + str(collectionids[i]))
                i += 1

            entries = len(collection) 

            collection_list = ""
            for map in collection:
                collection_list += f"{map}\n"
            collection_list = collection_list[0:1023]

            # Creates Embed
            embed = discord.Embed(title=collection_name, description=collection_list, color=0xFF6F00)
            embed.url = ("https://steamcommunity.com/sharedfiles/filedetails/?id=" + str(workshopid))
            if entries > 35:
                embed.set_footer(text="Warning! Approximately only 40 maps can be displayed")

            # Logs Usage
            print(str(username) + " Retrieved Collection " + str(collection_name) + " of " + str(workshopid))
            channel = client.get_channel(channel_log)
            await channel.send(str(username) + " Retrieved Collection " + str(collection_name) + " of " + str(workshopid))

        except:
            # Created Embed
            embed = discord.Embed(title="Failed to Retrieve Collection", description="Incorrect CollectionID or Try Again", color=0xFF6F00)

            # Logs Usage
            print(str(username) + " Failed Collection Request " + str(workshopid))
            channel = client.get_channel(channel_log)
            await channel.send(str(username) + " Failed Collection Request " + str(workshopid))

        user = await client.fetch_user(userid)
        await user.send(embed=embed)
        await botPending.delete()
        return



# Executing BotCrayon.
create_database()
check_update.start()

# Bot Token
token_file = open("bot_token.txt")
token = token_file.read()
client.run(token)