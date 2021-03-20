
import sqlite3

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