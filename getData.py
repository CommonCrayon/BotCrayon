
import requests
import time
from datetime import datetime
from datetime import date

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
        
        time_created = data["response"]["publishedfiledetails"][0]["time_created"]
        upload = time.strftime("%A, %d %B, %Y - %H:%M:%S UTC", time.gmtime(time_created))

        time_updated = data["response"]["publishedfiledetails"][0]["time_updated"]
        update = time.strftime("%A, %d %B, %Y - %H:%M:%S UTC", time.gmtime(time_updated))

        preview_url = data["response"]["publishedfiledetails"][0]["preview_url"]
        thumbnail = preview_url + "/?ima=fit"

        workshop_link = "https://steamcommunity.com/sharedfiles/filedetails/?id=" + str(workshopid)

        return (name, workshop_link, upload, update, thumbnail, filename, time_updated)
    except:
        print("Failed to Get Map Data of " + str(workshopid))



# Retriving Map Information.
def get_mapname(workshopid):
    try:
        payload = {"itemcount": 1, "publishedfileids[0]": [str(workshopid)]}
        r = requests.post("https://api.steampowered.com/ISteamRemoteStorage/GetPublishedFileDetails/v1/", data=payload)
        data = r.json()
        name = data["response"]["publishedfiledetails"][0]["title"]
        
        return (name)
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



def get_unlisted(workshopid):
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(requests.get("https://steamcommunity.com/sharedfiles/filedetails/"+ str(workshopid)).content,"html.parser")

        title = soup.find("div", class_="workshopItemTitle")
        name = title.get_text()

        detailStats = soup.find("div", class_="detailsStatsContainerRight")
        idk = detailStats.get_text()
        details = list(idk.split("\n")) 
        
        upload = details[2]
        update = details[3]

        #thumbnail = soup.find("div", class_="workshopItemPreviewImageMain")

        workshop_link = "https://steamcommunity.com/sharedfiles/filedetails/?id=" + str(workshopid)

        return(name, upload, update, workshop_link)

    except:
        print("Failed to get_unlisted of " + str(workshopid))