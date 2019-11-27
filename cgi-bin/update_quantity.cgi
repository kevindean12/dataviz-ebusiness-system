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
    new_quantity = form.getfirst("new_quantity")
    product_to_update = form.getfirst("product_update")
    productID = get_productID(conn, product_to_update)
    cookie = cookies.SimpleCookie(os.environ["HTTP_COOKIE"])
    try:
        sessionID = cookie["sessionID"].value
    except Exception as err:
        print("Content-type:text/html\r\n\r\n")
        print(err)
    uid = get_user_id_from_session(conn, sessionID)
    if int(uid) != 9999999:
        user = get_user(conn, uid)
    else:
        user = "Guest"
    if int(new_quantity) == 0:
        remove_from_cart(conn, productID, uid)
    else:
        update_quantity(conn, new_quantity, uid, productID)
    template = "../cart_x.html"
    try:
        print("<h3>Quantity updated!</h3>")
        print(display_cart(conn, uid, user, template))
    except Exception as err:
        print("Content-type:text/html\r\n\r\n")
        print(err)
    conn.close()
print("Content-type:text/html\r\n\r\n")
main()