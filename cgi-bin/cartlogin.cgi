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
    form = cgi.FieldStorage()
    n_products = int(form.getfirst("n_products"))
    products = [(form.getfirst(f"product_{i}"), form.getfirst(f"quantity_{i}")) for i in range(n_products)]
    user_type = form.getfirst("usertype")
    uname = form.getfirst("username")
    pword = form.getfirst("password")
    if user_type == "individual":
        table = "Individual_T"
    elif user_type == "business":
        table = "Business_T"
    else:
        table = "Staff_T"

    
    password_matches = check_credentials(conn,table,uname,pword)
    if password_matches:
        uid = getUID(conn,table,uname)
        set_cookie(conn, uid)

        #move products from guest session to user shopping cart, delete guest cart
        for prod in products:
            write_cart(conn, uid, prod[0], prod[1])
        delete_cart(conn, "9999999")
        
        print("Content-type:text/html\r\n\r\n")
        print("<html lang=\"en\">")
        print("<head>")
        print("<meta charset=\"UTF-8\">")
        print("<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">")
        print("<meta http-equiv=\"X-UA-Compatible\" content=\"ie=edge\">")
        print("<link rel=\"stylesheet\" href=\"../style.css\">")
        print("<title>Habitat</title>")
        print("</head>")
        print("<h1>Login Successful</h1>")
        print("<h3 class=\"card-title\"><a href=\"products.cgi\" class=\"btn\">Products</a></h3>")
        print("<h3 class=\"card-title\"><a href=\"viewcart.cgi\" class=\"btn\">View Cart</a></h3>")
        print("</html>")
    else:
        print("Content-type:text/html\r\n\r\n")
        login_failure()
main()