#!/var/www/ebusiness/b-f19-02/html/cgi-bin/proj/bin/python3

import cgi, cgitb
from http import cookies
import pymysql as db
from argon2 import PasswordHasher
from credentials import *

def main():
    conn = dbsetup(auth_name, dbpword, dbname)
    
    #cgitb.enable(display=0,logdir="testshopcart")

    #create instance of FieldStorage
    form = cgi.FieldStorage()
    #get data from fields
    user_type = form.getfirst("usertype")
    uname = form.getfirst("username")
    pword = pass_hash(form.getfirst("password"))
    address = form.getfirst("address")
    card = form.getfirst("debit_card")
    if user_type == "individual":
        table = "Individual_T"
    elif user_type == "business":
        table = "Business_T"
    else:
        table = "Staff_T"
    if table != "Staff_T":
        write_db(conn, table, uname, pword, address, card)
    else:
        write_db(conn, table, uname, pword)
    conn.close()
    if table != "Business_T":
        print("Content-type:text/html\r\n\r\n")
        print("<html lang=\"en\">")
        print("<head>")
        print("<meta charset=\"UTF-8\">")
        print("<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">")
        print("<meta http-equiv=\"X-UA-Compatible\" content=\"ie=edge\">")
        print("<link rel=\"stylesheet\" href=\"../style.css\">")
        print("<title>Habitat</title>")
        print("</head>")
        print("<h1>Registration Successful</h1>")
        print("<h3 class=\"card-title\"><a href=\"products.cgi\" class=\"btn\">Products</a></h3>")
        print("<h3 class=\"card-title\"><a href=\"../login.html\" class=\"btn\">Login</a></h3>")
        print("</html>")
    else:
        print("Content-type:text/html\r\n\r\n")
        print("""<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="X-UA-Compatible" content="ie=edge">
    <link rel="stylesheet" href="../style.css">
    <title>Habitat</title>
</head>
<body>
    <main id="showcase">
        <a href="index.html" class="btn-no-padding">Home</a>
        <div class="bg-image"></div>
        <h1>Welcome to Habitat!</h1>
        <p>To connect with us, please use our socket-based API by sending new data to be stored and processed to port 11020.</p>
        <p>Please expect your confirmation response back on port 11025</p>
        <p>Send new data in a file called userdata.txt with the following format: </p>
        <p>yourUserName,yourCustomerUserName,YYYY-MM-DD,itemOrdered,quantity,price,remainingInventoryofItem</p>
        
    </main>
    
     <!-- Footer -->
     <footer id="main-footer" class="grid">
            <div>Habitat Data Storage and Visualization</div>
            <div>Project by Kevin Dean
                    <div>With thanks to <a href="http://traversymedia.com" target="_blank">Traversy Media</a> for layout/styling</div> 
            </div>
        </footer>
        <script src="register.js"></script>
</body>
</html>""")

def dbsetup(usr, pwd, schema):
    """Sets up pymysql connection to MySQL database"""
    conn = db.connect(
        user=usr,
        password=pwd,
        db=schema,
        charset="utf8mb4",
        cursorclass=db.cursors.DictCursor
    )
    return conn

def pass_hash(pwd):
    ph = PasswordHasher()
    pwd_hashed = ph.hash(pwd)
    try:
        #ph.check_needs_rehash -- use this every time user logs in
        ph.verify(pwd_hashed, pwd)
        return pwd_hashed
    except Exception as err: #TODO specify VerifyMisMatchError
        print(err)
    except Exception as invalid_err: #TODO specify
        print(invalid_err)

def listify_file(filename):
    with open(filename) as fin:
        content = fin.read()
    return content 

#write to database
def write_db(conn, tablename, usrvalue, pwdvalue, address=None, card=None):
    name = "Username"
    if tablename == "Business_T":
        name = "Business_Name"
    if address != None and card != None:
        sql = f"INSERT INTO {tablename} ({name}, Password, Address, Debit_Card) VALUES ('{usrvalue}','{pwdvalue}','{address}','{card}')"
    else:
        sql = f"INSERT INTO {tablename} ({name}, Password) VALUES ('{usrvalue}','{pwdvalue}')"
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
        conn.commit()
    except Exception as err:
        print("Content-type:text/html\r\n\r\n")
        print(err)



#print("Location: index.html", "\n\n")
main()



#Adapted in part from:
#http://anh.cs.luc.edu/python/hands-on/3.1/handsonHtml/dynamic.html
#slides, cgi_example TODO find exact reference
#dynamic static pages http://anh.cs.luc.edu/python/hands-on/3.1/handsonHtml/webtemplates.html
#password hashing: https://pypi.org/project/argon2-cffi/