import mysql.connector

mydb = mysql.connector.connect(
  host="localhost",
  user="root",
  password="dominique59",
  database="store"
)

mycursor = mydb.cursor()

mycursor.execute("CREATE TABLE product (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255), description TEXT, price INT, quantity INT, id_category INT)")

mycursor.execute("CREATE TABLE category (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(255))")