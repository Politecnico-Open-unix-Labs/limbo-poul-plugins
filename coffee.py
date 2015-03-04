"""!coffee <command> controls the coffee maker. Available commands:
	*please* : makes you a coffee :)
	*list* : view the credit situation (_warning_: tags everyone that has positive credit)
	*set <nick> <amount>* : sets the credit counter for <nick> to <amount> (_warning_: works only for admins)
	*gift <nick> <gift_amount>* : gifts the user <nick> with <gift_amount> credits (_warning_: you must have those credits :P )"""
import json
import re
import serial
import time
import sqlite3 as lite
import thread

class CoffeeDB:
    def __init__(self):
        try:
            self.con = lite.connect('coffee.db')
            self.cur = self.con.cursor()    
            self.cur.execute("CREATE TABLE IF NOT EXISTS Coffee(nickname TEXT PRIMARY KEY, coins INTEGER)")
            self.con.commit()
        except lite.Error, e:
            if self.con:
                self.con.rollback()
            print("Error %s" % e.args[0])
            raise SystemExit
    
    def getCredit(self, nickname):
        self.cur.execute("SELECT coins FROM Coffee WHERE nickname=:Nick", 
                        {"Nick": nickname})
        rows = list(self.cur.fetchall())
        if len(rows) == 0:
            self.createUser(nickname)
            return self.getCredit(nickname)
        else:
            return rows[0][0]

    def setCredit(self, nickname, value):
        #if the user do not exists create it. then set his credit
        self.getCredit(nickname)
        self.cur.execute("UPDATE Coffee SET coins=:CoinValue WHERE nickname=:Nick", 
                        {"Nick": nickname, "CoinValue" : int(value)})
        self.con.commit()

    def createUser(self, nickname):
        self.cur.execute("INSERT INTO Coffee(nickname, coins) VALUES (:Nick, 0)",
                        {"Nick": nickname})
        self.con.commit()

    def deleteUser(self, nickname):
        self.cur.execute("DELETE FROM Coffee WHERE nickname=:Nick",
                        {"Nick": nickname})
        self.con.commit()

    def getCreditList(self):
        self.cur.execute("SELECT * FROM Coffee")
        self.con.commit()
        return list(self.cur.fetchall())

class CoffeeMachine:
    """
    Object representing and controlling the coffee machine
    """
    def __init__(self, serialDevice = "/dev/ttyUSB0"):
        self.serobj = serial.Serial(serialDevice)
        self.stop()

    def start(self):
        """
        Start coffee dispensing
        """
        self.serobj.setDTR(True)

    def stop(self):
        """
        Stop coffee dispensing
        """
        self.serobj.setDTR(False)

def get_coffee_balance(db):
    """Gets the current balance of coffees"""
    #fetch from the db the list of users with balance > 0
    result = "".join([r[0] + ": " + str(r[1]) + "\n" for r in db.getCreditList() if r[1]>0])
    if not result:
        return u"Nobody has credit :("
    else:
        return u"{0}".format(result)

def make_real_coffee(coffee_time):
    c = CoffeeMachine()
    c.start()
    time.sleep(coffee_time)
    c.stop()

def do_coffee(nick, state, db):
    """Makes a coffee!"""
    #let's check two people aren't making coffee at the same time    
    if not "doing_coffee" in state:
        state["doing_coffee"] = time.time()
    else:
        if state["doing_coffee"]+40 > time.time(): 
            return u"Whoops! Wait for your turn please."
        else: state["doing_coffee"] = time.time()

    #check if the user has credit. if it is the case, -- on it
    if db.getCredit(nick) <= 0:
        return u"Are you sure you do have credit? ;)"
    db.setCredit(nick, db.getCredit(nick) - 1)
    
    #make a coffee through usb
    thread.start_new_thread(make_real_coffee, (25,))

    #warn the user
    return u"{0} I am making your coffee :)".format(nick)

def admin_credit(admin, nick, new_credit, db):
    if admin["is_admin"] or admin["name"] == u"otacon22":
        nick = nick.lower()
        db.setCredit(nick, new_credit)
        return u"New credit for {0} is {1}".format(nick, new_credit)

def gift_credit(user, nick, credit_gifted, db):
    try:
        credit_gifted = int(credit_gifted)
    except:
        return u"Sir, please! Insert a number."

    if db.getCredit(user["name"]) >= credit_gifted:
        nick = nick.lower()
        db.setCredit(user["name"], db.getCredit(user["name"]) - credit_gifted)
        db.setCredit(nick, db.getCredit(nick) + credit_gifted)
        return u"New credit for {0} is {1}".format(nick, db.getCredit(nick))
    else: return u"Sir! You *must* have those credits ;)"

def on_message(msg, server):
    text = msg["text"]
    match = re.findall(r"!coffee (.*)", text)
    if not match: return

    #dear db, we are going to talk.
    db = CoffeeDB()

    user = server["client"].server.users.get(msg["user"])

    if u"please" in match[0]:
        #get the real user
        return do_coffee(user["name"], server["config"], db)
    elif u"reset" in match[0]:
        nick = match[0].split("reset ")[1] #syntax: "!coffee reset $nick"
        return admin_credit(user, nick, 0, db)
    elif u"set" in match[0]:
        nick, amount = match[0].split("set ")[1].split() #syntax: "!coffee set $nick $amount"
        return admin_credit(user, nick, amount, db)
    elif u"gift" in match[0]:
        nick, amount = match[0].split("gift ")[1].split() #syntax: "!coffee gift $nick $amount"
        return gift_credit(user, nick, amount, db)
    elif u"add" in match[0]:
        nick, amount = match[0].split("add ")[1].split() #syntax: "!coffee add $nick $amount"
        return admin_credit(user, nick, db.getCredit(nick.lower())+int(amount), db)
    elif u"list" in match[0]:
        return get_coffee_balance(db)
    return
