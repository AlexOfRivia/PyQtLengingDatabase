import sys

from PyQt6 import QtCore
import bcrypt
import json
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from PyQt6 import QtSql
from PyQt6.QtCore import Qt
from PyQt6.QtSql import QSqlQuery, QSqlDatabase 
from PyQt6.QtWidgets import QDateEdit, QApplication, QSpinBox, QWidget, QTableView, QHBoxLayout, QStackedLayout, QStackedWidget, QVBoxLayout, QLabel, QPushButton, QComboBox, QLineEdit, QAbstractItemView, QDialog

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
        graph_button.clicked.connect(lambda: self.show_lending_graph(self.graph_type_combo.currentText()))
        
        self.stacked_layout.addWidget(lendings_widget)
        
        self.load_record_data("lendings")


    #----------------------customer methods----------------------------

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

        save_button.clicked.connect(lambda: self.save_new_record(dialog, "customers", ["name", "email"], [name_input.text().strip(), email_input.text().strip()]))
        cancel_button.clicked.connect(dialog.reject)
        
        dialog.exec()

        #updating the customers table view
        self.load_record_data("customers")

    def edit_customer_record(self):
        selected_index = self.customers_table.currentIndex() #getting the selected row index
        if not selected_index.isValid():
            messagebox = QDialog(self)
            messagebox.setWindowTitle("No Selection")
            layout = QVBoxLayout()
            messagebox.setLayout(layout)    
            layout.addWidget(QLabel("No customer selected for editing."))
            ok_button = QPushButton("OK")
            ok_button.clicked.connect(messagebox.accept)
            layout.addWidget(ok_button)
            messagebox.exec()
            return  #no selection made
                
        selected_id = self.customers_table.model().data(self.customers_table.model().index(selected_index.row(), 0))
       
        selected_id = self.customers_table.model().data(self.customers_table.model().index(selected_index.row(), 0))

        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Customer")
        layout = QVBoxLayout()
        dialog.setLayout(layout)

        #input fields
        name_input = QLineEdit()
        email_input = QLineEdit()

        #setting input fields text to current data
        name_input.setText(self.customers_table.model().data(self.customers_table.model().index(selected_index.row(), 1)))
        email_input.setText(self.customers_table.model().data(self.customers_table.model().index(selected_index.row(), 2)))

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

        save_button.clicked.connect(lambda: self.edit_record(dialog, "customers", selected_id, ["name", "email"], [name_input.text().strip(), email_input.text().strip()]))
        cancel_button.clicked.connect(dialog.reject)
        dialog.exec()

        self.load_record_data("customers")
    
    def delete_customer_record(self):
        selected_index = self.customers_table.currentIndex() #getting the selected row index
        if not selected_index.isValid():
            messagebox = QDialog(self)
            messagebox.setWindowTitle("No Selection")
            layout = QVBoxLayout()
            messagebox.setLayout(layout)    
            layout.addWidget(QLabel("No customer selected for deletion."))
            ok_button = QPushButton("OK")
            ok_button.clicked.connect(messagebox.accept)
            layout.addWidget(ok_button)
            messagebox.exec()
            return  #no selection made
                
        selected_id = self.customers_table.model().data(self.customers_table.model().index(selected_index.row(), 0))

        dialog = QDialog(self)
        dialog.setWindowTitle("Delete Customer")
        layout = QVBoxLayout()
        dialog.setLayout(layout)

        layout.addWidget(QLabel("Are you sure you want to delete this customer?"))

        buttons_layout = QHBoxLayout()

        #buttons
        delete_button = QPushButton("Delete")
        cancel_button = QPushButton("Cancel")

        buttons_layout.addWidget(delete_button)
        buttons_layout.addWidget(cancel_button)
        layout.addLayout(buttons_layout)

        delete_button.clicked.connect(lambda: self.delete_record(dialog, "customers", selected_id))
        cancel_button.clicked.connect(dialog.reject)
        dialog.exec()

        self.load_record_data("customers")

    #---------------------------------------------------

    #-----------------lending methods--------------------

    def add_lending_record(self):
        if self.customers_table.model().rowCount() == 0 or self.cars_table.model().rowCount() == 0: #checking if there are customers and cars in the db
            messagebox = QDialog(self)
            messagebox.setWindowTitle("Input Error")
            layout = QVBoxLayout()
            messagebox.setLayout(layout)
            layout.addWidget(QLabel("There must be at least one customer and one car in the database to add a lending record."))
            ok_button = QPushButton("OK")
            ok_button.clicked.connect(messagebox.accept)
            layout.addWidget(ok_button)
            messagebox.exec()
            return

         #opening a dialog for adding a new lending record

        dialog = QDialog(self)
        dialog.setWindowTitle("Add Lending")
        layout = QVBoxLayout()
        dialog.setLayout(layout)

        #input fields
        customer_id_input = QSpinBox()
        car_id_input = QSpinBox()
        lending_date_input = QDateEdit()
        lending_date_input.setCalendarPopup(True)
        return_date_input = QDateEdit()
        return_date_input.setCalendarPopup(True)
        
        #setting default dates to current date
        lending_date_input.setDateTime(QtCore.QDateTime.currentDateTime())
        return_date_input.setDateTime(QtCore.QDateTime.currentDateTime())
        customer_id_input.setRange(0, self.customers_table.model().rowCount()) #setting max range to number of customers
        car_id_input.setRange(0, self.cars_table.model().rowCount()) #setting max range to number of cars

        layout.addWidget(QLabel("Customer ID:"))
        layout.addWidget(customer_id_input)
        layout.addWidget(QLabel("Car ID:"))
        layout.addWidget(car_id_input)
        layout.addWidget(QLabel("Lending Date (YYYY-MM-DD):"))
        layout.addWidget(lending_date_input)
        layout.addWidget(QLabel("Return Date (YYYY-MM-DD):"))
        layout.addWidget(return_date_input)
        buttons_layout = QHBoxLayout()

        #buttons
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")

        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_button)

        layout.addLayout(buttons_layout)

        save_button.clicked.connect(lambda: self.save_new_record(dialog, "lendings", ["customer_id", "car_id", "lending_date", "return_date"], [customer_id_input.value(), car_id_input.value(), lending_date_input.text(), return_date_input.text()]))
        cancel_button.clicked.connect(dialog.reject)

        dialog.exec()

        #updating the lendings table view
        self.load_record_data("lendings")

    def edit_lending_record(self):
        current_index = self.lendings_table.currentIndex()
        if not current_index.isValid():
            messagebox = QDialog(self)
            messagebox.setWindowTitle("No Selection")
            layout = QVBoxLayout()
            messagebox.setLayout(layout)    
            layout.addWidget(QLabel("No lending selected for editing."))
            ok_button = QPushButton("OK")
            ok_button.clicked.connect(messagebox.accept)
            layout.addWidget(ok_button)
            messagebox.exec()
            return  #no selection made
                
        selected_id = self.lendings_table.model().data(self.lendings_table.model().index(current_index.row(), 0))

        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Lending")

        layout = QVBoxLayout()
        dialog.setLayout(layout)

        #input fields
        customer_id_input = QSpinBox()
        customer_id_input.setRange(0, self.customers_table.model().rowCount()) #setting max range to number of customers
        car_id_input = QSpinBox()
        car_id_input.setRange(0, self.cars_table.model().rowCount()) #setting max range to number of cars
        lending_date_input = QDateEdit()
        lending_date_input.setCalendarPopup(True)
        return_date_input = QDateEdit()
        return_date_input.setCalendarPopup(True)
        
        #setting input fields text to current data
        customer_id_input.setValue(self.lendings_table.model().data(self.lendings_table.model().index(current_index.row(), 1)))
        car_id_input.setValue(self.lendings_table.model().data(self.lendings_table.model().index(current_index.row(), 2)))
        
        lending_date_input.setDateTime(QtCore.QDateTime.fromString(self.lendings_table.model().data(self.lendings_table.model().index(current_index.row(), 3)), "dd.MM.yyyy"))
        return_date_input.setDateTime(QtCore.QDateTime.fromString(self.lendings_table.model().data(self.lendings_table.model().index(current_index.row(), 4)), "dd.MM.yyyy"))

        layout.addWidget(QLabel("Customer ID:"))
        layout.addWidget(customer_id_input)
        layout.addWidget(QLabel("Car ID:"))
        layout.addWidget(car_id_input)
        layout.addWidget(QLabel("Lending Date (YYYY-MM-DD):"))
        layout.addWidget(lending_date_input)
        layout.addWidget(QLabel("Return Date (YYYY-MM-DD):"))
        layout.addWidget(return_date_input)
        buttons_layout = QHBoxLayout()
        
        #buttons
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_button)
        layout.addLayout(buttons_layout)
        save_button.clicked.connect(lambda: self.edit_record(dialog, "lendings", selected_id, ["customer_id", "car_id", "lending_date", "return_date"], [customer_id_input.value(), car_id_input.value(), lending_date_input.text(), return_date_input.text()]))
        cancel_button.clicked.connect(dialog.reject)

        dialog.exec()

        self.load_record_data("lendings")


    def delete_lending_record(self):
        selected_index = self.lendings_table.currentIndex() #getting the selected row index
        if not selected_index.isValid():
            messagebox = QDialog(self)
            messagebox.setWindowTitle("No Selection")
            layout = QVBoxLayout()
            messagebox.setLayout(layout)    
            layout.addWidget(QLabel("No lending selected for deletion."))
            ok_button = QPushButton("OK")
            ok_button.clicked.connect(messagebox.accept)
            layout.addWidget(ok_button)
            messagebox.exec()
            return  #no selection made
        
        selected_id = self.lendings_table.model().data(self.lendings_table.model().index(selected_index.row(), 0))
        dialog = QDialog(self)
        dialog.setWindowTitle("Delete Lending")
        layout = QVBoxLayout()
        dialog.setLayout(layout)
        layout.addWidget(QLabel("Are you sure you want to delete this lending record?"))
        buttons_layout = QHBoxLayout()
        
        #buttons
        delete_button = QPushButton("Delete")
        cancel_button = QPushButton("Cancel")
        
        buttons_layout.addWidget(delete_button)
        buttons_layout.addWidget(cancel_button)
        
        layout.addLayout(buttons_layout)
        delete_button.clicked.connect(lambda: self.delete_record(dialog, "lendings", selected_id))
        cancel_button.clicked.connect(dialog.reject)
        
        dialog.exec()

        #updating the lendings table view
        self.load_record_data("lendings")

    #---------------------------------------------
    

    #-------------car method------------------

    def add_car_record(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Car")
        layout = QVBoxLayout()
        dialog.setLayout(layout)

        #input fields
        make_input = QLineEdit()
        model_input = QLineEdit()
        year_input = QSpinBox()
        year_input.setRange(1900, 2100)

        layout.addWidget(QLabel("Make:"))
        layout.addWidget(make_input)
        layout.addWidget(QLabel("Model:"))
        layout.addWidget(model_input)
        layout.addWidget(QLabel("Year:"))
        layout.addWidget(year_input)

        buttons_layout = QHBoxLayout()

        #buttons
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")

        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_button)
        layout.addLayout(buttons_layout)

        save_button.clicked.connect(lambda: self.save_new_record(dialog, "cars", ["make", "model", "year"], [make_input.text().strip(), model_input.text().strip(), year_input.value()]))
        cancel_button.clicked.connect(dialog.reject)
        
        dialog.exec()

        #updating the cars table view
        self.load_record_data("cars")

    def edit_car_record(self):
        current_index = self.cars_table.currentIndex()
        if not current_index.isValid():
            messagebox = QDialog(self)
            messagebox.setWindowTitle("No Selection")
            layout = QVBoxLayout()
            messagebox.setLayout(layout)    
            layout.addWidget(QLabel("No car selected for editing."))
            ok_button = QPushButton("OK")
            ok_button.clicked.connect(messagebox.accept)
            layout.addWidget(ok_button)
            messagebox.exec()
            return  #no selection made
                
        selected_id = self.customers_table.model().data(self.customers_table.model().index(current_index.row(), 0))

        selected_id = self.cars_table.model().data(self.cars_table.model().index(current_index.row(), 0))

        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Car")
        layout = QVBoxLayout()
        dialog.setLayout(layout)

        #input fields
        make_input = QLineEdit()
        model_input = QLineEdit()
        year_input = QSpinBox()
        year_input.setRange(1900, 2100)

        #setting input fields text to current data
        make_input.setText(self.cars_table.model().data(self.cars_table.model().index(current_index.row(), 1)))
        model_input.setText(self.cars_table.model().data(self.cars_table.model().index(current_index.row(), 2)))
        year_input.setValue(int(self.cars_table.model().data(self.cars_table.model().index(current_index.row(), 3))))
        
        layout.addWidget(QLabel("Make:"))
        layout.addWidget(make_input)
        layout.addWidget(QLabel("Model:"))
        layout.addWidget(model_input)
        layout.addWidget(QLabel("Year:"))
        layout.addWidget(year_input)
        buttons_layout = QHBoxLayout()
        
        #buttons
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")
        
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_button)
        layout.addLayout(buttons_layout)
        
        save_button.clicked.connect(lambda: self.edit_record(dialog, "cars", selected_id, ["make", "model", "year"], [make_input.text().strip(), model_input.text().strip(), year_input.value()]))
        cancel_button.clicked.connect(dialog.reject)
        
        dialog.exec()
        
        self.load_record_data("cars")


    def delete_car_record(self):
        selected_index = self.cars_table.currentIndex() #getting the selected row index
        if not selected_index.isValid():
            messagebox = QDialog(self)
            messagebox.setWindowTitle("No Selection")
            layout = QVBoxLayout()
            messagebox.setLayout(layout)    
            layout.addWidget(QLabel("No car selected for deletion."))
            ok_button = QPushButton("OK")
            ok_button.clicked.connect(messagebox.accept)
            layout.addWidget(ok_button)
            messagebox.exec()
            return  #no selection made
                
        selected_id = self.cars_table.model().data(self.cars_table.model().index(selected_index.row(), 0))

        dialog = QDialog(self)
        dialog.setWindowTitle("Delete Car")
        layout = QVBoxLayout()
        dialog.setLayout(layout)

        layout.addWidget(QLabel("Are you sure you want to delete this car?"))

        buttons_layout = QHBoxLayout()

        #buttons
        delete_button = QPushButton("Delete")
        cancel_button = QPushButton("Cancel")

        buttons_layout.addWidget(delete_button)
        buttons_layout.addWidget(cancel_button)
        layout.addLayout(buttons_layout)

        delete_button.clicked.connect(lambda: self.delete_record(dialog, "cars", selected_id))
        
        cancel_button.clicked.connect(dialog.reject)
        dialog.exec()

        self.load_record_data("cars")
    #--------------------------------------------------------------------

    #------------------------universal methods---------------------------

    #universal method for saving new records to the database
    def save_new_record(self, dialog, table, fields, values):
        #checking, if none of the values are empty
        for value in values:
            if value == "":
                #throwing an error message box
                messagebox = QDialog(self)
                messagebox.setWindowTitle("Input Error")
                layout = QVBoxLayout()
                messagebox.setLayout(layout)
                layout.addWidget(QLabel("All fields must be filled out."))
                ok_button = QPushButton("OK")
                ok_button.clicked.connect(messagebox.accept)
                layout.addWidget(ok_button)
                messagebox.exec()
                dialog.reject()
                return

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

    #universal method for editing records in the database
    def edit_record(self, dialog, table, record_id, fields, values):
        set_clause = ", ".join([f"{field} = ?" for field in fields])
        query_str = f"UPDATE {table} SET {set_clause} WHERE id = ?"
        query = QSqlQuery()
        query.prepare(query_str)
        for value in values:
            query.addBindValue(value)
        query.addBindValue(record_id)
        if not query.exec():
            print(f"Failed to edit record in {table}:", query.lastError().text())
        else:
            dialog.accept()
            self.load_record_data(table)
    
    #universal method for deleting records from the database
    def delete_record(self, dialog, table, record_id):
        query_str = f"DELETE FROM {table} WHERE id = ?"
        query = QSqlQuery()  
        query.prepare(query_str)
        query.addBindValue(record_id)
        if not query.exec():
            print(f"Failed to delete record from {table}:", query.lastError().text())
        else:
            dialog.accept()
            self.load_record_data(table)

    #----------------------------------------------------------------------------------


    #method for showing lending graph
    def show_lending_graph(self, graph_type):
        #using the FigureCanvasQTAgg, NavigationToolbar2QT from matplotlib.backends.backend_qt5agg

        #fetching lending data from the database
        query = QSqlQuery("SELECT lending_date, COUNT(*) as count FROM lendings GROUP BY lending_date")
        dates = []
        counts = []
        while query.next():
            dates.append(query.value(0))
            counts.append(query.value(1))
        #creating the matplotlib figure
        from matplotlib.figure import Figure
        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)
        if graph_type == "Bar Chart":
            ax.bar(dates, counts)
        elif graph_type == "Line Chart":
            ax.plot(dates, counts)
        elif graph_type == "Pie Chart":
            ax.pie(counts, labels=dates, autopct='%1.1f%%')
        ax.set_title("Lending Statistics")
        ax.set_xlabel("Lending Date")
        ax.set_ylabel("Number of Lendings")
        #embedding the figure in the PyQt6 application
        canvas = FigureCanvasQTAgg(fig)
        toolbar = NavigationToolbar2QT(canvas, self)
        graph_dialog = QDialog(self)
        graph_dialog.setWindowTitle("Lending Statistics Graph")
        graph_layout = QVBoxLayout()
        graph_dialog.setLayout(graph_layout)
        graph_layout.addWidget(toolbar)
        graph_layout.addWidget(canvas)
        
        graph_dialog.exec()


        
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CarLendingApp()
    window.show()
    sys.exit(app.exec())