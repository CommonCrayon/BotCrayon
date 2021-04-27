from datetime import datetime
import sqlite3
import time


# Creating the database for the Map list.
def create_database():
    try:
        conn = sqlite3.connect("maplist.db")
        c = conn.cursor()
        c.execute("""CREATE TABLE IF NOT EXISTS maplist (userid text, mapid text, updatetime integer)""")
        conn.commit()
        c.close()
        print("Created Databases, if they didn't exist.")
    except:
        print("Failed to Create Databases.")



# Update Database after Map Update.
def update_record(time_updated, userid, workshopid):
    try:
        conn = sqlite3.connect("maplist.db")
        c = conn.cursor()
        update = c.execute("UPDATE maplist SET updatetime=? WHERE userid=? AND mapid=?",(time_updated, userid, workshopid),)
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
def delete_record(userid, workshopid):
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



# Gets all of database for Admin.
def master_data():
    try:

        f = open("database.txt","r+")
        f.truncate(0)
        f.close()

        conn = sqlite3.connect("maplist.db")
        c = conn.cursor()
        sqlite_select_query = """SELECT * from maplist"""
        c.execute(sqlite_select_query)
        records = c.fetchall()

        f = open("database.txt", "a")
        f.write("UserID = MapID = UpdateTime || @ " + str(datetime.now()) + "\n")
        f.close()

        for row in records:
            userid = row[0]
            mapid = row[1]
            updatetime = row[2]

            import getData
            (name) = getData.get_mapname(mapid)

            update = time.strftime("%A, %d %B, %Y - %H:%M:%S UTC", time.gmtime(updatetime))

            f = open("database.txt", "a")
            f.write(str(userid) + " = " + str(mapid) + " || " + str(name) + " = " + str(updatetime) + " || " + str(update) + "\n")
            f.close()
        c.close()



    except sqlite3.Error as error:
        print("Failed to read data from sqlite table", error)
    finally:
        if conn:
            conn.close()
            print("SQLite Connection Closed")