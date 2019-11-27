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
    address, card = get_user_info(conn, uid)
    last_four = str(card)[-4:]
    #get cart items from DB
    products = get_cart(conn, uid)
    total_price = math.fsum([tup[2]*tup[3] for tup in products]) + 8
    template = "../checkout_x.html"
    output = display_checkout_info(conn, uid, user, template, total_price, address, last_four)
    print(output)

print("Content-type:text/html\r\n\r\n")
main()