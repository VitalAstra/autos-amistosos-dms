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
from controllers.dashboard_controller import DashboardController
from controllers.customer_controller import CustomerController
from controllers.employee_controller import EmployeeController
from controllers.sales_controller import SalesController
from controllers.vehicle_controller import VehicleController
from views.customer_view import CustomerView
from views.dashboard_view import DashboardView
from views.sales_view import SalesView
from views.sales_review_view import SalesReviewView
from views.vehicle_view import VehicleView

class MainWindow(QMainWindow):
    """Ventana principal del DMS con menú lateral y contenedor de vistas."""

    def __init__(self, current_employee):
        super().__init__()
        self.current_employee = current_employee
        self.setWindowTitle("Autos Amistosos")
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

        sidebar_title = QLabel("Autos Amistosos")
        sidebar_title.setObjectName("sidebarTitle")
        sidebar_layout.addWidget(sidebar_title)
        sidebar_layout.addWidget(self.btn_dashboard)
        sidebar_layout.addWidget(self.btn_customers)
        sidebar_layout.addWidget(self.btn_vehicles)
        sidebar_layout.addWidget(self.btn_sales)
        sidebar_layout.addWidget(self.btn_surveys)

        # Contenedor de Vistas (QStackedWidget)
        self.view_stack = QStackedWidget()
        self.dashboard_controller = DashboardController()
        self.customer_controller = CustomerController()
        self.employee_controller = EmployeeController()
        self.sales_controller = SalesController()
        self.vehicle_controller = VehicleController()

        self.dashboard_view = DashboardView()
        self.customer_view = CustomerView()
        self.sales_review_view = SalesReviewView()
        self.vehicle_view = VehicleView()
        self.sales_view = SalesView()
        self.add_view(self.dashboard_view)
        self.add_view(self.customer_view)
        self.add_view(self.vehicle_view)
        self.add_view(self.sales_view)
        self.add_view(self.sales_review_view)

        # Unir al layout principal
        main_layout.addWidget(sidebar, stretch=1)
        main_layout.addWidget(self.view_stack, stretch=5)

        # Conectar navegación y carga de datos
        self.btn_dashboard.clicked.connect(self._show_dashboard)
        self.btn_customers.clicked.connect(self._show_customers)
        self.btn_vehicles.clicked.connect(self._show_vehicles)
        self.btn_sales.clicked.connect(self._show_sales)
        self.btn_surveys.setText("Aprobaciones")
        self.btn_surveys.clicked.connect(self._show_sales_review)
        employee_role = (
            self.current_employee.role.casefold()
            if self.current_employee is not None
            else ""
        )
        is_salesperson = employee_role == "salesperson"
        is_supervisor = employee_role in {
            "manager",
            "administrator",
        }
        self.btn_sales.setVisible(is_salesperson)
        self.btn_sales.setEnabled(is_salesperson)
        self.btn_surveys.setVisible(is_supervisor)
        self.btn_surveys.setEnabled(is_supervisor)
        self.customer_view.save_requested.connect(self._register_customer)
        self.vehicle_view.vehicle_save_requested.connect(self._register_vehicle)
        self.sales_view.sale_requested.connect(self._process_sale)
        self.sales_review_view.approve_requested.connect(self._approve_sale)
        self.sales_review_view.reject_requested.connect(self._reject_sale)
        self.sales_review_view.cancel_requested.connect(self._cancel_sale)
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
        self.customer_view.load_lead_sources(
            self.customer_controller.list_lead_sources()
        )

    def _show_vehicles(self):
        self.view_stack.setCurrentWidget(self.vehicle_view)
        self._set_active_navigation(self.btn_vehicles)
        vehicles = self.vehicle_controller.get_inventory(available_only=False)
        self.vehicle_view.load_data(vehicles)

    def _show_sales(self):
        if (
            self.current_employee is None
            or self.current_employee.role.casefold() != "salesperson"
        ):
            return
        self.view_stack.setCurrentWidget(self.sales_view)
        self._set_active_navigation(self.btn_sales)
        self.sales_view.load_selection_data(
            self.customer_controller.list_customers(),
            self.vehicle_controller.get_inventory(available_only=True),
            [self.current_employee],
        )

    def _register_customer(self, customer_data: dict):
        success, message = self.customer_controller.register_customer(customer_data)
        if success:
            self.customer_view.clear_form()
            self._show_customers()
            QMessageBox.information(self, "Cliente", message)
        else:
            QMessageBox.warning(self, "No se guardó el cliente", message)

    def _register_vehicle(self, vehicle_data: dict):
        success, message = self.vehicle_controller.add_vehicle(vehicle_data)
        if success:
            self.vehicle_view.clear_form()
            self._show_vehicles()
            QMessageBox.information(self, "Vehículo", message)
        else:
            QMessageBox.warning(self, "No se guardó el vehículo", message)

    def _process_sale(self, sale_data: dict):
        if self.current_employee is None:
            QMessageBox.warning(
                self,
                "Empleado requerido",
                "Registra una sesión de empleado para crear una venta.",
            )
            return
        payload = dict(sale_data)
        payload["employee_id"] = self.current_employee.employee_id
        success, message = self.sales_controller.process_sale(payload)
        if success:
            self._show_sales()
            QMessageBox.information(self, "Venta pendiente", message)
        else:
            QMessageBox.warning(self, "No se procesó la venta", message)

    def _show_sales_review(self):
        if self.current_employee is None or self.current_employee.role.casefold() not in {
            "manager",
            "administrator",
        }:
            return
        self.view_stack.setCurrentWidget(self.sales_review_view)
        self._set_active_navigation(self.btn_surveys)
        self.sales_review_view.load_data(self.sales_controller.list_reviewable_sales())

    def _approve_sale(self, invoice_id: int):
        self._review_sale(self.sales_controller.approve_sale, invoice_id)

    def _reject_sale(self, invoice_id: int, reason: str):
        self._review_sale(self.sales_controller.reject_sale, invoice_id, reason)

    def _cancel_sale(self, invoice_id: int, reason: str):
        self._review_sale(self.sales_controller.cancel_sale, invoice_id, reason)

    def _review_sale(self, action, invoice_id: int, reason=None):
        if self.current_employee is None:
            return
        if reason is None:
            success, message = action(invoice_id, self.current_employee.employee_id)
        else:
            success, message = action(
                invoice_id, self.current_employee.employee_id, reason
            )
        if success:
            self._show_sales_review()
            self._show_dashboard()
            QMessageBox.information(self, "Revisión de venta", message)
        else:
            QMessageBox.warning(self, "No se pudo revisar", message)

    def _show_dashboard(self):
        self.view_stack.setCurrentWidget(self.dashboard_view)
        self._set_active_navigation(self.btn_dashboard)
        data = self.dashboard_controller.get_dashboard_data()
        self.dashboard_view.update_metrics(data)
        self.dashboard_view.load_recent_sales(data["recent_sales"])

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
