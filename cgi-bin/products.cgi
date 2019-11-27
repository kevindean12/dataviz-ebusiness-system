#!/var/www/ebusiness/b-f19-02/html/cgi-bin/proj/bin/python3

import cgi, cgitb
from http import cookies
import pymysql as db
from credentials import *
from project_functions import *
import os

def main():
    conn = dbsetup(auth_name, dbpword, dbname)
    products = get_products(conn)
    names = []
    imgsrcs = []
    descriptions = []
    prices = []
    inventories = []
    for d in products:
        names.append(d["Product_Name"])
        imgsrcs.append(d["Photo_Link"])
        descriptions.append(d["Description"])
        prices.append(d["Current_Price"])
        inventories.append(d["Inventory"])
    template = "../products_x.html"
    cookie = cookies.SimpleCookie(os.environ["HTTP_COOKIE"])
    try:
        sessionID = cookie["sessionID"].value
    except Exception as err:
        sessionID = set_cookie(conn)
    uid = get_user_id_from_session(conn, sessionID)
    if int(uid) != 9999999:
        user = get_user(conn, uid)
        output = display_products(template, names, imgsrcs, descriptions, prices, inventories, user)
    else:
        output = display_products(template, names, imgsrcs, descriptions, prices, inventories)
    print("Content-type:text/html\r\n\r\n")
    print(output)


main()