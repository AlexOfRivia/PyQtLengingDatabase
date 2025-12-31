import sys
from PyQt6 import QtCore
import bcrypt
import json
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from PyQt6 import QtSql
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtSql import QSqlQuery, QSqlDatabase 
from PyQt6.QtWidgets import QDateEdit, QApplication, QSpinBox, QWidget, QTableView, QHBoxLayout, QStackedLayout, QVBoxLayout, QLabel, QPushButton, QComboBox, QLineEdit, QAbstractItemView, QDialog, QSizePolicy, QHeaderView
from matplotlib.figure import Figure
from matplotlib import pyplot as plt
import colorsys
from matplotlib import colors as mcolors

class CarLendingApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Car Lending Management System")
        self.setGeometry(100, 100, 1200, 600)
        
        self.db = self.init_db()
        
        #initializing the timer for real-time graph updates
        self.graph_timer = QTimer(self)
        self.graph_timer.setInterval(2000) #every 2 secs
        self.graph_timer.timeout.connect(self.refresh_graph)
        
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

    def apply_stylesheet(self):
        """Apply a sleek dark stylesheet with rounded corners."""
        style = """
        QWidget {
            background-color: #121212;
            color: #e0e0e0;
            font-family: "Segoe UI", Roboto, Arial, sans-serif;
            font-size: 12px;
        }
        QListView, QTreeView {
            background-color: #1e1e1e;
            border: 1px solid #2a2a2a;
            selection-background-color: #2a76d2;
            border-radius: 8px;
            gridline-color: #2a2a2a;
        }
        QTableView {
            background-color: #1e1e1e;
            border: 1px solid #2a2a2a;
            selection-background-color: #2a76d2;
            border-radius: 0px;
            gridline-color: #2a2a2a;
        }
        QPushButton {
            background-color: #1f2933;
            color: #e6eef8;
            border: 1px solid #2f3a45;
            padding: 6px 12px;
            border-radius: 10px;
        }
        QPushButton:hover { background-color: #26313b; }
        QPushButton:pressed { background-color: #1b2227; }
        QComboBox, QLineEdit, QSpinBox, QDateEdit {
            background-color: #161616;
            color: #e0e0e0;
            border: 1px solid #2a2a2a;
            padding: 5px;
            border-radius: 8px;
        }
        QLabel { color: #d4d7db; }
        QHeaderView::section { background-color: #1e1e1e; color: #cfd8e3; border: none; border-radius: 0px; }
        QMenuBar { background-color: transparent; }
        QDialog { background-color: #141414; }
        QScrollBar:vertical {
            background: #151515;
            width: 10px;
            margin: 0px 0px 0px 0px;
            border-radius: 5px;
        }
        QScrollBar::handle:vertical {
            background: #2a2a2a;
            min-height: 20px;
            border-radius: 5px;
        }
        QToolTip { background-color: #2a2a2a; color: #f0f0f0; border: 1px solid #3a3a3a; }
        """
        self.setStyleSheet(style)
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        button_layout = QHBoxLayout() #layout for buttons used to switch between tabs
        self.stacked_layout = QStackedLayout() #stackedlayout for "storing" the views
        main_layout.addLayout(button_layout)
        main_layout.addLayout(self.stacked_layout)
        # make stacked area expand to fill window
        main_layout.setStretch(0, 0)
        main_layout.setStretch(1, 1)
        self.setLayout(main_layout)

        # apply dark rounded stylesheet
        try:
            self.apply_stylesheet()
        except Exception:
            pass

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
        self.customers_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        customers_layout.addWidget(self.customers_table, 1)
        
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
        self.cars_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        cars_layout.addWidget(self.cars_table, 1)
        
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

        table_graph_layout = QHBoxLayout()
        lendings_layout.addLayout(table_graph_layout)
    
        self.lendings_table = QTableView()
        self.lendings_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.lendings_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        #give the graph more horizontal space (table:graph = 1:2)
        table_graph_layout.addWidget(self.lendings_table, 1)

        #graph area with embedded canvas
        self.graph_widget = QWidget()
        self.graph_layout = QVBoxLayout()
        self.graph_widget.setLayout(self.graph_layout)
        self.graph_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        table_graph_layout.addWidget(self.graph_widget, 1)
        
        #creating figure and canvas once, reusing for updates
        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvasQTAgg(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.canvas.setMinimumWidth(420)
        self.canvas.setMinimumHeight(320)
        self.ax = self.fig.add_subplot(111)
        self.graph_layout.addWidget(self.canvas)

        #combobox for selecting graph type
        self.graph_type_combo = QComboBox()
        self.graph_type_combo.addItems(["Bar Chart", "Pie Chart", "Line Graph"])
        self.graph_type_combo.currentTextChanged.connect(lambda: self.refresh_graph())

        #title customization input
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Custom Title (optional)")
        self.title_input.textChanged.connect(lambda: self.refresh_graph())

        #color selector
        self.color_combo = QComboBox()
        #include a set of named colors and hex values
        self.color_combo.addItems(["blue", "green", "orange", "red", "purple", "yellow"]) 
        self.color_combo.currentTextChanged.connect(lambda: self.refresh_graph())

        #button for showing the graph
        self.show_graph_button = QPushButton("Show Lending Graph")
        self.show_graph_button.clicked.connect(lambda: self.refresh_graph())
        buttons_layout = QHBoxLayout()

        #buttons
        add_button = QPushButton("Add Lending")
        edit_button = QPushButton("Edit Lending")
        delete_button = QPushButton("Delete Lending")

        buttons_layout.addWidget(add_button)
        buttons_layout.addWidget(edit_button)
        buttons_layout.addWidget(delete_button)
        buttons_layout.addWidget(self.show_graph_button)
        buttons_layout.addWidget(QLabel("Type:"))
        buttons_layout.addWidget(self.graph_type_combo)
        buttons_layout.addWidget(QLabel("Title:"))
        buttons_layout.addWidget(self.title_input)
        buttons_layout.addWidget(QLabel("Color:"))
        buttons_layout.addWidget(self.color_combo)

        lendings_layout.addLayout(buttons_layout)
        add_button.clicked.connect(self.add_lending_record)
        edit_button.clicked.connect(self.edit_lending_record)
        delete_button.clicked.connect(self.delete_lending_record)
        self.stacked_layout.addWidget(lendings_widget)
        
        self.load_record_data("lendings")
        
        #Start auto-refresh
        self.graph_timer.start()



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
            try:
                self.customers_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            except Exception:
                pass
        elif table == "cars":
            self.cars_table.setModel(model)
            try:
                self.cars_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            except Exception:
                pass
        elif table == "lendings":
            self.lendings_table.setModel(model)
            try:
                self.lendings_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            except Exception:
                pass

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

    #helper forfetching graph data
    def update_graph_data(self):
        query = QSqlQuery("SELECT lending_date, COUNT(*) as count FROM lendings GROUP BY lending_date")
        dates = []
        counts = []
        while query.next():
            dates.append(query.value(0))
            counts.append(query.value(1))
        return dates, counts

    #refreshing the graph display
    def refresh_graph(self):
        self.show_lending_graph(self.graph_type_combo.currentText())

    def _generate_color_tints(self, base_color, n):
        """Return n RGB tuples (0-1) as tints of base_color."""
        try:
            rgb = mcolors.to_rgb(base_color)
        except Exception:
            # fallback to a default blue
            rgb = (0.2, 0.4, 0.8)

        h, s, v = colorsys.rgb_to_hsv(*rgb)
        tints = []
        if n <= 1:
            return [rgb]
        for i in range(n):
            frac = i / (n - 1)
            # vary brightness from darker to lighter
            new_v = 0.4 + 0.6 * frac
            # slightly change saturation for contrast
            new_s = max(0.2, s * (0.6 + 0.4 * (1 - frac)))
            new_rgb = colorsys.hsv_to_rgb(h, new_s, new_v)
            tints.append(new_rgb)
        return tints

    #----------------------------------------------------------------------------------


    #method for showing lending graph
    def show_lending_graph(self, graph_type):
        #fetching data
        dates, counts = self.update_graph_data()

        #clearing axes and redraw
        self.ax.clear()

        #getting custom title or using default
        custom_title = self.title_input.text().strip() if hasattr(self, 'title_input') else ""

        if not dates or sum(counts) == 0:
            self.ax.text(0.5, 0.5, "No lending data available", ha='center', va='center')
            if custom_title:
                self.ax.set_title(custom_title)
            else:
                self.ax.set_title("Lendings")
        else:
            # determine selected color
            sel_color = None
            if hasattr(self, 'color_combo'):
                sel_color = self.color_combo.currentText()
            if not sel_color:
                sel_color = 'tab:blue'

            if graph_type == "Bar Chart":
                self.ax.bar(dates, counts, color=sel_color)
                title = custom_title if custom_title else "Lendings per Date - Bar Chart"
                self.ax.set_title(title)
                self.ax.set_xlabel("Date")
                self.ax.set_ylabel("Number of Lendings")
            elif graph_type == "Pie Chart":
                try:
                    colors = self._generate_color_tints(sel_color, len(counts))
                except Exception:
                    colors = [sel_color for _ in counts]
                self.ax.pie(counts, labels=dates, autopct='%1.1f%%', startangle=140, colors=colors)
                title = custom_title if custom_title else "Lendings Distribution - Pie Chart"
                self.ax.set_title(title)
            elif graph_type == "Line Graph":
                self.ax.plot(dates, counts, marker='o', linestyle='-', color=sel_color)
                title = custom_title if custom_title else "Lendings per Date - Line Graph"
                self.ax.set_title(title)
                self.ax.set_xlabel("Date")
                self.ax.set_ylabel("Number of Lendings")

        try:
            self.fig.tight_layout()
        except Exception:
            pass
        self.canvas.draw()     

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CarLendingApp()
    window.show()
    sys.exit(app.exec())