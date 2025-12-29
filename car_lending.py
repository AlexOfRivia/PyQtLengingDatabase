import sys
import bcrypt
import json
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from PyQt6 import QtSql
from PyQt6.QtCore import Qt
from PyQt6.QtSql import QSqlQuery, QSqlDatabase 
from PyQt6.QtWidgets import QApplication, QWidget, QTableView, QHBoxLayout, QStackedLayout, QStackedWidget, QVBoxLayout, QLabel, QPushButton, QComboBox, QLineEdit, QAbstractItemView, QDialog

#This app will manage car lending records using a SQLite database and PyQt6 for the GUI.
#edding, editing and deleting: customers, cars and lending records.
#But also there should be an option for showing a graph of lending statistics using matplotlib (plus options for choosing graph type using a combo box).
#the graph should be updated in real time using QTimer
#the graph must be shown in the app window (not in a separate window), preferably in the lendings view.

class CarLendingApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Car Lending Management System")
        self.setGeometry(100, 100, 800, 600)
        
        self.db = self.init_db()
        self.init_ui()
        
    def init_db(self):
        db = QSqlDatabase.addDatabase("QSQLITE")
        db.setDatabaseName("car_lending.db")
        if not db.open():
            print("Unable to open database")
            sys.exit(1)
        
        query = QSqlQuery()
        query.exec("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                email TEXT
            )
        """)
        query.exec("""
            CREATE TABLE IF NOT EXISTS cars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                make TEXT,
                model TEXT,
                year INTEGER
            )
        """)
        query.exec("""
            CREATE TABLE IF NOT EXISTS lendings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER,
                car_id INTEGER,
                lending_date TEXT,
                return_date TEXT,
                FOREIGN KEY(customer_id) REFERENCES customers(id),
                FOREIGN KEY(car_id) REFERENCES cars(id)
            )
        """)
        
        return db
    
    def init_ui(self):
        #implementing also other buttons for different views (customers, cars, lendings)
        #the ui should have switching between different views (customers, cars, lendings)
        #in the lendings view there should be also a button for showing a graph of lending statistics using matplotlib (plus options for choosing graph type using a combo box).
        #view could be implemented using stackedLayout
        #alco should be buttons on top for switching between views
        main_layout = QVBoxLayout()
        button_layout = QHBoxLayout() #layout for buttons used to switch between tabs
        self.stacked_layout = QStackedLayout() #stackedlayout for "storing" the views
        main_layout.addLayout(button_layout)
        main_layout.addLayout(self.stacked_layout)
        self.setLayout(main_layout)

        customers_button = QPushButton("Customers")
        cars_button = QPushButton("Cars")
        lendings_button = QPushButton("Lendings")

        #switching buttons
        button_layout.addWidget(customers_button)
        button_layout.addWidget(cars_button)
        button_layout.addWidget(lendings_button)

        #connecting buttons to switching views
        customers_button.clicked.connect(lambda: self.stacked_layout.setCurrentIndex(0)) #customers
        cars_button.clicked.connect(lambda: self.stacked_layout.setCurrentIndex(1)) #cars
        lendings_button.clicked.connect(lambda: self.stacked_layout.setCurrentIndex(2)) #lendnings

        #initializing views
        self.init_customers_view()
        self.init_cars_view()
        self.init_lendings_view()

    #initializing customers view
    def init_customers_view(self):
        customers_widget = QWidget()
        customers_layout = QVBoxLayout()
        customers_widget.setLayout(customers_layout)
        
        self.customers_table = QTableView() #table to store customers
        self.customers_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        customers_layout.addWidget(self.customers_table)
        
        buttons_layout = QHBoxLayout()

        #buttons
        add_button = QPushButton("Add Customer")
        edit_button = QPushButton("Edit Customer")
        delete_button = QPushButton("Delete Customer")
        buttons_layout.addWidget(add_button)

        buttons_layout.addWidget(edit_button)
        buttons_layout.addWidget(delete_button)
        customers_layout.addLayout(buttons_layout)
        
        add_button.clicked.connect(self.add_customer_record)
        edit_button.clicked.connect(self.edit_customer_record)
        delete_button.clicked.connect(self.delete_customer_record)
        
        self.stacked_layout.addWidget(customers_widget)
        
        self.load_record_data("customers")

    #initializing cars view
    def init_cars_view(self):
        cars_widget = QWidget()
        cars_layout = QVBoxLayout()
        cars_widget.setLayout(cars_layout)
        
        self.cars_table = QTableView()
        self.cars_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        cars_layout.addWidget(self.cars_table)
        
        buttons_layout = QHBoxLayout()
        
        #buttons
        add_button = QPushButton("Add Car")
        edit_button = QPushButton("Edit Car")
        delete_button = QPushButton("Delete Car")

        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(edit_button)
        buttons_layout.addWidget(delete_button)
        cars_layout.addLayout(buttons_layout)
        
        add_button.clicked.connect(self.add_car_record)
        edit_button.clicked.connect(self.edit_car_record)
        delete_button.clicked.connect(self.delete_car_record)
        
        self.stacked_layout.addWidget(cars_widget)
        
        self.load_record_data("cars")
        
    #initializing lendings view
    def init_lendings_view(self):
        lendings_widget = QWidget()
        lendings_layout = QVBoxLayout()
        lendings_widget.setLayout(lendings_layout)
        
        self.lendings_table = QTableView()
        self.lendings_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        lendings_layout.addWidget(self.lendings_table)
        
        buttons_layout = QHBoxLayout()

        #buttons
        add_button = QPushButton("Add Lending")
        edit_button = QPushButton("Edit Lending")
        delete_button = QPushButton("Delete Lending")

        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(edit_button)
        buttons_layout.addWidget(delete_button)
        lendings_layout.addLayout(buttons_layout)
        
        add_button.clicked.connect(self.add_lending_record)
        edit_button.clicked.connect(self.edit_lending_record)
        delete_button.clicked.connect(self.delete_lending_record)

        #graph button and combo box for choosing graph type
        #FigureCanvasQTAgg for embedding matplotlib graph in PyQt6
        graph_button = QPushButton("Show Lending Statistics Graph")
        self.graph_type_combo = QComboBox()
        self.graph_type_combo.addItems(["Bar Chart", "Line Chart", "Pie Chart"])
        buttons_layout.addWidget(graph_button)
        buttons_layout.addWidget(self.graph_type_combo)
        graph_button.clicked.connect(self.show_lending_graph)


        
        self.stacked_layout.addWidget(lendings_widget)
        
        self.load_record_data("lendings")
        
    #managing records methods
    def add_customer_record(self):
        #opening a dialog for adding a new customer record
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Customer")
        layout = QVBoxLayout()
        dialog.setLayout(layout)

        #input fields
        name_input = QLineEdit()
        email_input = QLineEdit()

        layout.addWidget(QLabel("Name:"))
        layout.addWidget(name_input)
        layout.addWidget(QLabel("Email:"))

        layout.addWidget(email_input)
        buttons_layout = QHBoxLayout()

        #buttons
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")

        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_button)
        layout.addLayout(buttons_layout)

        save_button.clicked.connect(lambda: self.save_new_record(dialog, "customers", ["name", "email"], [name_input.text(), email_input.text()]))
        cancel_button.clicked.connect(dialog.reject)
        
        dialog.exec()

        #updating the customers table view
        self.load_record_data("customers")

    #universal method for saving new records to the database
    def save_new_record(self, dialog, table, fields, values):
        placeholders = ", ".join(["?"] * len(values))
        query_str = f"INSERT INTO {table} ({', '.join(fields)}) VALUES ({placeholders})"
        query = QSqlQuery()
        query.prepare(query_str)
        for value in values:
            query.addBindValue(value)
        if not query.exec():
            print(f"Failed to add record to {table}:", query.lastError().text())
        else:
            dialog.accept()
            self.load_record_data(table)

    #universal method for loading data from a table
    def load_record_data(self, table):
        model = QtSql.QSqlTableModel()
        model.setTable(table)
        model.select()
        if table == "customers":
            self.customers_table.setModel(model)  
        elif table == "cars":
            self.cars_table.setModel(model)
        elif table == "lendings":
            self.lendings_table.setModel(model)  

    def edit_record(self):
        pass  #implementation for editing a record
    
    def delete_record(self):
        pass  #implementation for deleting a record   

    #method for showing lending graph
    def show_lending_graph(self):
        pass  #implementation for showing lending statistics graph

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CarLendingApp()
    window.show()
    sys.exit(app.exec())