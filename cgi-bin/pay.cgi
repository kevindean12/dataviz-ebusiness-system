#!/var/www/ebusiness/b-f19-02/html/cgi-bin/proj/bin/python3

import cgi, cgitb
from http import cookies
import pymysql as db
import os
from datetime import date
from credentials import *
from project_functions import *

def main():
    conn = dbsetup(auth_name, dbpword, dbname)
    sessionID, user, uid = get_session_info(conn)
    address, card = get_user_info(conn, uid)
    form = cgi.FieldStorage()

    expedited_shipping = form.getfirst("expedited_shipping")
    total_price = form.getfirst("total_price")
    if expedited_shipping == "True":
        shipping_method = "Expedited"
    else:
        shipping_method = "Standard"
    
    #bank_info: (filebase, customername, myname, mypassword, myaccount)
    bank_info = businesses.get("bank")
    bank_order_file = bank_info[0]
    QflagName_b, QnameAtC_b, QnameAtS_b, AflagName_b, AnameAtC_b, AnameAtS_b = flag_names(bank_order_file)
    #[(name,photo,price,quantity, inventory)]
    products = get_cart(conn, uid)
    
    #myID,mycustomer,mybank,customerbank,itemordered,quantity,totalamount,shipping
    write_to_bank(QnameAtC_b, user, bank_info[2], bank_info[4], card, total_price, QflagName_b, QnameAtS_b, AflagName_b, AnameAtC_b, AnameAtS_b)
    bank_confirmation = get_confirmation(AnameAtC_b)
    
    if int(bank_confirmation) != 0:
        print("Content-type:text/html\r\n\r\n")
        print("Something's wrong", "bank confirmation says", bank_confirmation)
    
    tax_info = businesses.get("mayor")
    tax_order_file = tax_info[0]
    QflagName_t, QnameAtC_t, QnameAtS_t, AflagName_t, AnameAtC_t, AnameAtS_t = flag_names(tax_order_file)

    write_to_taxes(QnameAtC_t, user, tax_info[2], bank_info[4], card, total_price, QflagName_t, QnameAtS_t, AflagName_t, AnameAtC_t, AnameAtS_t)
    tax_confirmation = get_confirmation(AnameAtC_t)

    if int(tax_confirmation) != 0:
        print("Content-type:text/html\r\n\r\n")
        print("Something's wrong", "tax confirmation says", tax_confirmation)
    
    shipping_info = businesses.get("shipping")
    ship_order_file = shipping_info[0]
    QflagName_s, QnameAtC_s, QnameAtS_s, AflagName_s, AnameAtC_s, AnameAtS_s = flag_names(ship_order_file)

    productIDs = [get_productID(conn,tup[0]) for tup in products]
    prices = [tup[2] for tup in products]
    quantities = [tup[3] for tup in products]

    write_to_shipping(QnameAtC_s, user, shipping_info[2], bank_info[4], card, productIDs, quantities, prices, shipping_method, QflagName_s, QnameAtS_s, AflagName_s, AnameAtC_s, AnameAtS_s)
    shipping_confirmation = get_confirmation(AnameAtC_s)

    if int(tax_confirmation) != 0:
        print("Content-type:text/html\r\n\r\n")
        print("Something's wrong", "shipping confirmation says", shipping_confirmation)

    it_info = businesses.get("IT")
    it_order_file = it_info[0]
    QflagName_i, QnameAtC_i, QnameAtS_i, AflagName_i, AnameAtC_i, AnameAtS_i = flag_names(it_order_file)

    order_date = str(date.today())
    product_names = [tup[0] for tup in products]
    inventories = [tup[4] for tup in products]
    #date in YYYY-MM-DD
    write_to_IT(QnameAtC_i, user, it_info[2], order_date, product_names, quantities, prices, inventories, QflagName_i, QnameAtS_i, AflagName_i, AnameAtC_i, AnameAtS_i)
    it_confirmation = get_confirmation(AnameAtC_i)

    if int(it_confirmation) != 0:
        print("Content-type:text/html\r\n\r\n")
        print("Something's wrong", "IT confirmation says", it_confirmation)
    else:
        for i in range(len(productIDs)):
            write_order_table(conn, productIDs[i], sessionID, quantities[i], shipping_method, card)
        product_quantity = [(prod, quan) for prod, quan in zip(productIDs, quantities)]
        for tup in product_quantity:
            deduct_quantity(conn, tup[0], tup[1])
        delete_cart(conn, sessionID)

        receipt_table = create_receipt(conn, uid)

        print("Content-type:text/html\r\n\r\n")
        print("<html lang=\"en\">")
        print("<head>")
        print("<meta charset=\"UTF-8\">")
        print("<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">")
        print("<meta http-equiv=\"X-UA-Compatible\" content=\"ie=edge\">")
        print("<link rel=\"stylesheet\" href=\"../style.css\">")
        print("<title>Habitat</title>")
        print("</head>")
        print("<h1>Transaction complete</h1>")
        print("<h3 class=\"card-title\"><a href=\"../index.html\" class=\"btn\">Home</a></h3>")
        print(receipt_table)
        print("</html>")

print("Content-type:text/html\r\n\r\n")
main()
    

    
