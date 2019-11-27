#!/var/www/ebusiness/b-f19-02/html/cgi-bin/proj/bin/python3

import pymysql as db
from credentials import *
from project_functions import *
from subprocess import run

def main():
    conn = dbsetup(auth_name, dbpword, dbname)
    userdata = receive_userdata()
    userdata_split = [row.split(",") for row in userdata]
    
    userdata_d = {
        "SellerID" : [get_businessID(conn, lst[0]) for lst in userdata_split],
        "Buyer_Name" : [lst[1] for lst in userdata_split],
        "Order_Date" : [lst[2] for lst in userdata_split],
        "Item_Ordered" : [lst[3] for lst in userdata_split],
        "Quantity" : [lst[4] for lst in userdata_split],
        "Price" : [lst[5] for lst in userdata_split],
        "Inventory" : [lst[6].replace("\n", "") for lst in userdata_split]
    }

    cost = 0
    for i in range(len(userdata_d["Item_Ordered"])):
        write_user_transaction(
            conn, 
            userdata_d["Item_Ordered"][i], 
            userdata_d["SellerID"][i], 
            userdata_d["Buyer_Name"][i],
            userdata_d["Order_Date"][i],
            userdata_d["Price"][i],
            userdata_d["Quantity"][i],
            userdata_d["Inventory"][i]
            )
        
        cost += 0.1

    customerID = userdata_d["SellerID"][0]
    customer_name = userdata_split[0][0]
    address, card = get_user_info(conn, customerID)

    bank_info = businesses.get("bank")
    bank_order_file = bank_info[0]
    QflagName_b, QnameAtC_b, QnameAtS_b, AflagName_b, AnameAtC_b, AnameAtS_b = flag_names(bank_order_file)
    write_to_bank(QnameAtC_b, customer_name, bank_info[2], bank_info[4], card, cost, QflagName_b, QnameAtS_b, AflagName_b, AnameAtC_b, AnameAtS_b)
    bank_confirmation = get_confirmation(AnameAtC_b)
    if int(bank_confirmation) != 0:
        print("Something's wrong", "bank confirmation says", bank_confirmation)
    
    tax_info = businesses.get("mayor")
    tax_order_file = tax_info[0]
    QflagName_t, QnameAtC_t, QnameAtS_t, AflagName_t, AnameAtC_t, AnameAtS_t = flag_names(tax_order_file)
    write_to_taxes(QnameAtC_t, customer_name, tax_info[2], bank_info[4], card, cost, QflagName_t, QnameAtS_t, AflagName_t, AnameAtC_t, AnameAtS_t)
    tax_confirmation = get_confirmation(AnameAtC_t)
    if int(tax_confirmation) != 0:
        print("Something's wrong", "tax confirmation says", tax_confirmation)
    else:
        tell_server_to_confirm()
    
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



if __name__ == "__main__":
    main()