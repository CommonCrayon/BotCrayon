import getData
import sqlite3


# Tries to add a map to the list.
def add_workshopid(userid, username, workshopid):
    descrip = ""
    name = ""
    max_list = 0
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
            
            # Counting how many entries the user has.
            if int(userid) == int(user_testid):
                max_list += 1

            # Checking if the map is in the Database.
            if int(userid) == int(user_testid) and int(workshopid) == int(map_testid):
                redundant_value = 1

    except:
        print("Failed Database check on $add " + str(username))

    try:
        if max_list >= 20:
            answer = ("Maximum Number of Entries Reached.")
            descrip = ("You can only have 20 workshop maps on your list.")
            log = (str(username) + " reached max number of entries, with " + str(workshopid))

        else:
            # If the map was not already added.
            if redundant_value == 0:
                (name, workshop_link, upload, update, thumbnail, filename, time_updated) = getData.get_mapinfo(workshopid)
                filename = filename[-3:]
                
                if filename == "bsp":
                    conn = sqlite3.connect("maplist.db")
                    c = conn.cursor()
                    c.execute("INSERT INTO maplist (userid, mapid, updatetime) VALUES (?, ?, ?)", (userid, workshopid, time_updated))
                    conn.commit()
                    conn.close()

                    answer = (str(name) + " Added")
                    log = str(name) + " Added by " + str(username)
                else:
                    answer = (str(name) + " is not a map.")
                    log = str(username) + " failed to add non-map " + str(name)                

            # If the map was already added.
            if redundant_value == 1:
                (name, workshop_link, upload, update, thumbnail, filename, time_updated) = getData.get_mapinfo(workshopid)

                answer = (str(name) + " is already on your list.")
                log = (str(username) + " tried to add already added map " + str(name))

    except:
        # Tells user that adding the map failed.
        answer = ("Failed to add " + str(workshopid))
        descrip = "Incorrect WorkshopID or Try Again." + "\n" + "(Remember! Only Public Visibility WorkshopIDs Work!)"
        log = (str(username) + " Failed to Add " + str(workshopid))

    return(name, answer, log, descrip)