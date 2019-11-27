#!/var/www/ebusiness/b-f19-02/html/cgi-bin/proj/bin/python3

import cgi, cgitb
from http import cookies
import pymysql as db
import os
from credentials import *
from project_functions import *
import math

def main():
    form = cgi.FieldStorage()
    conn = dbsetup(auth_name, dbpword, dbname)
    sessionID, user, uid = get_session_info(conn)
    
    ship = form.getfirst("shipping_method")
    if ship == "standard":
        shipping_price = 8
    else:
        shipping_price = 14
    
    confirm_addr = form.getfirst("address")
    confirm_bank = form.getfirst("bank_number")
    confirm_last_four = confirm_bank[-4:]

    address, card = get_user_info(conn, uid)
    last_four = str(card)[-4:]

    if confirm_addr != address:
        update_user_address(conn, uid, confirm_addr)
    
    if confirm_last_four != last_four:
        update_user_bank(conn, uid, confirm_bank)

    products = get_cart(conn, uid)
    total_price = math.fsum([tup[2]*tup[3] for tup in products]) + shipping_price

    template = "../checkout_x.html"
    if ship == "expedited":
        output = display_checkout_info(conn, uid, user, template, total_price, address, last_four, expedited=True)
    else:
        output = display_checkout_info(conn, uid, user, template, total_price, address, last_four)
    print(output)

print("Content-type:text/html\r\n\r\n")
main()
    
    