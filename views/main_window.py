from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt
from controllers.customer_controller import CustomerController
from controllers.vehicle_controller import VehicleController
from views.customer_view import CustomerView
from views.dashboard_view import DashboardView
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
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # Menú Lateral (Sidebar)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 12, 12, 12)
        sidebar_layout.setSpacing(8)
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.btn_dashboard = QPushButton("Inicio")
        self.btn_customers = QPushButton("Clientes")
        self.btn_vehicles = QPushButton("Vehículos")
        self.btn_sales = QPushButton("Nueva Venta")
        self.btn_surveys = QPushButton("Encuestas")
        for button in (
            self.btn_dashboard,
            self.btn_customers,
            self.btn_vehicles,
            self.btn_sales,
            self.btn_surveys,
        ):
            button.setObjectName("navButton")

        sidebar_title = QLabel("DMS MENÚ")
        sidebar_title.setObjectName("sidebarTitle")
        sidebar_layout.addWidget(sidebar_title)
        sidebar_layout.addWidget(self.btn_dashboard)
        sidebar_layout.addWidget(self.btn_customers)
        sidebar_layout.addWidget(self.btn_vehicles)
        sidebar_layout.addWidget(self.btn_sales)
        sidebar_layout.addWidget(self.btn_surveys)

        # Contenedor de Vistas (QStackedWidget)
        self.view_stack = QStackedWidget()
        self.customer_controller = CustomerController()
        self.vehicle_controller = VehicleController()

        self.dashboard_view = DashboardView()
        self.customer_view = CustomerView()
        self.vehicle_view = VehicleView()
        self.sales_view = SalesView()
        self.add_view(self.dashboard_view)
        self.add_view(self.customer_view)
        self.add_view(self.vehicle_view)
        self.add_view(self.sales_view)

        # Unir al layout principal
        main_layout.addWidget(sidebar, stretch=1)
        main_layout.addWidget(self.view_stack, stretch=5)

        # Conectar navegación y carga de datos
        self.btn_dashboard.clicked.connect(self._show_dashboard)
        self.btn_customers.clicked.connect(self._show_customers)
        self.btn_vehicles.clicked.connect(self._show_vehicles)
        self.btn_sales.clicked.connect(self._show_sales)
        self.dashboard_view.quick_action_requested.connect(
            self._handle_dashboard_action
        )

        self._show_dashboard()

    def add_view(self, view_widget: QWidget):
        """Agrega una nueva vista al contenedor acumulativo."""
        self.view_stack.addWidget(view_widget)

    def _show_customers(self):
        self.view_stack.setCurrentWidget(self.customer_view)
        self._set_active_navigation(self.btn_customers)
        customers = self.customer_controller.list_customers()
        self.customer_view.load_data(customers)

    def _show_vehicles(self):
        self.view_stack.setCurrentWidget(self.vehicle_view)
        self._set_active_navigation(self.btn_vehicles)
        vehicles = self.vehicle_controller.get_inventory(available_only=False)
        self.vehicle_view.load_data(vehicles)

    def _show_sales(self):
        self.view_stack.setCurrentWidget(self.sales_view)
        self._set_active_navigation(self.btn_sales)
        self.sales_view.load_selection_data(
            self.customer_controller.list_customers(),
            self.vehicle_controller.get_inventory(available_only=True),
        )

    def _show_dashboard(self):
        self.view_stack.setCurrentWidget(self.dashboard_view)
        self._set_active_navigation(self.btn_dashboard)

    def _handle_dashboard_action(self, action: str):
        actions = {
            "Registrar Cliente": self._show_customers,
            "Alta de Vehículo": self._show_vehicles,
            "Nueva Venta": self._show_sales,
        }
        handler = actions.get(action)
        if handler is not None:
            handler()

    def _set_active_navigation(self, active_button: QPushButton):
        for button in (
            self.btn_dashboard,
            self.btn_customers,
            self.btn_vehicles,
            self.btn_sales,
            self.btn_surveys,
        ):
            button.setProperty("active", button is active_button)
            button.style().unpolish(button)
            button.style().polish(button)
