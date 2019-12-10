#!/var/www/ebusiness/b-f19-02/html/cgi-bin/proj/bin/python3

import pymysql as db
from credentials import *
from project_functions import *
from subprocess import run

def main():
    conn = dbsetup(auth_name, dbpword, dbname)
    #Format of userdata.txt: OrderID,ItemID,Quantity,SaleAmount,CustomerBankAccount,ShipMethod,ShipAddress,CompanyName,Password,NewInventory
    userdata = receive_userdata()
    userdata_split = [row.split(",") for row in userdata]
    
    userdata_d = {
        "UserOrderID" : [lst[0] for lst in userdata_split],
        "ItemID" : [lst[1] for lst in userdata_split],
        "Quantity": [lst[2] for lst in userdata_split],
        "SaleAmount" : [lst[3] for lst in userdata_split],
        "CustomerBankAccount" : [lst[4] for lst in userdata_split],
        "ShipMethod" : [lst[5] for lst in userdata_split],
        "ShipAddress": [lst[6] for lst in userdata_split],
        "SellerID" : [get_businessID(conn, lst[7]) for lst in userdata_split],
        "SellerPassword" : [lst[8] for lst in userdata_split],
        "Inventory" : [lst[9].replace("\n", "") for lst in userdata_split]
        # "SellerID" : [get_businessID(conn, lst[7]) for lst in userdata_split],
        # "Buyer_Name" : [lst[1] for lst in userdata_split],
        # "Order_Date" : [lst[2] for lst in userdata_split],
        # "Item_Ordered" : [lst[3] for lst in userdata_split],
        # "Quantity" : [lst[4] for lst in userdata_split],
        # "SaleAmount" : [lst[5] for lst in userdata_split],
        # "Inventory" : [lst[6].replace("\n", "") for lst in userdata_split]
    }

    cost = 0
    for i in range(len(userdata_d["ItemID"])):
        write_user_transaction(conn, userdata_d["UserOrderID"][i], userdata_d["ItemID"][i], userdata_d["SellerID"][i], userdata_d["SaleAmount"][i], userdata_d["Quantity"][i], userdata_d["ShipMethod"][i], userdata_d["Inventory"][i])
        cost += 0.1

    customerID = userdata_d["SellerID"][0]
    customer_name = userdata_split[0][7]
    address, card = get_user_info(conn, customerID)
    quantity = cost/0.1

    orderID = write_order_table(conn, "6111105", customerID, quantity, "Digital", card)

    tell_server_to_confirm()

    bank, ship, mayor, it = get_accounts_info()
    bank_info = {
        "MyAccount" : bank[0],
        "MyPassword" : bank[1],
        "SendPort" : bank[2],
        "ReceivePort": bank[3],
        "FilePath" : bank[4]
    }

    mayor_info = {
        "MyAccount" : mayor[0],
        "MyPassword" : mayor[1],
        "SendPort" : mayor[2],
        "ReceivePort": mayor[3],
        "FilePath" : mayor[4]
    }

    QflagName_b, QnameAtC_b, QnameAtS_b, AflagName_b, AnameAtC_b, AnameAtS_b = flag_names("bank")
    QflagName_t, QnameAtC_t, QnameAtS_t, AflagName_t, AnameAtC_t, AnameAtS_t = flag_names("mayor")

    write_to_bank(QnameAtC_b, orderID, cost, card, bank_info["MyAccount"], bank_info["MyPassword"], QflagName_b, QnameAtS_b, AflagName_b, AnameAtC_b, AnameAtS_b, bank_info["SendPort"], bank_info["ReceivePort"], bank_info["FilePath"])
    bank_confirmation = get_confirmation(AnameAtC_b)
    if int(bank_confirmation) != 0:
        print("Something's wrong", "bank confirmation says", bank_confirmation)
    
    write_to_taxes(QnameAtC_t, orderID, cost, card, mayor_info["MyAccount"], mayor_info["MyPassword"], QflagName_t, QnameAtS_t, AflagName_t, AnameAtC_t, AnameAtS_t, mayor_info["SendPort"], mayor_info["ReceivePort"], mayor_info["FilePath"])
    tax_confirmation = get_confirmation(AnameAtC_t)
    if int(tax_confirmation) != 0:
        print("Something's wrong", "tax confirmation says", tax_confirmation)
        remove_unsuccessful_order(conn, orderID)
    else:
        receiptID = "021" + str(orderID)
        deduct_quantity(conn, "6111105", quantity)
        tell_server_to_confirm(receiptID)
    
    #seems a little too meta to track IT storage microtransactions as transactions
    #saving this just in case
    # it_info = businesses.get("IT")
    # it_order_file = it_info[0]
    # QflagName_i, QnameAtC_i, QnameAtS_i, AflagName_i, AnameAtC_i, AnameAtS_i = flag_names(it_order_file)
    # order_date = str(date.today())
    # write_to_IT(QnameAtC_i, customer_name, it_info[2], order_date, ["data storage microtransaction"], quantities, prices, inventories, QflagName_i, QnameAtS_i, AflagName_i, AnameAtC_i, AnameAtS_i)
    # it_confirmation = get_confirmation(AnameAtC_i)
    # if int(it_confirmation) != 0:
    #     print("Content-type:text/html\r\n\r\n")
    #     print("Something's wrong", "IT confirmation says", it_confirmation)

    conn.close()



main()