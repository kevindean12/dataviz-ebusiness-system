#!/var/www/ebusiness/b-f19-02/html/cgi-bin/proj/bin/python3

import cgi, cgitb
from http import cookies
import pymysql as db
import os
from credentials import *
from project_functions import *
import math

def main():
    conn = dbsetup(auth_name, dbpword, dbname)
    sessionID, user, uid = get_session_info(conn)
    if int(uid) != 9999999:
        address, card = get_user_info(conn, uid)
        last_four = str(card)[-4:]
        #get cart items from DB
        products = get_cart(conn, uid)
        total_price = math.fsum([tup[2]*tup[3] for tup in products]) + 8
        template = "../checkout_x.html"
        output = display_checkout_info(conn, uid, user, template, total_price, address, last_four)
        print("Content-type:text/html\r\n\r\n")
        print(output)
    else:
        products = get_cart(conn, uid)
        #store tuples of (productName, quantity)
        add_cart = [(f""" <input type="hidden" name="product_{i}" value="{prod[0]}"> """, f""" <input type="hidden" name="quantity_{i}" value="{prod[3]}"> """) for i, prod in enumerate(products)] 
        #tell the cartlogin program how many products it's looking for
        n_products = f""" <input type="hidden" name=n_products value={len(products)}> """
        formstart = """ <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <meta http-equiv="X-UA-Compatible" content="ie=edge">
                    <link rel="stylesheet" href="../style.css">
                    <title>Habitat</title>
                </head>
            <body>
            <form action="cartlogin.cgi" method="POST"> """
        formstart += n_products
        for pair in add_cart:
            formstart += pair[0]
            formstart += pair[1]
        rest_of_form = """ <div>
                <label for="user">Username</label>
                <input type="text" name="username" id="user" class="text-input">
            </div>
            <div>
                <label for="pass">Password</label>
                <input type="password" name="password" id="pass" class="text-input">
            </div>
            <div>
                <h3>Which type of account do you have?</h3>
            </div>
            <div>
                <input type="radio" name="usertype" id="individual" value="individual">
                <label for="individual">Individual</label>
                <input type="radio" name="usertype" id="business" value="business">
                <label for="business">Business</label>
                <input type="radio" name="usertype" id="staff" value="staff">
                <label for="staff">Staff</label>
            </div>
            <div>
                <input class="btn" type="submit" value="Submit">
            </div>  
        </form>
        </body>
        </html> """
        formstart += rest_of_form
        print("Content-type:text/html\r\n\r\n")
        print(formstart)

main()