#!/var/www/ebusiness/b-f19-02/html/cgi-bin/proj/bin/python3

import cgi, cgitb
from http import cookies
import pymysql as db
import os
from credentials import *
from project_functions import *

def main():
    conn = dbsetup(auth_name, dbpword, dbname)
    form = cgi.FieldStorage()
    cookie = cookies.SimpleCookie(os.environ["HTTP_COOKIE"])
    try:
        sessionID = cookie["sessionID"].value
    except Exception as err:
        print("Content-type:text/html\r\n\r\n")
        print(err)
    uid = get_user_id_from_session(conn, sessionID)
    if int(uid) != 9999999:
        user = get_user(conn, uid)
        product = form.getfirst("product")
        quantity = form.getfirst("quantity")
        write_cart(conn, uid, product, quantity)
        products = get_products(conn)
        template = "../products_x.html"
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
        output = display_products(template, names, imgsrcs, descriptions, prices, inventories, user)
        print(output)
    else:
        user = "Guest"
        product = form.getfirst("product")
        quantity = form.getfirst("quantity")
        write_cart(conn, uid, product, quantity)
        products = get_products(conn)
        template = "../products_x.html"
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
        output = display_products(template, names, imgsrcs, descriptions, prices, inventories, user)
        print(output)
        # print("<html lang=\"en\">")
        # print("<head>")
        # print("<meta charset=\"UTF-8\">")
        # print("<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">")
        # print("<meta http-equiv=\"X-UA-Compatible\" content=\"ie=edge\">")
        # print("<link rel=\"stylesheet\" href=\"../style.css\">")
        # print("<title>Habitat</title>")
        # print("</head>")
        # print("<h1>Not Logged In</h1>")
        # print("<h3>Please login to add items to your cart, or register for a new account.</h3>")
        # print("<h3 class=\"card-title\"><a href=\"../login.html\" class=\"btn\">Login</a></h3>")
        # print("<h3 class=\"card-title\"><a href=\"../register.html\" class=\"btn\">Register</a></h3>")
        # print("<h3 class=\"card-title\"><a href=\"products.cgi\" class=\"btn\">Products</a></h3>")
        # print("</html>")
    conn.close()
    
print("Content-type:text/html\r\n\r\n")
main()


