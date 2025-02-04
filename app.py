from flask import Flask, jsonify, request, session
from flask_restful import Api, Resource
from flaskext.mysql import MySQL
from passlib.hash import sha256_crypt
import os
import jwt
from pathlib import Path
from functools import wraps
from flask_cors import CORS, cross_origin
from emailClass import OAuthMail
from datetime import datetime
import datetime
import threading
import bcrypt
import pdfkit
import time
import base64
from pdf_writer import invoice_html_render
from weasyprint import HTML


app = Flask(__name__)
cors = CORS(app)


app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY")
app.config["MYSQL_DATABASE_HOST"] = os.environ.get("DATABASE_HOST")
app.config["MYSQL_DATABASE_USER"] = os.environ.get("DATABASE_USER")
app.config["MYSQL_DATABASE_PASSWORD"] = os.environ.get("DATABASE_PASSWORD")
app.config["MYSQL_DATABASE_DB"] = os.environ.get("DATABASE_DB")
app.config["MYSQL_DATABASE_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)
mysql.init_app(app)
api = Api(app)

def get_email(customer_id):
    cursor = mysql.get_db().cursor()
    query = "SELECT `email` FROM `CUSTOMER` WHERE customer_id = (%s)"
    cursor.execute(query, (customer_id,))
    return cursor.fetchone()[0]

def invoice(cart_id, items, mail):
    render = invoice_html_render(cart_id, "invoice.html", items)
    html_file = render.solid_write()
    print("html file has been successfully created")

    html_filename = render.filename
    pdf_filename = str(hash(cart_id)) + ".pdf"
    print ("pdf file has been succesfully created")

    htmldoc = HTML(string=html_file, base_url="")
    pdf = htmldoc.write_pdf()
    Path(pdf_filename).write_bytes(pdf)

    mail = OAuthMail(mail, "your invoice", html="mails/order.html", attach=[pdf_filename])
    mail.send()
    print("invoice has been sent to the customer successfully")

    with open(pdf_filename, 'rb') as f:
        blob = base64.b64encode(f.read())
        cursor = mysql.get_db().cursor()
        query = "INSERT INTO `INVOICE`(`invoice`, `cart_id`) VALUES ((%s),(%s))"
        cursor.execute(query, (blob, cart_id))
        mysql.get_db().commit()
    
    print("invoice has been inserted to the database")

    os.remove(pdf_filename)
    print("pdf file removed")

    print("returnning base64 object")

    return blob




def get_basket_price(product_id, cart_id):
    cursor = mysql.get_db().cursor()
    query = "SELECT price_with_discount FROM CART_PRODUCT WHERE product_id = (%s) AND cart_id = (%s)"
    cursor.execute(query, (product_id, cart_id))
    return cursor.fetchone()[0]

def get_quantity(cart_id, product_id):
    cursor = mysql.get_db().cursor()
    query = "SELECT  `amount` FROM `CART_PRODUCT` WHERE cart_id = (%s) AND product_id = (%s)"
    cursor.execute(query, (cart_id,product_id))
    return cursor.fetchone()[0]



def send_invoice(cart_id, items):
    render = invoice_html_render(cart_id,"invoice.html",items)
    render.solid_write()
    pdf = pdf_writer(cart_id,render.filename)
    time.sleep(3)
    count = 0
    print(items)
    while(count < 10):
        try:
            pdf.solid_write()
            count = 10
        except Exception:
            count += 1
            time.sleep(1)
    OAuthMail("alperenyildiz@sabanciuniv.edu","ephemeral html email", html="mails/order.html", attach=[pdf.filename]).send()
    with open(pdf.filename, 'rb') as f:
        blob = base64.b64encode(f.read())
        cursor = mysql.get_db().cursor()
        query = "INSERT INTO `INVOICE`(`invoice`, `cart_id`) VALUES ((%s),(%s))"
        cursor.execute(query, (blob, cart_id))
        mysql.get_db().commit()
    return blob


def increase_stock(product_id, amount):
    cursor = mysql.get_db().cursor()
    query = "SELECT stock FROM PRODUCT WHERE product_id =(%s)"
    cursor.execute(query, (product_id,))
    stock = cursor.fetchone()[0]
    stock += amount

    query = "UPDATE PRODUCT SET stock = (%s) WHERE product_id = (%s)"
    cursor.execute(query, (stock, product_id))
    mysql.get_db().commit()


def decrease_stock(product_id, amount):
    cursor = mysql.get_db().cursor()
    query = "SELECT stock FROM PRODUCT WHERE product_id =(%s)"
    cursor.execute(query, (product_id,))
    stock = cursor.fetchone()[0]
    stock -= amount

    query = "UPDATE PRODUCT SET stock = (%s) WHERE product_id = (%s)"
    cursor.execute(query, (stock, product_id))
    mysql.get_db().commit()

def get_price(product_id):
    cursor = mysql.get_db().cursor()
    query = "SELECT price FROM PRODUCT WHERE product_id =(%s)"
    cursor.execute(query, (product_id,))
    price = cursor.fetchone()[0]
    return price

def is_product_manager(user_id):
    cursor = mysql.get_db().cursor()
    query = """ SELECT *
                FROM PRODUCT_MANAGER, USERS
                WHERE pm_id = user_id and user_id = (%s)
            """

    cursor.execute(query, (user_id,))
    data = cursor.fetchone()

    if (data != None):
        return True
    else:
        return False


def is_sales_manager(user_id):
    cursor = mysql.get_db().cursor()
    query = """ SELECT *
                FROM SALES_MANAGER, USERS
                WHERE sm_id = user_id and user_id = (%s)
            """

    cursor.execute(query, (user_id,))
    data = cursor.fetchone()

    if (data != None):
        return True
    else:
        return False


def username_to_id(username):
    cursor = mysql.get_db().cursor()
    query = "SELECT user_id FROM USERS WHERE username = (%s)"
    cursor.execute(query, (username,))
    data = cursor.fetchone()
    user_id = data[0]

    return user_id


def product_to_id(product):
    cursor = mysql.get_db().cursor()
    query = "SELECT product_id FROM PRODUCT WHERE name = (%s)"
    cursor.execute(query, (product,))
    data = cursor.fetchone()
    return data[0]

def id_to_product(pID):
    cursor = mysql.get_db().cursor()
    query = "SELECT name FROM `PRODUCT` WHERE product_id=(%s)"
    cursor.execute(query, (pID))
    data = cursor.fetchone()
    return data[0]

def get_from_jwt(token, param):  # assumes jwt token is valid
    data = jwt.decode(token, os.environ.get("SECRET_KEY"), algorithms="HS256")
    return data[param]


def add_customer(username, phone, address, email):
    cursor = mysql.get_db().cursor()
    query = "SELECT user_id FROM USERS WHERE username = (%s)"
    cursor.execute(query, (username,))
    data = cursor.fetchone()
    user_id = data[0]  # id of the newly created user
    query = 'INSERT INTO `CUSTOMER` (customer_id, phone, address, email) VALUES (%s, %s, %s, %s)'
    cursor.execute(query, (str(user_id), str(phone), str(address), str(email)))
    mysql.get_db().commit()


def send_mail(first_name, email):
    message = f"Hello {first_name}, \nWelcome to our website! \n"
    mail = OAuthMail(email, "Hello and welcome {}!".format(
        first_name), html="mails/welcome.html")
    mail.send()


def add_user(first_name, last_name, username, password, email):
    cursor = mysql.get_db().cursor()
    query = "INSERT INTO `USERS` (`first_name`, `last_name`, `username`, `password`, `email`) VALUES ((%s), (%s), (%s), (%s), (%s))"
    cursor.execute(query, (first_name, last_name, username, password, email))
    mysql.get_db().commit()


def find_user(username):
    cursor = mysql.get_db().cursor()

    query = "SELECT * FROM USERS WHERE username=(%s)"
    cursor.execute(query, (username,))
    data = cursor.fetchone()

    return data


def check_posted_data(posted_data, function_name):
    if (function_name == "refund/post"):
        if ("product_name" not in posted_data):
            return 403
        else:
            return 200
    elif (function_name == "private_wrapper"):
        if ("token" not in posted_data or "user" not in posted_data):
            return 403
        else:
            return 200

    elif (function_name == "auth"):
        if("username" not in posted_data or "password" not in posted_data):
            return 400
        return 200
    elif (function_name == "users"):
        if ("first_name" not in posted_data
                or "last_name" not in posted_data
                or "username" not in posted_data
                or "password" not in posted_data
                or "email" not in posted_data
                or "phone" not in posted_data
                or "address" not in posted_data
                or "email" not in posted_data):
            return 400
        return 200

    elif (function_name == "basket_post"):
        if ("product_name" not in posted_data or "quantity" not in posted_data):
            return 400
        return 200

    elif (function_name == "basket_delete"):
        if ("product_name" not in posted_data):
            return 400
        return 200

    elif (function_name == "basket_put"):
        if ("product_name" not in posted_data or "quantity" not in posted_data):
            return 400
        return 200

    elif (function_name == "comment_post"):
        if ("product_name" not in posted_data or "comment" not in posted_data):
            return 400
        return 200
    elif (function_name == "comment_get"):
        if ("product_name" not in posted_data):
            return 400
        return 200


def check_headers(request, function_name):
    if (function_name == "private_wrapper"):
        if ("token" not in request.headers or "user" not in request.headers):
            return False
        return True


def check_if_user(request):  # to check if logged in or guest
    if ("token" not in request.headers or "user" not in request.headers):
        return False
    else:
        try:
            token = request.headers["token"]
            user = request.headers["user"]
            data = jwt.decode(
                token, app.config['SECRET_KEY'], algorithms="HS256")
            if (user != data["user"]):
                return False
            else:
                return True
        except Exception:
            return False


def product_manager_only(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        if check_headers(request, "private_wrapper") == False:
            return jsonify({
                "message": "Forbidden",
                "status_code": 403
            })
        else:
            token = request.headers["token"]
            user = request.headers["user"]
            try:
                data = jwt.decode(
                    token, app.config['SECRET_KEY'], algorithms="HS256")
                if (user != data["user"]):
                    return jsonify({
                        "message": "token does not match the user",
                        "status_code": 403
                    })
                elif (data["user_type"] != "product_manager"):
                    return jsonify({
                        "message": "user is not a product manager",
                        "status_code": 403
                    })
            except jwt.ExpiredSignatureError:
                return jsonify({
                    "message": "token expired",
                    "status_code": 403
                })
            except Exception:
                return jsonify({
                    "message": "invalid token",
                    "status_code": 403
                })
        return func(*args, **kwargs)
    return wrapped


def sales_manager_only(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        if check_headers(request, "private_wrapper") == False:
            return jsonify({
                "message": "Forbidden",
                "status_code": 403
            })
        else:
            token = request.headers["token"]
            user = request.headers["user"]
            try:
                data = jwt.decode(
                    token, app.config['SECRET_KEY'], algorithms="HS256")
                if (user != data["user"]):
                    return jsonify({
                        "message": "token does not match the user",
                        "status_code": 403
                    })
                elif (data["user_type"] != "sales_manager"):
                    return jsonify({
                        "message": "user is not a sales manager",
                        "status_code": 403
                    })
            except jwt.ExpiredSignatureError:
                return jsonify({
                    "message": "token expired",
                    "status_code": 403
                })
            except Exception:
                return jsonify({
                    "message": "invalid token",
                    "status_code": 403
                })
        return func(*args, **kwargs)
    return wrapped


def private(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        if check_headers(request, "private_wrapper") == False:
            return jsonify({
                "message": "Forbidden",
                "status_code": 403
            })
        else:
            token = request.headers["token"]
            user = request.headers["user"]
            try:
                data = jwt.decode(
                    token, app.config['SECRET_KEY'], algorithms="HS256")
                if (user != data["user"]):
                    return jsonify({
                        "message": "token does not match the user",
                        "status_code": 403
                    })
            except jwt.ExpiredSignatureError:
                return jsonify({
                    "message": "token expired",
                    "status_code": 403
                })
            except Exception:
                return jsonify({
                    "message": "invalid token",
                    "status_code": 403
                })
        return func(*args, **kwargs)
    return wrapped


def user_id_to_username(user_id):
    cursor = mysql.get_db().cursor()
    query = "SELECT username FROM USERS WHERE user_id = (%s)"
    cursor.execute(query, (user_id,))
    username = cursor.fetchone()

    return username[0]


class getComment(Resource):
    @cross_origin(origins="http://localhost:3000*")
    def post(self): #get all comments
        posted_data = request.get_json()
        product_name = posted_data["product_name"]
        cursor = mysql.get_db().cursor()
        # get product_id
        query = "SELECT product_id FROM PRODUCT WHERE name = (%s)"
        cursor.execute(query, (product_name,))
        product_id = cursor.fetchone()[0]

        query = "SELECT text, date_time, customer_id, approved, customer_id, product_id FROM `COMMENTS` WHERE product_id=(%s)"
        cursor.execute(query, (product_id,))
        comments = cursor.fetchall()
        product_comments = list()

        for comment in comments:
            product_comments.append({
                "username": user_id_to_username(comment[2]),
                "text": comment[0],
                "time": str(comment[1]),
                "approved": bool(comment[3]),
                "customer_id": comment[4],
                "product_id": comment[5] 
            })

        return jsonify({
            "status_code": 200,
            "comments": product_comments
        })


api.add_resource(getComment, "/getcomment")



class Comment(Resource):
    @cross_origin(origins="http://localhost:3000*")
    @private
    def post(self): #post comment
        posted_data = request.get_json()
        if (check_posted_data(posted_data, "comment_post") == 200):
            username = request.headers["user"]
            cursor = mysql.get_db().cursor()

            product_name = posted_data["product_name"]
            comment = posted_data["comment"]

            # get customer id
            query = "SELECT user_id FROM USERS WHERE username = (%s)"
            cursor.execute(query, (username,))
            user_id = cursor.fetchone()[0]

            # get product_id
            query = "SELECT product_id FROM PRODUCT WHERE name = (%s)"
            cursor.execute(query, (product_name,))
            product_id = cursor.fetchone()[0]

            now = datetime.datetime.now()
            dt_string = now.strftime("%H:%M:%S")
            
            query = "INSERT INTO `COMMENTS`(`product_id`, `customer_id`, `text`, `time`) VALUES ((%s),(%s),(%s),(%s))"
            cursor.execute(query, (product_id, user_id, comment,dt_string))
            mysql.get_db().commit()

            return jsonify({
                "message": "success",
                "status_code": 200
            })
        return jsonify({
            "message": "Bad Request",
            "status_code": 403
        })

    @cross_origin(origins="http://localhost:3000*")
    @product_manager_only
    def put(self): #approve comment
        posted_data = request.get_json()
        cursor = mysql.get_db().cursor()

        customer_id = posted_data["customer_id"]
        product_id = posted_data["product_id"]
        decision = posted_data["decision"]

        query = "UPDATE `COMMENTS` SET `approved`=(%s) WHERE customer_id = (%s) AND product_id = (%s)"
        cursor.execute(query, (bool(decision), customer_id,product_id))
        mysql.get_db().commit()

        if (decision == True):
            return jsonify({
                "message":"comment approved",
                "status_code":201
            })
        else:
            return jsonify({
                "message":"comment disapproved",
                "status_code":201
            })




    @cross_origin(origins="http://localhost:3000*")
    def get(self):
        posted_data = request.get_json()
        if (check_posted_data(posted_data, "comment_get") == 200):
            # get product_id
            product_name = request.headers["product_name"]
            cursor = mysql.get_db().cursor()

            query = "SELECT product_id FROM PRODUCT WHERE name = (%s)"
            cursor.execute(query, (product_name,))
            product_id = cursor.fetchone()[0]

            query = "SELECT text, time FROM `COMMENTS` WHERE product_id=(%s)"
            cursor.execute(query, (product_id,))
            comments = cursor.fetchall()
            product_comments = list()

            for comment in comments:
                product_comments.append({
                    "text": comment[0],
                    "time": str(comment[1])
                })

            return jsonify({
                "status_code": 200,
                "comments": product_comments
            })
        return jsonify({
            "status_code": 403,
            "message": "bad request"
        })


api.add_resource(Comment, "/comment")


class Auth(Resource):
    @cross_origin(origins="http://localhost:3000*")
    def post(self):  # login

        posted_data = request.get_json()
        status_code = check_posted_data(posted_data, "auth")

        if (status_code == 400):
            retJson = {
                'message': 'Missing fields',
                'status_code': status_code
            }
            return jsonify(retJson)

        else:
            username = posted_data["username"]
            password = posted_data["password"]

            cursor = mysql.get_db().cursor()

            query = "SELECT username, first_name, last_name, password FROM USERS WHERE username=(%s)"
            cursor.execute(query, (username, ))
            data = cursor.fetchone()

            if (data != None):

                if (not bcrypt.checkpw(password.encode('utf-8'), data[3].encode('utf-8'))):
                    return jsonify({
                        "message": "user not found",
                        "status_code": 404
                    })

                uid = username_to_id(username)
                if (is_product_manager(uid)):
                    token = jwt.encode({
                        'user': data[0],
                        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=1800),
                        'user_type': 'product_manager'
                    }, app.config['SECRET_KEY'], algorithm='HS256')
                    retJson = {
                        "username": data[0],
                        "name": data[1],
                        "surname": data[2],
                        "token": token,
                        "user_type": "product manager",
                        "status_code": 200
                    }
                elif (is_sales_manager(uid)):
                    token = jwt.encode({
                        'user': data[0],
                        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=1800),
                        'user_type': 'sales_manager'
                    }, app.config['SECRET_KEY'], algorithm='HS256')
                    retJson = {
                        "username": data[0],
                        "name": data[1],
                        "surname": data[2],
                        "token": token,
                        "user_type": "sales manager",
                        "status_code": 200
                    }
                else:
                    token = jwt.encode({
                        'user': data[0],
                        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=1800),
                        'user_type': 'customer'
                    },
                        app.config['SECRET_KEY'], algorithm='HS256')

                    retJson = {
                        "username": data[0],
                        "name": data[1],
                        "surname": data[2],
                        "token": token,
                        "user type": "customer",
                        "status_code": 200
                    }

                return jsonify(retJson)

            else:
                retJson = {
                    "message": "user not found",
                    "status_code": 404
                }

                return retJson

    @cross_origin(origins="http://localhost:3000*")
    @private
    def get(self):
        cursor = mysql.get_db().cursor()
        user = request.headers["user"]
        uid = username_to_id(user)

        query = """
        SELECT username, first_name,last_name,USERS.email,phone,address
        FROM USERS, CUSTOMER
        WHERE USERS.user_id = (%s) AND user_id = customer_id
        """
        cursor.execute(query, (uid,))
        data = cursor.fetchone()

        return jsonify({
            "username": data[0],
            "first_name": data[1],
            "last_name": data[2],
            "email": data[3],
            "phone": data[4],
            "address": data[5],
            "status_code": 200
        })

    @cross_origin(origins="http://localhost:3000*")
    @private
    def put(self):
        posted_data = request.get_json()
        cursor = mysql.get_db().cursor()
        user = request.headers["user"]
        uid = username_to_id(user)
        query = """
        SELECT username, first_name,last_name,USERS.email,phone,address, password
        FROM USERS, CUSTOMER
        WHERE USERS.user_id = (%s) AND user_id = customer_id
        """
        cursor.execute(query, (uid,))
        data = cursor.fetchone()

        username = data[0]

        if("username" not in posted_data):
            username = data[0]
        else:
            username = posted_data["username"]

        if("first_name" not in posted_data):
            first_name = data[1]
        else:
            first_name = posted_data["first_name"]

        if("last_name" not in posted_data):
            last_name = data[2]
        else:
            last_name = posted_data["last_name"]

        if("email" not in posted_data):
            email = data[3]
        else:
            email = posted_data["email"]

        if("phone" not in posted_data):
            phone = data[4]
        else:
            phone = posted_data["phone"]

        if("address" not in posted_data):
            address = data[5]
        else:
            address = posted_data["address"]

        if("password" not in posted_data or posted_data["password"] == ""):
            password = data[6]
        else:
            password = posted_data["password"]
            password = bcrypt.hashpw(
                password.encode('utf-8'), bcrypt.gensalt())

        query = """
        UPDATE `USERS`
        SET `username`=(%s),`password`=(%s),`first_name`=(%s),`last_name`=(%s),`email`=(%s)
        WHERE user_id = (%s)"""

        cursor.execute(query, (username, password,
                               first_name, last_name, email, uid))

        query = """UPDATE `CUSTOMER` SET `phone`=(%s),`address`=(%s),`email`=(%s) WHERE customer_id=(%s)"""

        cursor.execute(query, (phone, address,
                               email, uid))
        mysql.get_db().commit()
        print(posted_data)
        return jsonify({
            "status_code": 201,
            "message": "ok"
        })


api.add_resource(Auth, "/auth")


class Users(Resource):
    @cross_origin(origins="http://localhost:3000*")
    def post(self):  # registration
        posted_data = request.get_json()

        status_code = check_posted_data(posted_data, "users")

        if (status_code == 200):
            last_name = posted_data["last_name"]
            username = posted_data["username"]
            password = posted_data["password"]
            phone = posted_data["phone"]
            address = posted_data["address"]

            data = find_user(username)

            if (data == None):
                first_name = posted_data["first_name"]
                email = posted_data["email"]
                mail_thread = threading.Thread(
                    target=send_mail, args=(first_name, email))
                mail_thread.start()
                hashed = bcrypt.hashpw(
                    password.encode('utf-8'), bcrypt.gensalt())
                add_user(first_name, last_name, username, hashed, email)
                add_customer(username, phone, address, email)

                retJson = {
                    "message": "Registration completed.",
                    "status_code": 200
                }
                mail_thread.join()
                return retJson

            else:
                return jsonify({
                    "message": "user already exists",
                    "status_code": 409
                })
        else:
            return jsonify({
                "message": "missing arguments",
                "status_code": status_code
            })


api.add_resource(Users, "/users")


class findProduct(Resource):
    @cross_origin(origins="http://localhost:3000*")
    def post(self):  # find product from database
        posted_data = request.get_json()
        productName = posted_data["productName"]
        productName = "%"+productName+"%"
        cursor = mysql.get_db().cursor()

        query = "SELECT name, rating, model, price, image_path, stock, discount FROM PRODUCT WHERE name like (%s)"
        cursor.execute(query, (productName,))
        data = cursor.fetchall()

        data_list = list()

        if (data != None):
            for element in data:
                product = {
                    "name": element[0],
                    "rating": element[1],
                    "model": element[2],
                    "price": element[3],
                    "image_path": element[4],
                    "stock": element[5],
                    "discount":element[6]
                }
                data_list.append(product)
            return jsonify({
                "items": data_list,
                "status_code": 200
            })
        else:
            return jsonify({
                "message": "Item does not exist.",
                "status_code": 409
            })


api.add_resource(findProduct, "/findProduct")


class addProduct(Resource):
    @cross_origin(origins="http://localhost:3000*")
    @private
    def post(self):  # adding new product to database
        posted_data = request.get_json()

        name = posted_data["name"]
        rating = posted_data["rating"]
        model = posted_data["model"]
        price = posted_data["price"]
        image_path = posted_data["image_path"]

        cursor = mysql.get_db().cursor()

        query = "SELECT * FROM PRODUCT WHERE name=(%s)"
        cursor.execute(query, (name,))
        data = cursor.fetchone()

        if(data == None):
            # adding a new product to product table.
            query = "INSERT INTO `PRODUCT` (`name`, `rating`, `model`, `price`, `image_path`) VALUES ((%s), (%s), (%s), (%s), (%s))"
            cursor.execute(query, (name, rating, model, price, image_path))
            mysql.get_db().commit()

            retJson = {
                "message": "New item added..",
                "status_code": 200
            }
            return retJson
        else:
            return jsonify({
                "message": "This item already exists",
                "status_code": 409
            })


api.add_resource(addProduct, "/addProduct")


class addStock(Resource):
    # increasing the stock of the choosen product by the given quantity.
    @cross_origin(origins="http://localhost:3000*")
    def post(self):
        posted_data = request.get_json()

        product_id = posted_data["product_id"]
        quantity = posted_data["quantity"]

        cursor = mysql.get_db().cursor()

        query = "SELECT * FROM PRODUCT WHERE product_id=(%s)"
        cursor.execute(query, (product_id,))
        data = cursor.fetchone()

        if (data != None):
            # query = "INSERT INTO `PRODUCT` (`name`, `rating`, `model`, `price`, `image_path`) VALUES ((%s), (%s), (%s), (%s), (%s))"
            query = "UPDATE PRODUCT SET stock=(%s) WHERE product_id=(%s)"
            cursor.execute(query, (int(data[7] + quantity), product_id))
            mysql.get_db().commit()

            retJson = {
                "message": "Stock of {} increased by {}...".format(product_id, quantity),
                "status_code": 200
            }
            return retJson
        else:
            return jsonify({
                "message": "This item does not exist",
                "status_code": 409
            })


api.add_resource(addStock, "/addStock")


class reduceStock(Resource):
    @cross_origin(origins="http://localhost:3000*")
    @private
    def post(self):  # decreasing the stock of the choosen product by 1.
        posted_data = request.get_json()
        product_id = posted_data["product_id"]
        quantity = posted_data["quantity"]

        cursor = mysql.get_db().cursor()

        query = "SELECT * FROM PRODUCT WHERE product_id=(%s)"
        cursor.execute(query, (product_id,))
        data = cursor.fetchone()

        if (data != None):

            if (int(data[7])-quantity > 0):
                query = "UPDATE PRODUCT SET stock=stock-(%s) WHERE product_id=(%s)"
                cursor.execute(query, (quantity, product_id))
                mysql.get_db().commit()

                retJson = {
                    "message": "Stock of {} reduced by {}...".format(product_id, quantity),
                    "status_code": 200
                }
                return retJson
            else:
                query = "UPDATE PRODUCT SET stock='0' WHERE product_id=(%s)"
                cursor.execute(query, (product_id,))
                mysql.get_db().commit()

                retJson = {
                    "message": "Stock of {} reduced to 0...".format(product_id),
                    "status_code": 200
                }
                return retJson
        else:
            return jsonify({
                "message": "This item does not exist",
                "status_code": 409
            })


api.add_resource(reduceStock, "/reduceStock")


class orderBy(Resource):
    @cross_origin(origins="http://localhost:3000*")
    def post(self):
        posted_data = request.get_json()

        criteria = posted_data["criteria"]
        orderType = posted_data["orderType"]  # order type can be ASC or DESC

        cursor = mysql.get_db().cursor()

        query = "SELECT product_id, name, rating, model, price, image_path, stock, discount FROM PRODUCT ORDER BY {} {}".format(
            criteria, orderType)
        cursor.execute(query)

        datas = cursor.fetchall()
        retJson = {
            "product": [
                {
                    "product_id": data[0],
                    "name":data[1],
                    "rating":data[2],
                    "model":data[3],
                    "price":data[4],
                    "image_path":data[5],
                    "stock":data[6],
                    "discount":data[7]
                }for data in datas],
            "status_code": 200
        }
        return retJson


api.add_resource(orderBy, "/orderBy")


class categoryList(Resource):
    # retrieving all category list from db or only a specific one.
    @cross_origin(origins="http://localhost:3000*")
    def post(self):
        posted_data = request.get_json()
        whichCategory = posted_data["whichCategory"]
        cursor = mysql.get_db().cursor()

        query = "SELECT category_name FROM CATEGORY"
        cursor.execute(query)
        data = cursor.fetchall()
        if whichCategory == "all":
            retJson = {
                "name": data,
                "status_code": 200
            }
            return retJson
        else:
            try:
                intCat = int(whichCategory)
                retJson = {
                    "name": data[intCat],
                    "status_code": 200
                }
                return retJson
            except:
                try:
                    intCat2 = int(whichCategory)
                except:
                    retJson = {
                        "message": "You need to type integer value"
                    }
                    return retJson
                retJson = {
                    "message": "You tried to reach a category which is not exist in database."
                }
                return retJson


api.add_resource(categoryList, "/categoryList")


class productsOfCategory(Resource):
    # retrieving all products which belong to input category name.
    @cross_origin(origins="http://localhost:3000*")
    def post(self):
        posted_data = request.get_json()
        category_name = posted_data["category_name"]
        cursor = mysql.get_db().cursor()

        query = "SELECT C.category_id, product_id, name, rating, model, price, image_path, stock, pm_id, C.category_name, discount FROM PRODUCT P, CATEGORY C WHERE P.category_id = C.category_id AND C.category_name = (%s)"

        if ("lowest_rating" in posted_data):
            query = query + \
                " AND P.rating >= {}".format(posted_data["lowest_rating"])
        if ("highest_rating" in posted_data):
            query = query + \
                " AND P.rating <= {}".format(posted_data["highest_rating"])
        if ("lowest_price" in posted_data):
            query = query + \
                " AND P.price >= {}".format(posted_data["lowest_price"])
        if ("highest_rating" in posted_data):
            query = query + \
                " AND P.rating <= {}".format(posted_data["highest_rating"])

        cursor.execute(query, (category_name, ))
        data = cursor.fetchall()

        data_list = list()
        for info in data:
            data_list.append({
                "category_id": info[0],
                "product_id": info[1],
                "name": info[2],
                "rating": info[3],
                "model": info[4],
                "price": info[5],
                "image_path": info[6],
                "stock": info[7],
                "pm_id": info[8],
                "category_name": info[9],
                "discount": info[10],
            })

        retJson = {
            "category_elements": data_list,
            "status_code": 200
        }
        return retJson


api.add_resource(productsOfCategory, "/productsOfCategory")


class products(Resource):
    @cross_origin(origins="http://localhost:3000*")
    def post(self):

        posted_data = request.get_json()
        cursor = mysql.get_db().cursor()

        query = "SELECT category_id, product_id, name, rating, model, price, image_path, stock, discount FROM PRODUCT"

        if ("lowest_rating" in posted_data or "highest_rating" in posted_data or "lowest_price" in posted_data or "highest_price" in posted_data):
            query = query + " WHERE"

        if ("lowest_rating" in posted_data):
            query = query + " AND" if query[-5:] != "WHERE" else query
            query = query + \
                " rating >= {}".format(posted_data["lowest_rating"])

        if ("highest_rating" in posted_data):
            query = query + " AND" if query[-5:] != "WHERE" else query
            query = query + \
                " rating <= {}".format(posted_data["highest_rating"])

        if ("lowest_price" in posted_data):
            query = query + " AND" if query[-5:] != "WHERE" else query
            query = query + \
                " price >= {}".format(posted_data["lowest_price"])

        if ("highest_price" in posted_data):
            query = query + " AND" if query[-5:] != "WHERE" else query
            query = query + \
                " price <= {}".format(posted_data["highest_price"])

        cursor.execute(query)
        data = cursor.fetchall()

        data_list = list()
        for info in data:
            data_list.append({
                "category_id": info[0],
                "product_id": info[1],
                "name": info[2],
                "rating": info[3],
                "model": info[4],
                "price": info[5],
                "image_path": info[6],
                "stock": info[7],
                "discount": info[8],
            })

        retJson = {
            "category_elements": data_list,
            "status_code": 200
        }
        return retJson


api.add_resource(products, "/products")


class basket(Resource):
    @cross_origin(origins="http://localhost:3000*")
    def post(self):  # add items to basket
        if check_if_user(request):
            customer_id = username_to_id(request.headers["user"])
        else:
            customer_id = -1
        posted_data = request.get_json()
        return_code = check_posted_data(posted_data, "basket_post")
        if (return_code == 200):
            product_name = posted_data["product_name"]
            quantity = posted_data["quantity"]
            cursor = mysql.get_db().cursor()

            # get product id
            query = "SELECT product_id, price, discount FROM PRODUCT WHERE name = (%s)"
            cursor.execute(query, (product_name,))
            product_data = cursor.fetchone()
            product_id = product_data[0]
            discount = product_data[2]
            print("*************")
            print(discount)
            if (float(discount) != 0):
                cost = float(float(product_data[1]) - float(product_data[1])*(float(discount)/100.0))
                print(cost)
            else:
                cost = float(product_data[1])

            # check if product is already in basket
            query = "SELECT quantity FROM `BASKET` WHERE product_id = (%s) AND customer_id = (%s)"
            cursor.execute(query, (product_id, customer_id))
            data = cursor.fetchone()
            if (data is None):
                # add to basket
                print("basket query")
                print(cost)
                query = "INSERT INTO `BASKET`(`cost`, `quantity`, `product_name`, `product_id`, `customer_id`) VALUES ((%s),(%s),(%s),(%s),(%s))"

                cursor.execute(
                    query, (float(cost), quantity, product_name, product_id, customer_id))
                mysql.get_db().commit()
            else:
                quantity = int(data[0])+1
                query = "UPDATE `BASKET` SET quantity=(%s) WHERE product_id=(%s) AND customer_id=(%s)"
                cursor.execute(query, (quantity, product_id, customer_id))
                mysql.get_db().commit()
            retJson = {
                "message": "item added",
                "status_code": 200,
                "customer_id": customer_id
            }

            return retJson

        else:
            return jsonify({
                "message": "Bad Request",
                "status_code": 400
            })

    @cross_origin(origins="http://localhost:3000*")
    def get(self):
        cursor = mysql.get_db().cursor()
        if check_if_user(request):
            customer_id = customer_id = username_to_id(request.headers["user"])
        else:
            customer_id = -1

        # fetch all product_id's
        query = "SELECT product_id, quantity FROM BASKET WHERE customer_id = (%s)"
        cursor.execute(query, (customer_id,))
        product_ids = cursor.fetchall()

        products = list()

        for id, quantity in product_ids:
            query = "SELECT name, model, price, image_path, stock FROM PRODUCT WHERE product_id = (%s)"
            cursor.execute(query, (id,))
            product_info = cursor.fetchone()

            cursor.execute("SELECT cost FROM BASKET WHERE customer_id = (%s) AND product_id = (%s)", (customer_id,id))
            cost = cursor.fetchone()[0]
            products.append({
                "name": product_info[0],
                "model": product_info[1],
                "price": cost,
                "image_path": product_info[3],
                "quantity": quantity,
                "stock": product_info[4]
            })

        return jsonify({
            "products": products,
            "status_code": 200,
            "customer_id": customer_id
        })

    @cross_origin(origins="http://localhost:3000*")
    def delete(self):  # delete an item from basket
        cursor = mysql.get_db().cursor()
        posted_data = request.get_json()
        if (check_posted_data(posted_data, "basket_delete") == 200):
            product_name = posted_data["product_name"]

            if check_if_user(request):
                customer_id = customer_id = username_to_id(
                    request.headers["user"])
            else:
                customer_id = -1

            # get product_id
            query = "SELECT product_id FROM PRODUCT WHERE name = (%s)"
            cursor.execute(query, (product_name,))
            product_id = cursor.fetchone()[0]

            # check if product exists in basket
            query = "SELECT * FROM BASKET WHERE product_id = (%s) AND customer_id = (%s)"
            cursor.execute(query, (product_id, customer_id))
            data = cursor.fetchone()

            if (data is None):
                return({
                    "message": "product not found",
                    "status_code": 404,
                    "customer_id": customer_id
                })

            query = "DELETE FROM BASKET WHERE customer_id = (%s) AND product_id = (%s)"
            cursor.execute(query, (customer_id, product_id))
            mysql.get_db().commit()

            return jsonify({
                "message": "successful",
                "status_code": 200,
                "customer_id": customer_id
            })
        return jsonify({
            "message": "Bad Request",
            "status_code": 403
        })

    @cross_origin(origins="http://localhost:3000*")
    def put(self):  # change quantity of an item from basket
        cursor = mysql.get_db().cursor()
        posted_data = request.get_json()
        if (check_posted_data(posted_data, "basket_put") == 200):
            product_name = posted_data["product_name"]
            quantity = posted_data["quantity"]

            if check_if_user(request):
                customer_id = username_to_id(
                    request.headers["user"])
            else:
                customer_id = -1

            # get product_id
            query = "SELECT product_id FROM PRODUCT WHERE name = (%s)"
            cursor.execute(query, (product_name,))
            product_id = cursor.fetchone()[0]

            query = "UPDATE BASKET SET quantity=(%s) WHERE customer_id = (%s) AND product_id = (%s)"
            cursor.execute(query, (quantity, customer_id, product_id))
            print(query, (quantity, customer_id, product_id))
            mysql.get_db().commit()

            return jsonify({
                "message": "successful",
                "status_code": 200,
                "customer_id": customer_id
            })
        return jsonify({
            "message": "Bad Request",
            "status_code": 403
        })


api.add_resource(basket, "/basket")


class order(Resource):
    def isStockAdequate(self, product_id, quantity):
        cursor = mysql.get_db().cursor()
        query = "SELECT stock FROM `PRODUCT` WHERE product_id=(%s)"
        cursor.execute(query, (product_id,))
        stock = cursor.fetchone()[0]
        if (quantity <= stock):
            return True
        else:
            return False
    
    def getStock(self, product_id):
        cursor = mysql.get_db().cursor()
        query = "SELECT stock FROM `PRODUCT` WHERE product_id=(%s)"
        cursor.execute(query, (product_id,))
        stock = cursor.fetchone()[0]
        return stock

    @private
    @cross_origin(origins="http://localhost:3000*")
    def get(self): #past orders
        cursor = mysql.get_db().cursor()
        customer_id = username_to_id(
            request.headers["user"])
        query = "SELECT cart_id, date_of_purchase, amount, status, order_id FROM `ORDERS` WHERE customer_id = (%s)"
        cursor.execute(query, (customer_id,))

        # get all cart ids from the corresponding user
        orders = cursor.fetchall()

        return_list = list()
        for order in orders:
            # to get product information
            query = "SELECT name, rating, model, price, image_path, stock, product_id amount FROM CART_PRODUCT NATURAL JOIN PRODUCT WHERE cart_id = (%s)"
            cursor.execute(query, (order[0],))
            # products that the corresponding user bought in this particular order
            products = cursor.fetchall()
            
            return_list.append(
                {
                    "cart_id": order[0],
                    "time": str(order[1]),
                    "total_amount": sum([1 for product in products]),
                    "status": order[3],
                    "order_id": order[4],
                    "total_price": sum( [float(product[3]) * float( get_quantity(order[0], product[6]) ) for product in products]),
                    "products": [{
                        "name": product[0],
                        "rating": product[1],
                        "model": product[2],
                        "price": get_basket_price(product[6], order[0]),
                        "image_path": product[4],
                        "stock": product[5],
                        "amount": get_quantity(order[0], product[6])
                    } for product in products]
                }
            )
            
        return jsonify({
            "status_code": 200,
            "orders": return_list
        })

    
    @cross_origin(origins="http://localhost:3000*")
    @private
    def post(self):  # order everything on basket
        cursor = mysql.get_db().cursor()
        customer_id = username_to_id(
            request.headers["user"])

        # add each product to cart
        query = "SELECT cost, quantity, product_id FROM BASKET WHERE customer_id = (%s)"

        cursor.execute(query, (customer_id,))
        elements = cursor.fetchall()

        query = "INSERT INTO `CART`(`customer_id`, `product_id`, `total_cost`, `quantity`) VALUES ((%s),(%s),(%s),(%s))"
        cursor.execute(
            query, (customer_id, 1, 2, 3))

        # get cart id
        query = "SELECT cart_id FROM CART WHERE customer_id = (%s)"
        cursor.execute(query, (customer_id))
        cart_id = cursor.fetchall()[-1]

        # add to orders
        query = "INSERT INTO `ORDERS`(`amount`,`status`,`cart_id`,`customer_id`,`sm_id`, `time`) VALUES ((%s),(%s),(%s),(%s),(%s),(%s))"
        now = datetime.datetime.now()
        dt_string = now.strftime("%H:%M:%S")
        cursor.execute(
            query, (0, "Preparing", cart_id, customer_id, 5, str(dt_string)))

        products_dict = dict() #will be used to send invoice
        for element in elements:
            price = element[0]
            quantity = element[1]
            product_id = element[2]
            if (self.isStockAdequate(product_id, quantity) == False):
                return jsonify({
                    "message": "not adequate stock for at least one item",
                    "status_code": 403
                })

            # update the stock
            query = "UPDATE `PRODUCT` SET `stock`=(%s) WHERE product_id=(%s)"
            new_stock = self.getStock(product_id)-quantity
            cursor.execute(query, (new_stock, product_id))
            

            # add to cart_product
            query = "INSERT INTO `CART_PRODUCT`(`cart_id`,`product_id`,`amount`,`price_with_discount`) VALUES ((%s),(%s),(%s),(%s))"
            cursor.execute(query, (cart_id, product_id, quantity, price))
            

            # remove from basket
            query = "DELETE FROM `BASKET` WHERE product_id = (%s) AND customer_id = (%s)"
            cursor.execute(query, (product_id, customer_id))
            

            #prepare invoice
            product_name = id_to_product(product_id)

            products_dict[product_name+"({})".format(str(quantity))] = str(quantity*price)
        
        
        email = get_email(customer_id)
        #send invoice
        blob = invoice(cart_id, products_dict, email)
        
        mysql.get_db().commit()

        return jsonify({
            "message": "successful",
            "invoice": blob.decode(),
            "status_code": 200
        })


    


class refund(Resource):
    @cross_origin(origins="http://localhost:3000*")
    @private
    def post(self):  # ask for a refund
        posted_data = request.get_json()
        if True:
            cursor = mysql.get_db().cursor()
            customer_id = username_to_id(
                request.headers["user"])
            product_name = posted_data["product_name"]
            amount = posted_data["amount"]

            if (amount <= 0):
                return jsonify({
                    "message":"amount parameter cannot be equal or smaller than zero",
                    "status_code":403
                })

            product_id = product_to_id(product_name)
            query = "SELECT * FROM refund_request WHERE product_id = (%s) AND customer_id =(%s)"
            cursor.execute(query, (product_id, customer_id))
            data = cursor.fetchone()

            if (data != None):
                query = "UPDATE `refund_request` SET `amount`=(%s)  WHERE product_id = (%s) AND customer_id =(%s)"
                cursor.execute(query, (amount, product_id, customer_id))
                mysql.get_db().commit()

                return jsonify({
                    "message":"refund request updated!",
                    "status_code":201
                })

            cart_id = posted_data["cart_id"]

            # check if refund request amount is <= than ordered
            query = """ SELECT CART_PRODUCT.amount
                        FROM ORDERS, CART, CART_PRODUCT, PRODUCT
                        WHERE 
                        ORDERS.cart_id = CART.cart_id AND 
                        CART_PRODUCT.cart_id = CART.cart_id AND 
                        name = (%s) AND 
                        ORDERS.customer_id = (%s) AND 
                        ORDERS.cart_id = (%s) """
            print(query, (str(product_name),
                                   str(customer_id), str(cart_id)))
            cursor.execute(query, (str(product_name),
                                   str(customer_id), str(cart_id)))
            amount_ordered = cursor.fetchone()
            amount_ordered = amount_ordered[0]

            if (int(amount) > int(amount_ordered)):
                return jsonify({
                    "message": "we can't refund you more than you originally ordered",
                    "status_code": 403
                })

            query = "SELECT * FROM ORDERS WHERE customer_id = (%s)"
            cursor.execute(query, (customer_id,))

            query = "INSERT INTO `refund_request`(`product_id`, `customer_id`,`amount`,`cart_id`) VALUES ((%s),(%s),(%s),(%s))"
            cursor.execute(query, (product_id, customer_id, amount, cart_id))
            mysql.get_db().commit()
            

            return jsonify({
                "status_code": check_posted_data(posted_data, "refund/post"),
                "message": "ok"
            })
        else:
            return jsonify({
                "message": "bad request",
                "status_code": check_posted_data(posted_data, "refund/post")})
    @cross_origin(origins="http://localhost:3000*")
    @sales_manager_only
    def get(self):  # get refund requests
        cursor = mysql.get_db().cursor()
        query = """ SELECT username, name, cart_id, refund_request.amount
                    FROM refund_request, USERS, PRODUCT
                    WHERE refund_request.customer_id = USERS.user_id AND PRODUCT.product_id = refund_request.product_id
                """
        cursor.execute(query)
        refund_requests = cursor.fetchall()

        return jsonify({
            "refunds": [
                {
                    "customer": refund_request[0],
                    "product":refund_request[1],
                    "cart_id":refund_request[2],
                    "amount":refund_request[3]
                } for refund_request in refund_requests
            ],
            "status_code": 200
        })
    @cross_origin(origins="http://localhost:3000*")
    @sales_manager_only
    def put(self):  # evaluate refund
        cursor = mysql.get_db().cursor()
        posted_data = request.get_json()
        product_name = posted_data["product_name"]
        customer_name = posted_data["customer_name"]
        decision = posted_data["decision"]

        product_id = product_to_id(product_name)
        customer_id = username_to_id(customer_name)

        if (decision == "reject"):

            query = "DELETE FROM `refund_request` WHERE product_id = (%s) AND customer_id = (%s)"
            cursor.execute(query, (product_id, customer_id))
            mysql.get_db().commit()

            return jsonify({
                "message": "refund request has been rejected",
                "status_code": 201
            })

        elif (decision == "accept"):
            query = "SELECT amount FROM `refund_request` WHERE product_id = (%s) AND customer_id = (%s)"
            cursor.execute(query, (product_id, customer_id))
            amount = cursor.fetchone()

            # increase stock
            increase_stock(product_id, amount)

            # delete refund request
            query = "DELETE FROM `refund_request` WHERE product_id = (%s) AND customer_id = (%s)"
            cursor.execute(query, (product_id, customer_id))
            mysql.get_db().commit()
            return jsonify({
                "amount": amount
            })

class rate(Resource):
    #Adding given rate to database with customer and product name.
    @cross_origin(origins="http://localhost:3000*")
    def post(self):
        posted_data = request.get_json()
        product_name = posted_data["product_name"]
        username = request.headers["user"]
        rate = posted_data["rate"]

        cursor = mysql.get_db().cursor()

        query = "SELECT product_id FROM PRODUCT WHERE name = (%s)"
        cursor.execute(query, (product_name,))
        data = cursor.fetchone()
        product_id = data[0]

        query = "SELECT user_id FROM USERS WHERE username = (%s)"
        cursor.execute(query, (username,))
        data = cursor.fetchone()
        user_id = data[0]


        query = "INSERT INTO `RATES` (`rate`, `customer_id`, `product_id`) VALUES ((%s), (%s), (%s))"
        cursor.execute(query, (rate, user_id, product_id))
        mysql.get_db().commit()

        query = "SELECT * FROM RATES WHERE product_id=(%s)"
        cursor.execute(query, (product_id,))
        rates = cursor.fetchall()
        product_rates = list()
        total = 0
        count = 0
        for rate in rates:
            total += rate[0]
            count += 1
        AVG = total / count

        query = "UPDATE `PRODUCT` SET rating = (%s) WHERE product_id = (%s)"
        cursor.execute(query, (AVG, product_id))
        mysql.get_db().commit()

        retJson = {
                "message": "Rate successfully added to database.",
                "avgRate": AVG,
                "status_code": 200
        }
        return retJson

api.add_resource(rate, "/rate")

class avgRate(Resource):
    #Calculating average rate for given product id.
    @cross_origin(origins="http://localhost:3000*")
    def post(self):
        posted_data = request.get_json()
        product_name = posted_data["product_name"]

        cursor = mysql.get_db().cursor()

        query = "SELECT product_id FROM PRODUCT WHERE name = (%s)"
        cursor.execute(query, (product_name,))
        data = cursor.fetchone()
        product_id = data[0]


        query = "SELECT * FROM RATES WHERE product_id=(%s)"
        cursor.execute(query, (product_id,))
        rates = cursor.fetchall()
        product_rates = list()
        total = 0
        count = 0
        for rate in rates:
            total += rate[0]
            count += 1
        AVG = total / count

        query = "UPDATE `PRODUCT` SET rating = (%s) WHERE product_id = (%s)"
        cursor.execute(query, (AVG, product_id))
        mysql.get_db().commit()

        return jsonify({
            "status_code": 200,
            "rate": AVG
        })

class stock(Resource):
    def isStockAdequate(self, product_id, quantity):
        cursor = mysql.get_db().cursor()
        query = "SELECT stock FROM `PRODUCT` WHERE product_id=(%s)"
        cursor.execute(query, (product_id,))
        stock = cursor.fetchone()[0]
        if (quantity <= stock):
            return True
        else:
            return False
    @cross_origin(origins="http://localhost:3000*")
    def put(self): #change stock
        cursor = mysql.get_db().cursor()
        posted_data = request.get_json()
        product_name = posted_data["product_name"]
        

        query="SELECT * FROM PRODUCT WHERE name=(%s)"
        cursor.execute(query, (product_name,))
        product = cursor.fetchone()
        
        if ("add" in posted_data and product is None and posted_data["add"]):
            print("hy")
            query = """INSERT INTO `PRODUCT`
            (`category_id`, `name`, `model`, `price`, `image_path`, `stock`, `discount`,  `expense`) 
            VALUES ((%s),(%s),(%s),(%s),(%s),(%s),(%s),(%s))"""

            category_id = posted_data["category_id"]
            model = posted_data["model"]
            price = posted_data["price"]
            image_path = posted_data["image_path"]
            stock = posted_data["stock"]
            expense = posted_data["expense"]

            cursor.execute(query, (category_id, product_name, model, price, image_path, stock,"0",expense))
            mysql.get_db().commit()

            return jsonify({
            "status_code": 201,
            "rate": "succeess"
        })
        elif ("remove" in posted_data and posted_data["remove"]):
            query="SELECT * FROM PRODUCT WHERE name=(%s)"
            cursor.execute(query, (product_name,))
            data = cursor.fetchone()
            if (data is None):
                return jsonify({
                    "message":"product does not exist",
                    "status_code":404
                })
            product_id  = product_to_id(product_name)
            
            query = "DELETE FROM `PRODUCT` WHERE product_id = (%s)"
            cursor.execute(query, (product_id))
            mysql.get_db().commit()
        elif ("increase" in posted_data):
            product_id  = product_to_id(product_name)
            increase_stock(product_id, posted_data["increase"])
        elif ("decrease" in posted_data):
            product_id  = product_to_id(product_name)
            if (self.isStockAdequate(product_id, posted_data["decrease"])):
                decrease_stock(product_id, posted_data["decrease"])
                return jsonify({
                    "status_code": 201,
                    "message": "succeess"
                })
            else:
                return jsonify({
                    "status_code": 404,
                    "message": "not enough stock"
                    })
        return jsonify({
            "status_code": 201,
            "message": "succeess"
        })

class changeMail(Resource):
    #Changing mail of the user both from customer and users table. Takes username and new mail as inputs.
    @cross_origin(origins="http://localhost:3000*")
    def post(self):
        posted_data = request.get_json()
        username = posted_data["username"]
        newMail = posted_data["newMail"]

        cursor = mysql.get_db().cursor()

        query = "UPDATE `USERS` SET email = (%s) WHERE username = (%s)"
        cursor.execute(query, (newMail, username))
        mysql.get_db().commit()

        query = "SELECT user_id FROM USERS WHERE username = (%s)"
        cursor.execute(query, (username,))
        userid_data = cursor.fetchone()
        user_id = userid_data[0]

        query = "UPDATE `CUSTOMER` SET email = (%s) WHERE customer_id = (%s)"
        cursor.execute(query, (newMail, user_id))
        mysql.get_db().commit()

        retJson = {
                "message": "Email changed successfully.",
                "status_code": 200
        }
        return retJson

api.add_resource(changeMail, "/changeMail")

class changePhone(Resource):
    #Changing phone number of the customer from customer table. Takes username and new phone number as inputs.
    @cross_origin(origins="http://localhost:3000*")
    def post(self):
        posted_data = request.get_json()
        username = posted_data["username"]
        newPhone = posted_data["newPhone"]

        cursor = mysql.get_db().cursor()

        query = "SELECT user_id FROM USERS WHERE username = (%s)"
        cursor.execute(query, (username,))
        userid_data = cursor.fetchone()
        user_id = userid_data[0]

        query = "UPDATE `CUSTOMER` SET phone = (%s) WHERE customer_id = (%s)"
        cursor.execute(query, (newPhone, user_id))
        mysql.get_db().commit()

        retJson = {
                "message": "Phone number changed successfully.",
                "status_code": 200
        }
        return retJson

api.add_resource(changePhone, "/changePhone")

class changeAddress(Resource):
    #Changing address of the customer from customer table. Takes username and new address as inputs.
    @cross_origin(origins="http://localhost:3000*")
    def post(self):
        posted_data = request.get_json()
        username = posted_data["username"]
        newAddress = posted_data["newAddress"]

        cursor = mysql.get_db().cursor()

        query = "SELECT user_id FROM USERS WHERE username = (%s)"
        cursor.execute(query, (username,))
        userid_data = cursor.fetchone()
        user_id = userid_data[0]

        query = "UPDATE `CUSTOMER` SET address = (%s) WHERE customer_id = (%s)"
        cursor.execute(query, (newAddress, user_id))
        mysql.get_db().commit()

        retJson = {
                "message": "Address changed successfully.",
                "status_code": 200
        }
        return retJson

class pmview(Resource):
    @cross_origin(origins="http://localhost:3000*")
    @product_manager_only
    def get(self):
        cursor = mysql.get_db().cursor()
        query = "SELECT time, status, cart_id, customer_id FROM `ORDERS`"
        cursor.execute(query)
        orders = cursor.fetchall()

        return jsonify({
            "orders":[
                {
                    "time":str(order[0]),
                    "status":order[1],
                    "cart_id":order[2],
                    "customer_id":order[3],

                } for order in orders
            ],
            "status_code":200
        })
    @cross_origin(origins="http://localhost:3000*")
    def post(self): #get invoice, adress, time and phone 
        cursor = mysql.get_db().cursor()
        posted_data = request.get_json()
        cart_id = posted_data["cart_id"]
        query = "SELECT date_of_purchase, address, phone FROM ORDERS, CUSTOMER WHERE ORDERS.customer_id = CUSTOMER.customer_id AND ORDERS.cart_id = (%s)"
        cursor.execute(query,(cart_id,))
        data = cursor.fetchone()

        date_of_purchase = data[0].strftime('%Y-%m-%d %H-%M-%S')
        address = data[1]
        phone = data[2]

        query = "SELECT invoice FROM INVOICE WHERE cart_id = (%s)"
        cursor.execute(query,(cart_id,))
        data = cursor.fetchone()

        if (data is None):
            mystr = "invoice not found"
            mystr_bytes = mystr.encode('ascii')
            invoice = base64.b64encode(mystr_bytes)
        else:
            invoice = data[0]

        query = "SELECT price_with_discount, quantity FROM CART_PRODUCT , CART WHERE CART_PRODUCT.cart_id = (%s) AND CART_PRODUCT.cart_id = CART.cart_id"
        cursor.execute(query,(cart_id,))
        products = cursor.fetchall()


        return jsonify({
            "invoice":invoice.decode(),
            "date_of_purchase": date_of_purchase,
            "address": address,
            "phone": phone,
            "purchased products": [
                {
                    "price_with_discount": product[0],
                    "quantity": product[1]
                } for product in products
            ],
            "status_code":200
        })

    @cross_origin(origins="http://localhost:3000*")
    @product_manager_only
    def put(self): #change status of the order
        cursor = mysql.get_db().cursor()
        posted_data = request.get_json()
        cart_id = posted_data["cart_id"]
        new_status = posted_data["new_status"]

        query = "UPDATE `ORDERS` SET status=(%s) WHERE cart_id = (%s)"
        cursor.execute(query, (new_status, cart_id))
        mysql.get_db().commit()

        return jsonify({
            "status_code":201,
            "message":"success"
        })

class cancelOrder(Resource):
    #Cancelling the order, adding the cancelled amount of the products to stock and changing status of the order as Cancelled.
    @cross_origin(origins="http://localhost:3000*")
    def post(self):
        posted_data = request.get_json()
        order_id = posted_data["order_id"]

        cursor = mysql.get_db().cursor()

        query = "SELECT cart_id FROM ORDERS WHERE order_id = (%s)"
        cursor.execute(query, (order_id,))
        cart = cursor.fetchone()
        cart_id = cart[0]

        query = "SELECT product_id FROM CART_PRODUCT WHERE cart_id = (%s)"
        cursor.execute(query, (cart_id,))
        product_id_list = cursor.fetchall()
        
        query = "SELECT amount FROM CART_PRODUCT WHERE cart_id = (%s)"
        cursor.execute(query, (cart_id,))
        amount_list = cursor.fetchall()

        for i in range(0,len(product_id_list)):
            product_id_var = product_id_list[i]
            amount_list_var = amount_list[i]
            query = "SELECT * FROM PRODUCT WHERE product_id=(%s)"
            cursor.execute(query, (product_id_var[0],))
            data = cursor.fetchone()

            query = "UPDATE PRODUCT SET stock=(%s) WHERE product_id=(%s)"
            cursor.execute(query, (int(data[7] + int(amount_list_var[0])), product_id_var[0]))
            mysql.get_db().commit()

        

        #query = "SELECT * FROM PRODUCT WHERE product_id=(%s)"
        #cursor.execute(query, (product_id,))
        #data = cursor.fetchone()

        #query = "UPDATE PRODUCT SET stock=(%s) WHERE product_id=(%s)"
        #cursor.execute(query, (int(data[7] + int(amountofProduct)), product_id))
        #mysql.get_db().commit()

        #query = "DELETE FROM CART WHERE cart_id = (%s)"
        #cursor.execute(query, (cart_id,))
        #mysql.get_db().commit()

        query = "UPDATE ORDERS SET status = (%s) WHERE order_id = (%s)"
        cursor.execute(query, ("Cancelled", order_id))
        mysql.get_db().commit()

        retJson = {
                "message": "Order canceled successfully.",
                "status_code": 200
        }
        return retJson


class change_price(Resource):
    @cross_origin(origins="http://localhost:3000*")
    def post(self): # change price of a product
        cursor = mysql.get_db().cursor()
        posted_data = request.get_json()
        product_name = posted_data["product_name"]
        new_price = posted_data["new_price"]
        product_id = product_to_id(product_name)

        query = "UPDATE `PRODUCT` SET `price`=(%s) WHERE product_id = (%s)"
        cursor.execute(query, (new_price, product_id))
        mysql.get_db().commit()

        return jsonify({
            "message":"success",
            "status_code": 201
        })

class discount(Resource):
    @cross_origin(origins="http://localhost:3000*")
    def post(self): # change discount of a product
        cursor = mysql.get_db().cursor()
        posted_data = request.get_json()
        product_name = posted_data["product_name"]
        discount = posted_data["discount"]
        product_id = product_to_id(product_name)

        query = "UPDATE `PRODUCT` SET `discount`=(%s) WHERE product_id = (%s)"
        cursor.execute(query, (discount, product_id))
        mysql.get_db().commit()

        return jsonify({
            "message":"success",
            "status_code": 201
        })

class viewInvoices(Resource):
    @cross_origin(origins="http://localhost:3000*")
    def post(self):
        cursor = mysql.get_db().cursor()
        posted_data = request.get_json()
        start_date = posted_data["start_date"]
        end_date = posted_data["end_date"]

        query = "SELECT invoice FROM ORDERS, INVOICE WHERE INVOICE.cart_id = ORDERS.order_id AND date_of_purchase >= (%s) AND date_of_purchase <= (%s)"
        cursor.execute(query, (start_date, end_date))

        invoices = cursor.fetchall()

        return jsonify({
            "invoices": [invoice[0].decode() for invoice in invoices],
            "status_code":200
        })

class stonks(Resource):
    @cross_origin(origins="http://localhost:3000*")
    @sales_manager_only
    def post(self): 
        cursor = mysql.get_db().cursor()
        posted_data = request.get_json()
        start_date = posted_data["start_date"]
        end_date = posted_data["end_date"]

        #calculate expense
        query = "SELECT expense, stock FROM PRODUCT WHERE when_purchased >= (%s) AND when_purchased <= (%s)"
        cursor.execute(query, (start_date, end_date))

        total_expense = 0
        expenses = cursor.fetchall()

        for expense in expenses:
            total_expense += expense[0]*expense[1]
        
        #calculate revenue

        query = "SELECT CART_PRODUCT.amount, price_with_discount FROM ORDERS, CART_PRODUCT WHERE ORDERS.cart_id = CART_PRODUCT.cart_id AND ORDERS.date_of_purchase >= (%s) AND ORDERS.date_of_purchase <= (%s)"
        cursor.execute(query, (start_date, end_date))

        total_revenue = 0
        revenues = cursor.fetchall()

        for revenue in revenues:
            total_revenue += float(revenue[0]) * revenue[1]
        
        
        return jsonify({
            "expenses":total_expense,
            "revenue":total_revenue,
            "profit":total_revenue-total_expense
        })

api.add_resource(stonks, "/stonks")
api.add_resource(viewInvoices, "/viewinvoices")
api.add_resource(discount, "/discount")
api.add_resource(cancelOrder, "/cancelOrder")
api.add_resource(change_price, "/change_price")
api.add_resource(pmview, "/pmview")
api.add_resource(changeAddress, "/changeAddress")
api.add_resource(stock, "/stock")
api.add_resource(avgRate, "/avgRate")
api.add_resource(order, "/order")
api.add_resource(refund, "/refund")


if __name__ == "__main__":
    app.run(debug=True)
# with app.app_context():
#    cursor = mysql.get_db().cursor()
#    query = "INSERT INTO USERS (username, password, first_name, last_name) VALUES(%s,%s,%s,%s)"
#    cursor.execute(query, ("alperenn2", "12345", "alperen", "yıldız"))
#    mysql.get_db().commit()
# with app.app_context():
#    cursor = mysql.get_db().cursor()
#    query = "SELECT * FROM USERS WHERE username=(%s) and password=(%s)"
#    cursor.execute(query, ("albertlevi", "albert123"))
#    data = cursor.fetchone()
#    print(data)
