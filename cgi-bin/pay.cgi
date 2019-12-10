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
    
    bank, ship, mayor, it = get_accounts_info()
    bank_info = {
        "MyAccount" : bank[0],
        "MyPassword" : bank[1],
        "SendPort" : bank[2],
        "ReceivePort": bank[3],
        "FilePath" : bank[4]
    }

    ship_info = {
        "MyAccount" : ship[0],
        "MyPassword" : ship[1],
        "SendPort" : ship[2],
        "ReceivePort": ship[3],
        "FilePath" : ship[4]
    }

    mayor_info = {
        "MyAccount" : mayor[0],
        "MyPassword" : mayor[1],
        "SendPort" : mayor[2],
        "ReceivePort": mayor[3],
        "FilePath" : mayor[4]
    }

    it_info = {
        "MyAccount" : it[0],
        "MyPassword" : it[1],
        "SendPort" : it[2],
        "ReceivePort": it[3],
        "FilePath" : it[4]
    }

    #[(name,photo,price,quantity, inventory)]
    products = get_cart(conn, uid)
    productIDs = [get_productID(conn,tup[0]) for tup in products]
    prices = [tup[2] for tup in products]
    quantities = [tup[3] for tup in products]
    order_date = str(date.today())
    product_names = [tup[0] for tup in products]
    inventories = [tup[4] for tup in products]

    #initial write to order table (and generates an orderID), delete if order fails
    orderIDs = []
    for i in range(len(productIDs)):
        oid = write_order_table(conn, productIDs[i], uid, quantities[i], shipping_method, card)
        orderIDs.append(oid)
    confirmationIDs = ["020"+str(order) for order in orderIDs]

    all_orders = [
        {
            "OrderID": orderIDs[i], 
            "CustomerID": uid, 
            "ItemID": productIDs[i], 
            "Quantity": quantities[i], 
            "SaleAmount" : prices[i]*quantities[i], 
            "CustomerBank": card, 
            "ShipMethod": shipping_method, 
            "ShipAddress": address
        } for i in range(len(orderIDs))]

    #bank files
    QflagName_b, QnameAtC_b, QnameAtS_b, AflagName_b, AnameAtC_b, AnameAtS_b = flag_names("bank")
     #mayor files
    QflagName_t, QnameAtC_t, QnameAtS_t, AflagName_t, AnameAtC_t, AnameAtS_t = flag_names("mayor")
    #shipping files
    QflagName_s, QnameAtC_s, QnameAtS_s, AflagName_s, AnameAtC_s, AnameAtS_s = flag_names("ship")
     #IT files
    QflagName_i, QnameAtC_i, QnameAtS_i, AflagName_i, AnameAtC_i, AnameAtS_i = flag_names("it")
    
    #myID,mycustomer,mybank,customerbank,itemordered,quantity,totalamount,shipping
    confirmations = []
    for order in all_orders:
        write_to_bank(QnameAtC_b, order["OrderID"], order["SaleAmount"], card, bank_info["MyAccount"], bank_info["MyPassword"], QflagName_b, QnameAtS_b, AflagName_b, AnameAtC_b, AnameAtS_b, bank_info["SendPort"], bank_info["ReceivePort"], bank_info["FilePath"])
        bank_confirmation = get_confirmation(AnameAtC_b)
        if int(bank_confirmation) != 0:
            print("Content-type:text/html\r\n\r\n")
            print("Something's wrong", "bank confirmation says", bank_confirmation)
        else:
            confirmations.append(int(bank_confirmation))

        write_to_taxes(QnameAtC_t, order["OrderID"], order["SaleAmount"], card, mayor_info["MyAccount"], mayor_info["MyPassword"], QflagName_t, QnameAtS_t, AflagName_t, AnameAtC_t, AnameAtS_t, mayor_info["SendPort"], mayor_info["ReceivePort"], mayor_info["FilePath"])
        tax_confirmation = get_confirmation(AnameAtC_t)

        if int(tax_confirmation) != 0:
            print("Content-type:text/html\r\n\r\n")
            print("Something's wrong", "tax confirmation says", tax_confirmation)
        else:
            confirmations.append(int(tax_confirmation))

        write_to_shipping(QnameAtC_s, order["OrderID"], order["ItemID"], order["Quantity"], shipping_method, address, ship_info["MyAccount"], ship_info["MyPassword"], QflagName_s, QnameAtS_s, AflagName_s, AnameAtC_s, AnameAtS_s, ship_info["SendPort"], ship_info["ReceivePort"], ship_info["FilePath"])
        shipping_confirmation = get_confirmation(AnameAtC_s)

        if int(shipping_confirmation) != 0:
            print("Content-type:text/html\r\n\r\n")
            print("Something's wrong", "shipping confirmation says", shipping_confirmation)
        else:
            confirmations.append(int(shipping_confirmation))
        #date in YYYY-MM-DD
        write_to_IT(QnameAtC_i, order["OrderID"], order["ItemID"], order["Quantity"], order["SaleAmount"], card, shipping_method, address, it_info["MyAccount"], it_info["MyPassword"], QflagName_i, QnameAtS_i, AflagName_i, AnameAtC_i, AnameAtS_i, it_info["SendPort"], it_info["ReceivePort"], it_info["FilePath"])
        it_confirmation = get_confirmation(AnameAtC_i)

        if int(it_confirmation) != 0:
            print("Content-type:text/html\r\n\r\n")
            print("Something's wrong", "IT confirmation says", it_confirmation)
        else:
            confirmations.append(int(it_confirmation))
    if 0 in set(confirmations) and len(set(confirmations)) == 1:
        product_quantity = [(prod, quan) for prod, quan in zip(productIDs, quantities)]
        for tup in product_quantity:
            deduct_quantity(conn, tup[0], tup[1])
        for order in zip(orderIDs, confirmationIDs):
            write_confirmations(conn, order[0], order[1])
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

    else:
        for oid in orderIDs:
            remove_unsuccessful_order(conn, oid)
        print("Content-type:text/html\r\n\r\n")
        print("Transaction Failed. Please try again.")
        

        

main()
    

    
