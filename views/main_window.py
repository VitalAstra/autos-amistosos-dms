from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)
from PySide6.QtCore import Qt
from controllers.customer_controller import CustomerController
from controllers.employee_controller import EmployeeController
from controllers.sales_controller import SalesController
from controllers.vehicle_controller import VehicleController
from views.customer_view import CustomerView
from views.dashboard_view import DashboardView
from views.new_employee_view import NewEmployeeView
from views.new_vehicle_view import NewVehicleView
from views.sales_view import SalesView
from views.sales_history_view import SalesHistoryView
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
        self.btn_sales_history = QPushButton("Ventas registradas")
        self.btn_surveys = QPushButton("Encuestas")
        for button in (
            self.btn_dashboard,
            self.btn_customers,
            self.btn_vehicles,
            self.btn_sales,
            self.btn_sales_history,
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
        sidebar_layout.addWidget(self.btn_sales_history)
        sidebar_layout.addWidget(self.btn_surveys)

        # Contenedor de Vistas (QStackedWidget)
        self.view_stack = QStackedWidget()
        self.customer_controller = CustomerController()
        self.employee_controller = EmployeeController()
        self.sales_controller = SalesController()
        self.vehicle_controller = VehicleController()
        self._new_vehicle_window = None
        self._new_employee_window = None

        self.dashboard_view = DashboardView()
        self.customer_view = CustomerView()
        self.vehicle_view = VehicleView()
        self.sales_view = SalesView()
        self.sales_history_view = SalesHistoryView()
        self.add_view(self.dashboard_view)
        self.add_view(self.customer_view)
        self.add_view(self.vehicle_view)
        self.add_view(self.sales_view)
        self.add_view(self.sales_history_view)

        # Unir al layout principal
        main_layout.addWidget(sidebar, stretch=1)
        main_layout.addWidget(self.view_stack, stretch=5)

        # Conectar navegación y carga de datos
        self.btn_dashboard.clicked.connect(self._show_dashboard)
        self.btn_customers.clicked.connect(self._show_customers)
        self.btn_vehicles.clicked.connect(self._show_vehicles)
        self.btn_sales.clicked.connect(self._show_sales)
        self.btn_sales_history.clicked.connect(self._show_sales_history)
        self.dashboard_view.quick_action_requested.connect(
            self._handle_dashboard_action
        )
        self.customer_view.save_requested.connect(self._register_customer)
        self.customer_view.update_requested.connect(self._update_customer)
        self.customer_view.delete_requested.connect(self._delete_customer)
        self.customer_view.new_employee_requested.connect(
            self._open_new_employee
        )
        self.sales_view.sale_requested.connect(self._process_sale)
        self.vehicle_view.new_vehicle_requested.connect(
            self._open_new_vehicle
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

    def _register_customer(self, customer_data: dict):
        success, message = self.customer_controller.register_customer(
            customer_data
        )
        self.customer_view.show_save_result(success, message)
        if success:
            self.customer_view.load_data(
                self.customer_controller.list_customers()
            )

    def _update_customer(self, payload: dict):
        customer_id = payload.get("id")
        if customer_id is None:
            self.customer_view.show_save_result(False, "No hay cliente seleccionado.")
            return
        # Excluir id antes de pasar los campos al controlador
        data = {k: v for k, v in payload.items() if k != "id"}
        success, message = self.customer_controller.update_customer(customer_id, data)
        self.customer_view.show_save_result(success, message)
        if success:
            self.customer_view.load_data(self.customer_controller.list_customers())

    def _delete_customer(self, customer_id: int):
        reply = QMessageBox.question(
            self,
            "Confirmar eliminación",
            "¿Estás seguro de eliminar este cliente? Esta acción no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        success, message = self.customer_controller.delete_customer(customer_id)
        self.customer_view.show_save_result(success, message)
        if success:
            self.customer_view.load_data(self.customer_controller.list_customers())

    def _show_vehicles(self):
        self.view_stack.setCurrentWidget(self.vehicle_view)
        self._set_active_navigation(self.btn_vehicles)
        vehicles = self.vehicle_controller.get_inventory(available_only=False)
        self.vehicle_view.load_data(vehicles)

    def _open_new_vehicle(self):
        if self._new_vehicle_window is None:
            self._new_vehicle_window = NewVehicleView(self)
            self._new_vehicle_window.save_requested.connect(
                self._register_vehicle
            )
        self._new_vehicle_window.show()
        self._new_vehicle_window.raise_()
        self._new_vehicle_window.activateWindow()

    def _register_vehicle(self, vehicle_data: dict):
        success, message = self.vehicle_controller.add_vehicle(vehicle_data)
        self._new_vehicle_window.show_save_result(success, message)
        if success:
            self.vehicle_view.load_data(
                self.vehicle_controller.get_inventory(available_only=False)
            )
            self.sales_view.load_selection_data(
                self.customer_controller.list_customers(),
                self.vehicle_controller.get_inventory(available_only=True),
                self.employee_controller.list_employees(),
            )

    def _open_new_employee(self):
        if self._new_employee_window is None:
            self._new_employee_window = NewEmployeeView(self)
            self._new_employee_window.save_requested.connect(
                self._register_employee
            )
        self._new_employee_window.show()
        self._new_employee_window.raise_()
        self._new_employee_window.activateWindow()

    def _register_employee(self, employee_data: dict):
        success, message = self.employee_controller.add_employee(
            employee_data
        )
        self._new_employee_window.show_save_result(success, message)
        if success:
            self.sales_view.load_selection_data(
                self.customer_controller.list_customers(),
                self.vehicle_controller.get_inventory(available_only=True),
                self.employee_controller.list_employees(),
            )

    def _show_sales(self):
        self.view_stack.setCurrentWidget(self.sales_view)
        self._set_active_navigation(self.btn_sales)
        self.sales_view.load_selection_data(
            self.customer_controller.list_customers(),
            self.vehicle_controller.get_inventory(available_only=True),
            self.employee_controller.list_employees(),
        )

    def _show_sales_history(self):
        self.view_stack.setCurrentWidget(self.sales_history_view)
        self._set_active_navigation(self.btn_sales_history)
        self.sales_history_view.load_sales(
            self.sales_controller.get_sales_history()
        )

    def _show_dashboard(self):
        self.view_stack.setCurrentWidget(self.dashboard_view)
        self._set_active_navigation(self.btn_dashboard)
        self.dashboard_view.update_metrics(
            self.sales_controller.get_dashboard_data()
        )
        self.dashboard_view.load_recent_sales(
            self.sales_controller.get_recent_sales()
        )
        self.sales_history_view.load_sales(
            self.sales_controller.get_sales_history()
        )

    def _process_sale(self, payload: dict):
        success, message = self.sales_controller.process_sale(
            customer_id=payload["customer_id"],
            vehicle_id=payload["vehicle_id"],
            negotiated_price=payload["negotiated_price"],
            tax_rate=payload["tax_rate"],
            employee_id=payload["employee_id"],
            current_mileage=payload["current_mileage"],
            license_fee=payload["license_fee"],
            addons=payload["addons"],
            manager_approval=payload["manager_approval"],
        )
        self.sales_view.show_sale_result(success, message)
        if success:
            self.sales_view.load_selection_data(
                self.customer_controller.list_customers(),
                self.vehicle_controller.get_inventory(available_only=True),
                self.employee_controller.list_employees(),
            )
            self.dashboard_view.update_metrics(
                self.sales_controller.get_dashboard_data()
            )
            self.dashboard_view.load_recent_sales(
                self.sales_controller.get_recent_sales()
            )

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
            self.btn_sales_history,
            self.btn_surveys,
        ):
            button.setProperty("active", button is active_button)
            button.style().unpolish(button)
            button.style().polish(button)
