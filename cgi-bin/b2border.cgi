#!/var/www/ebusiness/b-f19-02/html/cgi-bin/proj/bin/python3

import cgi, cgitb
import pymysql as db
from credentials import *
from project_functions import *
from subprocess import run

def main():
    conn = dbsetup(auth_name, dbpword, dbname)
    form = cgi.FieldStorage()
    team = form.getfirst("teamID")
    port_num = "11" + str(team) + "0"
    product = form.getfirst("productorder")
    quantity = form.getfirst("quantity")

    order_from = businesses.get(port_num)
    order_file = order_from[0]
    uname = order_from[2]
    pwrd = order_from[3]

    #filenames for Client.java command line args:
    QflagName, QnameAtC, QnameAtS, AflagName, AnameAtC, AnameAtS = flag_names(order_file)

    write_order_request(QnameAtC, product, quantity, uname, pwrd, QflagName, QnameAtS, AflagName, AnameAtC, AnameAtS)
    #flag file is named f-{order_file}_confirmation.txt, follow this convention everywhere
    get_confirmation(AnameAtC)

main()
print("Content-type:text/html\r\n\r\n")
print("Done")