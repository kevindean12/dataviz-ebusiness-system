#!/var/www/ebusiness/b-f19-02/html/cgi-bin/proj/bin/python3

import cgi, cgitb
from http import cookies
import pymysql as db
from argon2 import PasswordHasher
from credentials import *
from project_functions import *
import pandas as pd
import altair as alt

def main():
    conn = dbsetup(auth_name, dbpword, dbname)
    form = cgi.FieldStorage()
    user_type = form.getfirst("usertype")
    #TODO handle wrong username
    uname = form.getfirst("username")
    pword = form.getfirst("password")
    if user_type == "individual":
        table = "Individual_T"
    elif user_type == "business":
        table = "Business_T"
    else:
        table = "Staff_T"
    
    password_matches = check_credentials(conn,table,uname,pword)

    if password_matches and table=="Business_T":
        uid = getUID(conn,table,uname)
        set_cookie(conn, uid)
        #data: list of dicts with keys Product_Name, Transact_Date, Price, Quantity
        
        try:
            data = get_business_data(conn, uid)
        except Exception as err:
            print("Content-type:text/html\r\n\r\n")
            print(err)
        if data != ():
            df = pd.DataFrame({
                "Product" : [d["Product_Name"] for d in data],
                "Date" : [str(d["Transact_Date"]) for d in data],
                "Price": [float(d["Price"]) for d in data],
                "Quantity": [int(d["Quantity"]) for d in data]
                })
            sales_date_df = df
            sales_date_df["Amount"] = sales_date_df.Price.mul(sales_date_df.Quantity)
            sales_date_df = sales_date_df.groupby(["Date"]).sum()
            sales_date_df.index = pd.to_datetime(sales_date_df.index)
            sales_date_df = sales_date_df.reset_index()
            chart = alt.Chart(sales_date_df).mark_line(color="#d786a4", size=3, point=True).encode(
                x=alt.X("Date", axis=alt.Axis(title="Date of Transaction", titleFontSize=20, titleColor="#ccc", grid=True, gridColor="#ccc", labelColor="#ccc")),
                y=alt.Y("Amount", axis=alt.Axis(title="Sales on Date", format="$", titleFontSize=20, titleColor="#ccc", grid=True, gridColor="#ccc", labelColor="#ccc")), 
                tooltip=["Date", "Amount", "Quantity"]).configure(background="#181818"
                ).properties(
                    width=500,
                    height=500,
                    autosize=alt.AutoSizeParams(contains="padding", type="fit")
                ).interactive().to_json()
            product_sales_df = df
            product_sales_df["Amount"] = product_sales_df.Price.mul(product_sales_df.Quantity)
            product_sales_df = product_sales_df.groupby(["Product"]).sum()
            product_sales_df = product_sales_df.reset_index()
            chart2 = alt.Chart(product_sales_df).mark_bar(color="#d786a4").encode(
                x=alt.X("Product", axis=alt.Axis(title="Product", titleFontSize=20, titleColor="#ccc", labelColor="#ccc")), 
                y=alt.Y("Quantity", axis=alt.Axis(title="Number Sold", titleFontSize=20, titleColor="#ccc", labelColor="#ccc")),
                ).properties(
                    width=500,
                    height=500,
                    autosize=alt.AutoSizeParams(contains="padding", type="fit")).to_json()
            print("Content-type:text/html\r\n\r\n")
            print(visualize_data(chart, chart2))
        else:
            print("Content-type:text/html\r\n\r\n")
            print("<html lang=\"en\">")
            print("<head>")
            print("<meta charset=\"UTF-8\">")
            print("<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">")
            print("<meta http-equiv=\"X-UA-Compatible\" content=\"ie=edge\">")
            print("<link rel=\"stylesheet\" href=\"../style.css\">")
            print("<title>Habitat</title>")
            print("</head>")
            print("<h2>You don't have any sales yet!</h2>")
            print("<h3 class=\"card-title\"><a href=\"products.cgi\" class=\"btn\">Products</a></h3>")
            print("<h3 class=\"card-title\"><a href=\"../index.html\" class=\"btn\">Home</a></h3>")
            print("</html>")
        

    elif password_matches and table=="Individual_T":
        uid = getUID(conn,table,uname)
        set_cookie(conn, uid)
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
        print("</html>")
    elif password_matches and table == "Staff_T":
        form = "b2bform_x.html"
        print("Content-type:text/html\r\n\r\n")
        display_b2bform(form)

    else:
        print("Content-type:text/html\r\n\r\n")
        login_failure()

    conn.close()

def check_credentials(conn, table, uname, pword):
    ph = PasswordHasher()
    if table == "Business_T":
        sql = "SELECT Password FROM Business_T WHERE Business_Name = %s"
    else:
        sql = "SELECT Password FROM Individual_T WHERE Username = %s"
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

def visualize_data(chartjson, chartjson2):
    returnpage = listify_file("../dataviz_x.html")
    for line in returnpage:
        if "putdataviz" in line:
            i = returnpage.index(line)
            returnpage.insert(i+1, 
                f"<script type=\"text/javascript\"> var mychart = {chartjson}; vegaEmbed(\'#vis\', mychart); </script>"
            )
            returnpage.insert(i+2,
                f"<script type=\"text/javascript\"> var mychart2 = {chartjson2}; vegaEmbed(\'#vis2\', mychart2); </script>" 
            )
    returnpagestr = ""
    returnpagestr = returnpagestr.join(returnpage)
    return returnpagestr

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

def display_b2bform(file):
    with open(f"../{file}") as fin:
        print(fin.read())


main()

