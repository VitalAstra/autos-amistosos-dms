from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QStackedWidget, QLabel
from PySide6.QtCore import Qt
from controllers.customer_controller import CustomerController
from controllers.vehicle_controller import VehicleController
from models.sales_invoice import SalesInvoice
from views.customer_view import CustomerView
from views.sales_view import SalesView
from views.vehicle_view import VehicleView

class MainWindow(QMainWindow):
    """Ventana principal del DMS con menú lateral y contenedor de vistas."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Autos Amistosos - Dealership Management System")
        self.resize(1280, 720)

        # Widget central y layout principal
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Menú Lateral (Sidebar)
        sidebar = QWidget()
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.btn_customers = QPushButton("Clientes")
        self.btn_vehicles = QPushButton("Vehículos")
        self.btn_sales = QPushButton("Nueva Venta")
        self.btn_surveys = QPushButton("Encuestas")

        sidebar_layout.addWidget(QLabel("<b>DMS MENÚ</b>"))
        sidebar_layout.addWidget(self.btn_customers)
        sidebar_layout.addWidget(self.btn_vehicles)
        sidebar_layout.addWidget(self.btn_sales)
        sidebar_layout.addWidget(self.btn_surveys)

        # Contenedor de Vistas (QStackedWidget)
        self.view_stack = QStackedWidget()
        self.customer_controller = CustomerController()
        self.vehicle_controller = VehicleController()

        self.customer_view = CustomerView()
        self.vehicle_view = VehicleView()
        self.sales_view = SalesView()
        self.add_view(self.customer_view)
        self.add_view(self.vehicle_view)
        self.add_view(self.sales_view)

        # Unir al layout principal
        main_layout.addWidget(sidebar, stretch=1)
        main_layout.addWidget(self.view_stack, stretch=5)

        # Conectar navegación y carga de datos
        self.btn_customers.clicked.connect(self._show_customers)
        self.btn_vehicles.clicked.connect(self._show_vehicles)
        self.btn_sales.clicked.connect(self._show_sales)

        self._show_customers()

    def add_view(self, view_widget: QWidget):
        """Agrega una nueva vista al contenedor acumulativo."""
        self.view_stack.addWidget(view_widget)

    def _show_customers(self):
        self.view_stack.setCurrentWidget(self.customer_view)
        self.customer_view.load_data(self.customer_controller.list_customers())

    def _show_vehicles(self):
        self.view_stack.setCurrentWidget(self.vehicle_view)
        self.vehicle_view.load_data(self.vehicle_controller.get_inventory())

    def _show_sales(self):
        self.view_stack.setCurrentWidget(self.sales_view)
        self.sales_view.load_data(SalesInvoice.get_sales_summary())