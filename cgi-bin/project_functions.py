import cgi, cgitb
from http import cookies
import pymysql as db
import os
from subprocess import run
import secrets
from argon2 import PasswordHasher

#TODO update this dict with real business' port numbers
#format: port_num : filename(no extension), business' username, my username w/ that business, my password for that business
businesses = { 
    "11020" : ("order", "Habitat", "deank", "habitat"),
    }

def create_receipt(conn, sessionID):
    sql = "SELECT OrderID, Item_Ordered, Quantity, Shipping_Method FROM Order_T WHERE UserID = %s"
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (sessionID))
            response = cursor.fetchall()
    except Exception as err:
        print("Content-type:text/html\r\n\r\n") #TODO testing only
        print(err)
    orderIDs = [d["OrderID"] for d in response]
    items = [d["Item_Ordered"] for d in response]
    quantities = [d["Quantity"] for d in response]
    ships = [d["Shipping_Method"] for d in response]
    html = """<table id="receipt">
    <caption>Your orders</caption>
    <thead>
        <tr>
            <th scope="col">Order Number</th>
            <th scope="col">Item</th>
            <th scope="col">Quantity</th>
            <th scope="col">Shipping Method</th>
        </tr>
    </thead>
    <tbody>"""
    for i in range(len(orderIDs)):
        html = html + f"""<tr>
        <td>{orderIDs[i]}</td>
        <td>{items[i]}</td>
        <td>{quantities[i]}</td>
        <td>{ships[i]}</td>
        </tr>"""
    html = html + """</tbody </table>"""
    return html

def dbsetup(usr, pwd, schema):
    """
    Sets up pymysql connection to MySQL database
    usr: username
    pwd: password
    schema: which database to use
    returns conn, a pymysql connection object
    """
    conn = db.connect(
        user=usr,
        password=pwd,
        db=schema,
        charset="utf8mb4",
        cursorclass=db.cursors.DictCursor
    )
    return conn

def deduct_quantity(conn, productID, deduct_how_much):
    current_quantity_sql = "SELECT Inventory, Number_Sold FROM Product_T WHERE ProductID = %s"
    try:
        with conn.cursor() as cursor:
            cursor.execute(current_quantity_sql, (productID))
            response = cursor.fetchone()
    except Exception as err:
        print("Content-type:text/html\r\n\r\n") #TODO testing only
        print(err)
    old_inventory = int(response["Inventory"])
    if response["Number_Sold"] == None:
        old_sales = 0
    else:
        old_sales = int(response["Number_Sold"])
    new_inventory = old_inventory - int(deduct_how_much)
    new_sales = old_sales + int(deduct_how_much)
    sql = "UPDATE Product_T SET Inventory = %s, Number_Sold = %s WHERE ProductID = %s"
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (new_inventory, new_sales, productID))
            conn.commit()
    except Exception as err:
        print("Content-type:text/html\r\n\r\n") #TODO testing only
        print(err)

def delete_cart(conn, userID):
    sql = "DELETE FROM Shopping_Cart_T WHERE UserID = %s"
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (userID))
            conn.commit()
    except Exception as err:
        print("Content-type:text/html\r\n\r\n") #TODO testing only
        print(err)

def display_cart(conn, userID, user, template):
    html = listify_file(template)
    sql = "SELECT Product_Name, Photo_Link, Current_Price, Quantity FROM Shopping_Cart_T INNER JOIN Product_T ON Shopping_Cart_T.ProductID = Product_T.ProductID WHERE UserID = %s"
    total_price = 0
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (userID))
            response = cursor.fetchall()
    except Exception as err:
        print("Content-type:text/html\r\n\r\n") #TODO testing only
        print(err)
    products = [(d["Product_Name"], d["Photo_Link"], d["Current_Price"], d["Quantity"]) for d in response]
    for line in html:
        if "putuserinfo" in line:
            i = html.index(line)
            html.insert(i+1, f"<div class=\"cart-title\">{user}\'s Cart</div>")
        if "putcartitem" in line:
            j = html.index(line)
            if len(products) == 0:
                html.insert(j+1,
                f"""<div class="cart-item">
                    <span>Your cart is empty!</span>
                </div>""" 
                )
            for tup in products:
                product, photo, price, quantity = tup
                total_price += price*quantity
                html.insert(j+1,
                f"""<div class="cart-item">
                    <div class="cart-btns">
                        <span class="delete-btn"></span>
                    </div>
                    <div class="cart-img">
                        <img src="{photo}" alt="">
                    </div>
                    <div class="cart-item-description">
                        <span>{product}</span>
                    </div>
                    <div class="cart-item-quantity">
                        <form action="update_quantity.cgi" method="POST">
                            <input type="number" name="new_quantity" id="quantity" value="{quantity}">
                            <input type="hidden" name="product_update" id="prod_update" value="{product}">
                            <button type="submit" class="btn">
                                Update Quantity
                            </button>
                        </form>
                        <form action="update_quantity.cgi" method="POST">
                            <input type="hidden" name="new_quantity" id="quantity" value="0">
                            <input type="hidden" name="product_update" id="prod_update" value="{product}">
                            <button type="submit" class="btn">
                                Remove
                            </button>
                        </form>
                        <div class="cart-item-price">${price*quantity}</div>
                    </div>
                </div>""")
                j+=1
            html.insert(j+1, f"""<div class="cart-item-price">Total Price ${total_price}</div>""")
    returnstr = ""
    returnstr = returnstr.join(html)
    return returnstr

def display_checkout_info(conn, userID, user, template, total_price, address, last_four, expedited=False):
    html = listify_file(template)
    sql = "SELECT Product_Name, Photo_Link, Current_Price, Quantity FROM Shopping_Cart_T INNER JOIN Product_T ON Shopping_Cart_T.ProductID = Product_T.ProductID WHERE UserID = %s"
    if expedited:
        expedited_checked = "checked"
        standard_checked = ""
    else:
        expedited_checked = ""
        standard_checked = "checked"
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (userID))
            response = cursor.fetchall()
    except Exception as err:
        print("Content-type:text/html\r\n\r\n") #TODO testing only
        print(err)
    products = [(d["Product_Name"], d["Photo_Link"], d["Current_Price"], d["Quantity"]) for d in response]
    for line in html:
        if "putcartitem" in line:
            j = html.index(line)
            if len(products) == 0:
                html.insert(j+1,
                f"""<div class="cart-item">
                    <span>Your cart is empty!</span>
                </div>""" 
                )
            for tup in products:
                product, photo, price, quantity = tup
                html.insert(j+1,
                f"""<div class="cart-item">
                    <div class="cart-btns">
                        <span class="delete-btn"></span>
                    </div>
                    <div class="cart-img">
                        <img src="{photo}" alt="">
                    </div>
                    <div class="cart-item-description">
                        <span>{product}</span>
                    </div>
                    <div class="cart-item-quantity">
                        Quantity: {quantity}
                        <div class="cart-item-price">${price*quantity}</div>
                    </div>
                </div>""")
                j+=1
            html.insert(j+1, f"""<div class="cart-item-price">Total Price ${total_price}</div>""")
        if "putcheckoutinfo" in line:
            k = html.index(line)
            html.insert(k+1, f"""<form action="update_checkout.cgi" method="POST">
                <div>
                    <p>Please select shipping method:</p>
                </div>
                <div>
                    <input type="radio" name="shipping_method" id="standard" value="standard" {standard_checked}>
                    <label for="standard">Standard - $8</label>
                    <input type="radio" name="shipping_method" id="expedited" value="expedited" {expedited_checked}>
                    <label for="expedited">Expedited - $14</label>
                </div>
                <div>
                    <label for="bank">Bank Number</label>
                    Please enter your full bank number if the last four digits do not match
                    your desired method of payment.
                    <input type="text" name="bank_number" id="bank" class="text-input" value="xxxxxxxxxxxx{last_four}">
                </div>
                <div>
                    <label for="addr">Shipping Address</label>
                    <input type="text" name="address" id="addr" class="text-input" value="{address}">
                </div>
                <div>
                    <input class="btn" type="submit" value="Update Information">
                </div>
            </form>
            <form action="pay.cgi" method="post">
                <input type="hidden" name="total_price" value="{total_price}">
                <input type="hidden" name="expedited_shipping" value="{expedited}">
                <div>
                    <h2>If the information above is correct, please click Submit Payment.</h2>
                    <input class="btn" type="submit" value="Submit Payment">
                </div>
            </form>
            """)
    returnstr = ""
    returnstr = returnstr.join(html)
    return returnstr

def display_products(template_file, names, imgsrcs, descriptions, prices, inventories, user=None):
    """
    Prints an HTML response showing the current products available.
    template_file: a string containing the relative path and filename of the html template file
    user: string, username to display on the page
    names: list of product names from DB for display
    imgsrcs: list of relative paths to a photo for the product
    descriptions: list of brief textual descriptions of the product
    prices: list of the current price for each product
    inventories: list of how many of each product are still available (only displays if below 5)
    num_on_page: which place in the template grid to place the product in range [1,6]
    returns string of the contents of the template html with the product information inserted
    """
    html = listify_file(template_file)
    if len({len(names), len(imgsrcs), len(descriptions), len(prices), len(inventories)}) != 1:
        raise ListMismatchError
    for i in range(len(names)):
        num_on_page = i+1
        for line in html:
            if f"putproduct{num_on_page}" in line:
                j = html.index(line)
                if int(inventories[i]) != 0:
                    html.insert(j+1,
                    f"<h2>{names[i]}</h2>\n <h3>${prices[i]}</h3>\n <img id=\"product-img\" src=\"{imgsrcs[i]}\"><form action=\"shoppingcart.cgi\" method=\"POST\"><input type=\"number\" name=\"quantity\" value=\"1\"><input type=\"hidden\" name=\"product\" value=\"{names[i]}\"><input type=\"submit\" class=\"btn\" value=\"Add to Cart\"></form><p>{descriptions[i]}</p>"
                    )
                else:
                    html.insert(j+1,
                    f"<h2>{names[i]}</h2>\n <h3>Out of stock!</h3>\n <img id=\"product-img\" src=\"{imgsrcs[i]}\">"
                    )
    if user != None:
        for line in html:
            if "putuserinfo" in line:
                k = html.index(line)
                html.insert(k+1, f"<h2>Welcome, {user}</h2>")
    returnstr = ""
    returnstr = returnstr.join(html)
    return returnstr

def flag_names(order_file):
    QflagName = f"f-Q-{order_file}.txt"
    QnameAtC = f"Q-{order_file}.txt"
    QnameAtS = f"Q-{order_file}_s.txt"
    AflagName = f"f-A-{order_file}.txt"
    AnameAtC = f"A-{order_file}.txt"
    AnameAtS = f"A-{order_file}_s.txt"
    return QflagName, QnameAtC, QnameAtS, AflagName, AnameAtC, AnameAtS

def get_businessID(conn, business_name):
    sql = "SELECT BusinessID FROM Business_T WHERE Business_Name = %s"
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (business_name))
            response = cursor.fetchone()
            businessID = response["BusinessID"]
            return businessID
    except Exception as err:
        print(err)

def get_all_data(conn):
    sql = "SELECT DISTINCT Product_Name, Sale_Amount, Quantity, Shipping_Method FROM User_Transaction_T INNER JOIN User_Product_T ON User_Transaction_T.ProductID = User_Product_T.ProductID"
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            response = cursor.fetchall()
            return response
    except Exception as err:
        print("Content-type:text/html\r\n\r\n") 
        print(err)

def get_transaction_data(conn):
    sql = "SELECT SellerID, Sale_Amount from User_Transaction_T"
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            response = cursor.fetchall()
            return response
    except Exception as err:
        print("Content-type:text/html\r\n\r\n") 
        print(err)

def get_business_data(conn, businessID):
    sql = "SELECT DISTINCT Product_Name, Sale_Amount, Quantity, Shipping_Method FROM User_Transaction_T INNER JOIN User_Product_T ON User_Transaction_T.ProductID = User_Product_T.ProductID WHERE User_Transaction_T.SellerID = %s"
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (businessID))
            response = cursor.fetchall()
            return response
    except Exception as err:
        print("Content-type:text/html\r\n\r\n") 
        print(err)

def get_cart(conn, userID):
    """Gets shopping cart items from the user's ID.
    Returns: products, a list of tuples.
    """
    sql = "SELECT Product_Name, Photo_Link, Current_Price, Quantity, Inventory FROM Shopping_Cart_T INNER JOIN Product_T ON Shopping_Cart_T.ProductID = Product_T.ProductID WHERE UserID = %s"
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (userID))
            response = cursor.fetchall()
    except Exception as err:
        print("Content-type:text/html\r\n\r\n") #TODO testing only
        print(err)
    products = [(d["Product_Name"], d["Photo_Link"], d["Current_Price"], d["Quantity"], d["Inventory"]) for d in response]
    return products

def get_confirmation(answer_file):
    """Waits for a flag file to have the value 1
    and reads its contents when it does."""
    while True:
        flag = open(f"../files/f-{answer_file}")
        try:
            if flag.read() != 1:
                pass
        except Exception as err:
            print("Content-type:text/html\r\n\r\n")
            print(str(err))
            break
        else:
            with open(f"../files/{answer_file}") as data:
                answer = data.readline()
                answer = answer.replace("\n","")
                #data == 0 means good, 1 means no account, 2 means not enough money
                #TODO testing only
                # with open("../files/test_confirmation.txt", "w") as test_confirm:
                #     test_confirm.write(answer)
            with open(f"../files/f-{answer_file}", "w") as update_flag:
                update_flag.write("0")
            flag.close()
            return answer
#orderID,theirCustomerID,itemID,quantity,saleAmt,customerBank,shipMethod,shipAddress
def get_accounts_info():
    with open("../files/comAccounts.txt") as fin:
        accounts = fin.readlines()
    bank = accounts[0].split(",")
    ship = accounts[1].split(",")
    mayor = accounts[2].split(",")
    it = accounts[3].split(",")
    return bank, ship, mayor, it

def get_products(conn):
    """
    Queries the database for all current product information.
    Returns: a list of dictionaries (one dict for each row with col:value pairs) 
    Example return (with one row): 
    [{"Product_Name": "WiFi Router", "Current_Price": 15.00, "Inventory":12}]
    """
    sql = "SELECT Product_Name, Photo_Link, Description, Current_Price, Inventory FROM Product_T WHERE ProductID != 6111105"
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            response = cursor.fetchall()
    except Exception as err:
        print("Content-type:text/html\r\n\r\n") #TODO testing only
        print(err)
    return response

def get_productID(conn, product_name):
    """Returns the productID for a product given its name"""
    sql = "SELECT ProductID FROM Product_T WHERE Product_Name = %s"
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (product_name))
            response = cursor.fetchone()
            productID = response["ProductID"]
            return productID
    except Exception as err:
        print("Content-type:text/html\r\n\r\n") #TODO testing only
        print(err)    

def get_session_info(conn):
    """Checks HTTP_COOKIE environment variable set by Apache 
    for sessionID and username.
    Returns: sessionID and username; (None, None) if there is no sessionID in the
    cookie.
    """
    cookie = cookies.SimpleCookie(os.environ["HTTP_COOKIE"])
    try:
        sessionID = cookie["sessionID"].value
    except Exception as err:
        print("Content-type:text/html\r\n\r\n")
        print(err)
    uid = get_user_id_from_session(conn, sessionID)
    user = get_user(conn, uid)
    return sessionID, user, uid

def get_user(conn, userID):
    """Get the username that matches a user's ID.
    returns: a string, the username
    """
    if int(userID)//1000000 == 1:
        col = "Business_Name"
        sql = "SELECT Business_Name FROM Business_T WHERE BusinessID = %s"
    elif int(userID) == 9999999:
        username = "Guest"
        return username
    else:
        col = "Username"
        sql = "SELECT Username FROM Individual_T WHERE UserID = %s"
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (userID))
            response = cursor.fetchone()
    except Exception as err:
        print("Content-type:text/html\r\n\r\n") #TODO testing only
        print(err)
    username = response[col]
    return username

def get_user_id_from_session(conn, sessionID):
    sql = "SELECT UserID from Session_T WHERE SessionID = %s"
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (sessionID))
            response = cursor.fetchone()
    except Exception as err:
        print("Content-type:text/html\r\n\r\n") #TODO testing only
        print(err)
    return response["UserID"]

def get_user_info(conn, userID):
    if int(userID)//1000000 != 2:
        table = "Business_T"
        idtype = "BusinessID"
        sql = "SELECT Address, Debit_Card FROM Business_T WHERE BusinessID = %s"
    else:
        table = "Individual_T"
        idtype = "UserID"
        sql = "SELECT Address, Debit_Card FROM Individual_T WHERE UserID = %s"
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (userID))
            response = cursor.fetchone()
    except Exception as err:
        print("Content-type:text/html\r\n\r\n") #TODO testing only
        print(err)
    address = response["Address"]
    card = response["Debit_Card"]
    return address, card

def listify_file(filename):
    """
    Converts a text document to a list of strings.
    filename: name of a text-based file
    returns list of strings (one string per line in the file)
    """
    with open(filename) as fin:
        content = fin.readlines()
    return content 



class ListMismatchError(Exception):
    """
    You provided lists that are not the same length
    in a place where the lengths must match.
    """
    pass

def receive_userdata():
    """Accept data about a user's business transaction to be stored for later visualization.
    Format of userdata.txt: OrderID,ItemID,Quantity,SaleAmount,CustomerBankAccount,ShipMethod,ShipAddress,CompanyName,Password,NewInventory
    """
    while True:
        flag = open(f"../files/f-userdata.txt")
        try:
            if flag.read() != 1:
                pass
        except Exception as err:
            print(err)
            break
        else:
            with open(f"../files/userdata.txt") as fin:
                data = fin.readlines()
            with open(f"../files/f-userdata.txt", "w") as wflag:
                wflag.write("0")
            flag.close()
            break
    return data

def remove_from_cart(conn, productID, userID):
    sql = "DELETE FROM Shopping_Cart_T WHERE ProductID = %s AND UserID = %s"
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (productID, userID))
        conn.commit()
    except Exception as err:
        print("Content-type:text/html\r\n\r\n")
        print(err)

def remove_unsuccessful_order(conn, orderID):
    sql = "DELETE FROM Order_T WHERE OrderID = %s"
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (orderID))
        conn.commit()
    except Exception as err:
        print("Content-type:text/html\r\n\r\n")
        print(err)

def set_cookie(conn, uid=None):
    #set cookies
    #Python cookies: http://cgi.tutorial.codepoint.net/set-the-cookie
    #https://docs.python.org/3.6/library/http.cookies.html
    sessionID = secrets.randbelow(9999999)
    cookie = cookies.SimpleCookie()
    if uid != None:
        #update user's sessionID in Session_T
        session_update(conn, uid, sessionID)
        # #if unsuccessful, try one more time
        # if not updated:
        #         sessionID = secrets.randbelow(99999999)
        #         try:
        #             updated = session_update(conn, uid, sessionID)
        #             #if still unsuccessful, there's a problem, raise exception
        #             if not updated:
        #                 raise SessionIdError("SessionID cannot be updated.")
        #         except SessionIdError as err:
        #             print("Content-type:text/html\r\n\r\n")
        #             print(err)
    else: #guest user who isn't logged in
        set_guest_session(conn, sessionID)
    cookie["sessionID"] = sessionID
    cookie["sessionID"]["expires"] = "1 Jan 2021 12:00:00 UTC"
    print(cookie)
    return sessionID

class SessionIdError(Exception):
    """SessionID cannot be updated. It may not be unique, or there is a different DB error."""

def session_update(conn, uid, sessionID):
    sql = "INSERT INTO Session_T(SessionID, UserID) VALUES(%s, %s) ON DUPLICATE KEY UPDATE SessionID = %s"
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (sessionID, uid, sessionID))
        conn.commit()
    except Exception as err:
        print("Content-type:text/html\r\n\r\n")
        print(err)

def set_guest_session(conn, sessionID):
    sql = "INSERT INTO Session_T(SessionID, UserID) VALUES(%s, 9999999) ON DUPLICATE KEY UPDATE SessionID = %s"
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (sessionID, sessionID))
        conn.commit()
    except Exception as err:
        print("Content-type:text/html\r\n\r\n")
        print(err)

def tell_server_to_confirm():
    while True:
        flag = open(f"../files/f-userdata_confirmation.txt")
        try:
            if flag.read() != 1:
                pass
        except Exception as err:
            print(err)
            break
        else:
            with open(f"../files/userdata_confirmation.txt", "w") as fout:
                fout.write("0")
            with open(f"../files/f-userdata_confirmation.txt", "w") as wflag:
                wflag.write("1")
            flag.close()
            break
    print("Go ahead, Java, it's all yours")

def update_quantity(conn, new_quantity, userID, productID):
    sql = "UPDATE Shopping_Cart_T SET Quantity = %s WHERE UserID = %s AND ProductID = %s"
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (new_quantity, userID, productID))
        conn.commit()
    except Exception as err:
        print("Content-type:text/html\r\n\r\n")
        print(err)

def update_user_address(conn, userID, address):
    if int(userID)//1000000 != 2:
        table = "Business_T"
        idtype = "BusinessID"
        sql = "UPDATE Business_T SET Address = %s WHERE BusinessID = %s"
    else:
        table = "Individual_T"
        idtype = "UserID"
        sql = "UPDATE Individual_T SET Address = %s WHERE UserID = %s"
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (address, userID))
        conn.commit()
    except Exception as err:
        print("Content-type:text/html\r\n\r\n")
        print(err)

def update_user_bank(conn, userID, bank):
    if int(userID)//1000000 != 2:
        table = "Business_T"
        idtype = "BusinessID"
        sql = "UPDATE Business_T SET Debit_Card = %s WHERE BusinessID = %s"
    else:
        table = "Individual_T"
        idtype = "UserID"
        sql = "UPDATE Individual_T SET Debit_Card = %s WHERE UserID = %s"
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (bank, userID))
        conn.commit()
    except Exception as err:
        print("Content-type:text/html\r\n\r\n")
        print(err)

def write_cart(conn, userID, product_name, quantity):
    productID = get_productID(conn, product_name)
    #first check if user-item already in Shopping_Cart_T, if so just increment quantity
    sql_check = "SELECT UserID, ProductID, Quantity FROM Shopping_Cart_T WHERE UserID = %s AND ProductID = %s"
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql_check, (userID, productID))
        response = cursor.fetchone()
    except Exception as err:
        print("Content-type:text/html\r\n\r\n")
        print(err)
    if response == None:
        sql = "INSERT INTO Shopping_Cart_T VALUES (%s, %s, %s)"
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, (userID, productID, quantity))
            conn.commit()
        except Exception as err:
            print("Content-type:text/html\r\n\r\n")
            print(err)
    else:
        additional_quantity = int(response["Quantity"])
        total_quantity = additional_quantity + int(quantity)
        update_quantity(conn, total_quantity, userID, productID)

def write_order_request(QnameAtC, product, quantity, myusername, mypassword, QflagName, QnameAtS, AflagName, AnameAtC, AnameAtS, sendPort, receivePort):
    """Writes a txt file for the B2B order and update flag file to indicate
    Client.java may read it and process the order. Calls Client program.
    """
    while True:
        flag = open(f"../files/f-{QnameAtC}")
        try:
            if flag.read() != 0:
                pass
        except Exception as err:
            print("Content-type:text/html\r\n\r\n")
            print(str(err))
            break
        else:
            with open(f"../files/{QnameAtC}", "w") as fin:
                fin.write(f"{myusername},{mypassword},{product},{quantity}")
            with open(f"../files/f-{QnameAtC}", "w") as flag:
                flag.write("1")
            run(["java","Client", f"../files/{QflagName}", f"../files/{QnameAtC}", f"../files/{QnameAtS}", f"../files/{AflagName}", f"../files/{AnameAtC}", f"../files/{AnameAtS}", sendPort, receivePort])
            flag.close()
            break

def write_to_bank(QnameAtC, orderID, sale_amount, customer_account, my_account, my_password, QflagName, QnameAtS, AflagName, AnameAtC, AnameAtS, sendPort, receivePort):
    """Writes a txt file to the bank to process payment information.
    Format: OrderID,SaleAmount,CustomerBankAcct,MyBankAcct,MyBankPassword
    """
    while True:
        flag = open(f"../files/f-{QnameAtC}")
        try:
            if flag.read() != 0:
                pass
        except Exception as err:
            print("Content-type:text/html\r\n\r\n")
            print(str(err))
            break
        else:
            with open(f"../files/{QnameAtC}", "w") as fin:
                fin.write(f"{orderID},{sale_amount},{customer_account},{my_account},{my_password}")
            with open(f"../files/f-{QnameAtC}", "w") as flag:
                flag.write("1")
            run(["java","Client", f"../files/{QflagName}", f"../files/{QnameAtC}", f"../files/{QnameAtS}", f"../files/{AflagName}", f"../files/{AnameAtC}", f"../files/{AnameAtS}", sendPort, receivePort])
            flag.close()
            break
    
#myID,mycustomer,mybank,customerbank,itemordered,quantity,totalamount,shipping
def write_order_table(conn, item_ordered, customerID, quantity, shipping_method, card):
    sql = "INSERT INTO Order_T(Item_Ordered, UserID, Quantity, Shipping_Method, Card_Number) VALUES(%s, %s, %s, %s, %s)"
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (item_ordered, customerID, quantity, shipping_method, card))
            orderID = cursor.lastrowid
        conn.commit()
    except Exception as err:
        print("Content-type:text/html\r\n\r\n")
        print(err)
    return orderID

def write_to_taxes(QnameAtC, orderID, sale_amount, customer_account, my_tax_acct, my_password, QflagName, QnameAtS, AflagName, AnameAtC, AnameAtS, sendPort, receivePort):
    """Write tax info to mayor.
    Format: OrderID,SaleAmount,CustomerBankAcct,MyTaxAcct,MyTaxPassword
    """
    while True:
        flag = open(f"../files/f-{QnameAtC}")
        try:
            if flag.read() != 0:
                pass
        except Exception as err:
            print("Content-type:text/html\r\n\r\n")
            print(str(err))
            break
        else:
            with open(f"../files/{QnameAtC}", "w") as fin:
                fin.write(f"{orderID},{sale_amount},{customer_account},{my_tax_acct},{my_password}")
            with open(f"../files/f-{QnameAtC}", "w") as flag:
                flag.write("1")
            run(["java","Client", f"../files/{QflagName}", f"../files/{QnameAtC}", f"../files/{QnameAtS}", f"../files/{AflagName}", f"../files/{AnameAtC}", f"../files/{AnameAtS}", sendPort, receivePort])
            flag.close()
            break
#myID,mycustomer,mybank,customerbank,itemordered,quantity,totalamount,shipping
def write_to_shipping(QnameAtC, orderID, itemID, quantity, shipping_method, shipping_address, my_ship_acct, my_password, QflagName, QnameAtS, AflagName, AnameAtC, AnameAtS, sendPort, receivePort):
    """Write shipping info.
    Format: OrderID,ItemID,Quantity,ShipMethod,ShipAddr,MyShipAcct,MyShipPassword
    """
    while True:
        flag = open(f"../files/f-{QnameAtC}")
        try:
            if flag.read() != 0:
                pass
        except Exception as err:
            print("Content-type:text/html\r\n\r\n")
            print(str(err))
            break
        else:
            with open(f"../files/{QnameAtC}", "w") as fin:
                fin.write(f"{orderID},{itemID},{quantity},{shipping_method},{shipping_address},{my_ship_acct},{my_password}")
            with open(f"../files/f-{QnameAtC}", "w") as flag:
                flag.write("1")
            run(["java","Client", f"../files/{QflagName}", f"../files/{QnameAtC}", f"../files/{QnameAtS}", f"../files/{AflagName}", f"../files/{AnameAtC}", f"../files/{AnameAtS}", sendPort, receivePort])
            flag.close()
            break

def write_to_IT(QnameAtC, orderID, itemID, quantity, sale_amount, customer_account, shipping_method, shipping_address, my_it_acct, my_password, QflagName, QnameAtS, AflagName, AnameAtC, AnameAtS, sendPort, receivePort):
    """Write order to (the other) IT data collection company.
    Format: OrderID,ItemID,Quantity,SaleAmount,CustomerBankAcct,ShipMethod,ShipAddr,MyItAcct,MyItPassword
    """
    while True:
        flag = open(f"../files/f-{QnameAtC}")
        try:
            if flag.read() != 0:
                pass
        except Exception as err:
            print("Content-type:text/html\r\n\r\n")
            print(str(err))
            break
        else:
            with open(f"../files/{QnameAtC}", "w") as fin:
                fin.write(f"{orderID},{itemID},{quantity},{sale_amount},{customer_account},{shipping_method},{shipping_address},{my_it_acct},{my_password}\n")
            with open(f"../files/f-{QnameAtC}", "w") as flag:
                flag.write("1")
            run(["java","Client", f"../files/{QflagName}", f"../files/{QnameAtC}", f"../files/{QnameAtS}", f"../files/{AflagName}", f"../files/{AnameAtC}", f"../files/{AnameAtS}", sendPort, receivePort])
            flag.close()
            break

def write_user_transaction(conn, user_orderID, product_name, sellerID, sale_amount, quantity, shipping_method, inventory):
    update_user_product(conn, product_name, sellerID, inventory)
    sql_productID = "SELECT ProductID FROM User_Product_T WHERE Product_Name = %s"
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql_productID, (product_name))
            response_id = cursor.fetchone()
    except Exception as err:
        print(err)
    productID = response_id["ProductID"]
    sql = "INSERT INTO User_Transaction_T(ProductID, SellerID, Sale_Amount, Quantity, UserOrderID, Shipping_Method) VALUES(%s, %s, %s, %s, %s, %s)"
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (productID, sellerID, sale_amount, quantity, user_orderID, shipping_method))
        conn.commit()
    except Exception as err:
        print(err)

def update_user_product(conn, product_name, businessID, inventory):
    sql_productid = "SELECT ProductID FROM User_Product_T WHERE Product_Name = %s"
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql_productid, (product_name))
            response = cursor.fetchone()
    except Exception as err:
        print(err)
    if response != None:
        productID = response["ProductID"]
        sql = "UPDATE User_Product_T SET Inventory = %s WHERE ProductID = %s"
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, (inventory, productID))
            conn.commit()
        except Exception as err:
            print(err)
    else:
        sql = "INSERT INTO User_Product_T(BusinessID, Product_Name, Inventory) VALUES(%s, %s, %s)"
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql, (businessID, product_name, inventory))
            conn.commit()
        except Exception as err:
            print(err)

#login functions

def check_credentials(conn, table, uname, pword):
    ph = PasswordHasher()
    if table == "Business_T":
        sql = "SELECT Password FROM Business_T WHERE Business_Name = %s"
    elif table == "Individual_T":
        sql = "SELECT Password FROM Individual_T WHERE Username = %s"
    else:
        sql = "SELECT Password FROM Staff_T WHERE Username = %s"
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (uname))
            answer = cursor.fetchone()
    except Exception as err:
        print("Content-type:text/html\r\n\r\n") #TODO testing only
        print(err)
    try:
        encrypted_pword = answer["Password"]
    except Exception as err:
        return False
    try:
        password_matches = ph.verify(encrypted_pword, pword)
    except Exception as mismatcherr: #TODO be more specific, it's VerifyMismatchError
        password_matches = False
    if not password_matches:
        return password_matches
    else:
        rehash = ph.check_needs_rehash(encrypted_pword)
        if rehash:
            rehash_pwd(conn, pword, uname, table)
    return password_matches

def rehash_pwd(conn, pword, uname, table):
    new_pwd = pass_hash(pword)
    if table == "Business_T":
        sql = "UPDATE Business_T SET Password = %s WHERE Business_Name = %s"
    else:
        sql = "UPDATE Individual_T SET Password = %s WHERE Username = %s"
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (new_pwd, uname))
        conn.commit()
    except Exception as err:
        print("Content-type:text/html\r\n\r\n") #TODO testing only
        print(err)

#get userID from DB
def getUID(conn, tablename, user):
    if tablename == "Business_T":
        col = "Business_Name"
        id_col = "BusinessID"
        sql = "SELECT BusinessID FROM Business_T WHERE Business_Name = %s"
    else:
        col = "Username"
        id_col = "UserID"
        sql = "SELECT UserID FROM Individual_T WHERE Username = %s"
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, (user))
            response = cursor.fetchone()
    except Exception as err:
        print("Content-type:text/html\r\n\r\n") #TODO testing only
        print(err)
    uid = response[f"{id_col}"]
    return uid

def login_failure():
    print("<html lang=\"en\">")
    print("<head>")
    print("<meta charset=\"UTF-8\">")
    print("<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">")
    print("<meta http-equiv=\"X-UA-Compatible\" content=\"ie=edge\">")
    print("<link rel=\"stylesheet\" href=\"../style.css\">")
    print("<title>Habitat</title>")
    print("</head>")
    print("<h1>Login Failed</h1>")
    print("<h3>Please try again.</h3>")
    print("<h3 class=\"card-title\"><a href=\"../login.html\" class=\"btn\">Login</a></h3>")
    print("</html>")

def pass_hash(pwd):
    ph = PasswordHasher()
    pwd_hashed = ph.hash(pwd)
    try:
        #ph.check_needs_rehash -- use this every time user logs in
        ph.verify(pwd_hashed, pwd)
        return pwd_hashed
    except Exception as err: #VerifyMismatchError
        print(err)
    # except InvalidHash as invalid_err:
    #     print(invalid_err)