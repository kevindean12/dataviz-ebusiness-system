#!/var/www/ebusiness/b-f19-02/html/cgi-bin/proj/bin/python3

import cgi, cgitb
from http import cookies
import pymysql as db
import os
from credentials import *
from project_functions import *

def main():
    expire_cookie()
    print("Content-type:text/html\r\n\r\n")
    print("<html lang=\"en\">")
    print("<head>")
    print("<meta charset=\"UTF-8\">")
    print("<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">")
    print("<meta http-equiv=\"X-UA-Compatible\" content=\"ie=edge\">")
    print("<link rel=\"stylesheet\" href=\"../style.css\">")
    print("<title>Habitat</title>")
    print("</head>")
    print("<h1>Logout Successful</h1>")
    print("<h3 class=\"card-title\"><a href=\"../index.html\" class=\"btn\">Home</a></h3>")
    print("<h3 class=\"card-title\"><a href=\"products.cgi\" class=\"btn\">Products</a></h3>")
    print("</html>")

def expire_cookie():
    cookie = cookies.SimpleCookie()
    cookie["sessionID"] = ""
    cookie["sessionID"]["expires"] = "1 Jan 1970 00:00:00 UTC"
    print(cookie)

main()
    