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
        if int(uid) == 1111100:
            #admin user who sees overview of all data
            try:
                data = get_all_data(conn)
            except Exception as err:
                print("Content-type:text/html\r\n\r\n")
                print(err)
            try:
                transaction_data = get_transaction_data(conn)
            except Exception as err:
                print("Content-type:text/html\r\n\r\n")
                print(err)

            df = pd.DataFrame({
                "Product" : [d["Product_Name"] for d in data],
                "Shipping_Method" : [str(d["Shipping_Method"]) for d in data],
                "Sale_Amount": [float(d["Sale_Amount"]) for d in data],
                "Quantity": [int(d["Quantity"]) for d in data]
                })
            sales_by_product = df.groupby(["Product"]).Sale_Amount.sum().reset_index()
            chart = alt.Chart(sales_by_product).mark_bar(color="#d786a4").encode(
                x=alt.X("Product", axis=alt.Axis(title="Product", titleFontSize=20, titleColor="#ccc", grid=True, gridColor="#ccc", labelColor="#ccc")),
                y=alt.Y("Sale_Amount", axis=alt.Axis(title="Total Amount Sold ($)", format="$", titleFontSize=20, titleColor="#ccc", grid=True, gridColor="#ccc", labelColor="#ccc")), 
                tooltip=["Product", "Sale_Amount"]).configure(background="#181818"
                ).properties(
                    width=500,
                    height=500,
                    autosize=alt.AutoSizeParams(contains="padding", type="fit")
                ).interactive().to_json()
            shipping_by_product = df.groupby(["Shipping_Method", "Product"]).sum().reset_index()
            chart2 = alt.Chart(shipping_by_product).mark_bar().encode(
                x=alt.X("Quantity", axis=alt.Axis(title="Quantity Sold", titleFontSize=20, titleColor="#ccc", gridColor="#ccc", labelColor="#ccc")),
                y=alt.Y("Shipping_Method", axis=alt.Axis(title="Shipping Method", titleFontSize=20, titleColor="#ccc", gridColor="#ccc", labelColor="#ccc")),
                color="Product",
                tooltip=["Product", "Quantity"]).configure(background="#181818"
                ).properties(
                    width=700,
                    height=500,
                    autosize=alt.AutoSizeParams(contains="padding", type="fit")
                ).configure_legend(strokeColor="gray", fillColor="#ccc").to_json()
            transaction_df = pd.DataFrame({
                "SellerID" : [str(d["SellerID"]) for d in transaction_data],
                "Sale_Amount": [float(d["Sale_Amount"]) for d in transaction_data]
            })
            sales_by_user = transaction_df.groupby(["SellerID"]).sum().reset_index()
            chart3 = alt.Chart(sales_by_user).mark_bar().encode(
                x=alt.X("sum(Sale_Amount)", axis=alt.Axis(title="Total Sales ($)", titleFontSize=20, titleColor="#ccc", gridColor="#ccc", labelColor="#ccc")),
                y=alt.Y("SellerID", axis=alt.Axis(title="User (ID)", titleFontSize=20, titleColor="#ccc", gridColor="#ccc", labelColor="#ccc")),
                color="SellerID",
                tooltip=["SellerID", "Sale_Amount"]).configure(background="#181818"
                ).properties(
                    width=700,
                    height=500,
                    autosize=alt.AutoSizeParams(contains="padding", type="fit")
                ).configure_legend(strokeColor="gray", fillColor="#ccc").to_json()
            
            print("Content-type:text/html\r\n\r\n")
            print(visualize_data(chart, chart2, chart3))
        else:
            #data: list of dicts with keys Product_Name, Transact_Date, Price, Quantity
            try:
                data = get_business_data(conn, uid)
            except Exception as err:
                print("Content-type:text/html\r\n\r\n")
                print(err)
            if data != ():
                df = pd.DataFrame({
                    "Product" : [d["Product_Name"] for d in data],
                    "Shipping_Method" : [str(d["Shipping_Method"]) for d in data],
                    "Sale_Amount": [float(d["Sale_Amount"]) for d in data],
                    "Quantity": [int(d["Quantity"]) for d in data]
                    })
                sales_by_product = df.groupby(["Product"]).Sale_Amount.sum().reset_index()
                chart = alt.Chart(sales_by_product).mark_bar(color="#d786a4").encode(
                    x=alt.X("Product", axis=alt.Axis(title="Product", titleFontSize=20, titleColor="#ccc", grid=True, gridColor="#ccc", labelColor="#ccc")),
                    y=alt.Y("Sale_Amount", axis=alt.Axis(title="Total Amount Sold ($)", format="$", titleFontSize=20, titleColor="#ccc", grid=True, gridColor="#ccc", labelColor="#ccc")), 
                    tooltip=["Product", "Sale_Amount"]).configure(background="#181818"
                    ).properties(
                        width=500,
                        height=500,
                        autosize=alt.AutoSizeParams(contains="padding", type="fit")
                    ).interactive().to_json()
                shipping_by_product = df.groupby(["Shipping_Method", "Product"]).sum().reset_index()
                chart2 = alt.Chart(shipping_by_product).mark_bar().encode(
                    x=alt.X("Quantity", axis=alt.Axis(title="Quantity Sold", titleFontSize=20, titleColor="#ccc", gridColor="#ccc", labelColor="#ccc")),
                    y=alt.Y("Shipping_Method", axis=alt.Axis(title="Shipping Method", titleFontSize=20, titleColor="#ccc", gridColor="#ccc", labelColor="#ccc")),
                    color="Product",
                    tooltip=["Product", "Quantity"]).configure(background="#181818"
                    ).properties(
                        width=700,
                        height=500,
                        autosize=alt.AutoSizeParams(contains="padding", type="fit")
                    ).configure_legend(strokeColor="gray", fillColor="#ccc").to_json()
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



def visualize_data(chartjson, chartjson2, chartjson3=None):
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
            if chartjson3 != None:
                returnpage.insert(i+3, 
                    f"<script type=\"text/javascript\"> var mychart3 = {chartjson3}; vegaEmbed(\'#vis3\', mychart3); </script>" 
                )
    returnpagestr = ""
    returnpagestr = returnpagestr.join(returnpage)
    return returnpagestr

def display_b2bform(file):
    with open(f"../{file}") as fin:
        print(fin.read())


main()

