from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QInputDialog,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from controllers.customer_controller import CustomerController
from controllers.dashboard_controller import DashboardController
from controllers.employee_controller import EmployeeController
from controllers.sales_controller import SalesController
from controllers.vehicle_controller import VehicleController
from views.customer_view import CustomerView
from views.dashboard_view import DashboardView
from views.new_employee_view import NewEmployeeView
from views.sales_history_view import SalesHistoryView
from views.sales_review_view import SalesReviewView
from views.sales_view import SalesView
from views.vehicle_view import VehicleView


class MainWindow(QMainWindow):
    """Ventana principal del DMS con menú lateral y contenedor de vistas."""

    def __init__(self, current_employee):
        super().__init__()
        self.current_employee = current_employee
        self.setWindowTitle("Autos Amistosos")
        self.resize(1280, 720)

        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

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
        self.btn_sales_history = QPushButton("Historial de ventas")
        self.btn_sales_review = QPushButton("Aprobaciones")
        self.nav_buttons = (
            self.btn_dashboard,
            self.btn_customers,
            self.btn_vehicles,
            self.btn_sales,
            self.btn_sales_history,
            self.btn_sales_review,
        )
        for button in self.nav_buttons:
            button.setObjectName("navButton")

        sidebar_title = QLabel("Autos Amistosos")
        sidebar_title.setObjectName("sidebarTitle")
        sidebar_layout.addWidget(sidebar_title)
        for button in self.nav_buttons:
            sidebar_layout.addWidget(button)

        self.view_stack = QStackedWidget()
        self.dashboard_controller = DashboardController()
        self.customer_controller = CustomerController()
        self.employee_controller = EmployeeController()
        self.sales_controller = SalesController()
        self.vehicle_controller = VehicleController()
        self._new_employee_window = None

        self.dashboard_view = DashboardView()
        self.customer_view = CustomerView()
        self.vehicle_view = VehicleView()
        self.sales_view = SalesView()
        self.sales_history_view = SalesHistoryView()
        self.sales_review_view = SalesReviewView()
        for view in (
            self.dashboard_view,
            self.customer_view,
            self.vehicle_view,
            self.sales_view,
            self.sales_history_view,
            self.sales_review_view,
        ):
            self.view_stack.addWidget(view)

        main_layout.addWidget(sidebar, stretch=1)
        main_layout.addWidget(self.view_stack, stretch=5)

        self.btn_dashboard.clicked.connect(self._show_dashboard)
        self.btn_customers.clicked.connect(self._show_customers)
        self.btn_vehicles.clicked.connect(self._show_vehicles)
        self.btn_sales.clicked.connect(self._show_sales)
        self.btn_sales_history.clicked.connect(self._show_sales_history)
        self.btn_sales_review.clicked.connect(self._show_sales_review)
        self.dashboard_view.quick_action_requested.connect(
            self._handle_dashboard_action
        )
        self.customer_view.save_requested.connect(self._register_customer)
        self.customer_view.update_requested.connect(self._update_customer)
        self.customer_view.delete_requested.connect(self._delete_customer)
        self.customer_view.new_employee_requested.connect(
            self._open_new_employee
        )
        self.vehicle_view.vehicle_save_requested.connect(self._register_vehicle)
        self.sales_view.sale_requested.connect(self._process_sale)
        self.sales_review_view.approve_requested.connect(self._approve_sale)
        self.sales_review_view.reject_requested.connect(self._reject_sale)
        self.sales_review_view.cancel_requested.connect(self._cancel_sale)

        self._show_dashboard()

    def _show_customers(self):
        self.view_stack.setCurrentWidget(self.customer_view)
        self._set_active_navigation(self.btn_customers)
        self.customer_view.load_data(self.customer_controller.list_customers())
        self.customer_view.load_lead_sources(
            self.customer_controller.list_lead_sources()
        )

    def _register_customer(self, customer_data: dict):
        success, message = self.customer_controller.register_customer(customer_data)
        self.customer_view.show_save_result(success, message)
        if success:
            self.customer_view.clear_form()
            self.customer_view.load_data(self.customer_controller.list_customers())

    def _update_customer(self, payload: dict):
        customer_id = payload.get("id")
        if customer_id is None:
            self.customer_view.show_save_result(
                False, "No hay cliente seleccionado."
            )
            return
        data = {key: value for key, value in payload.items() if key != "id"}
        success, message = self.customer_controller.update_customer(
            customer_id, data
        )
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
        self.vehicle_view.load_data(
            self.vehicle_controller.get_inventory(available_only=False)
        )

    def _register_vehicle(self, vehicle_data: dict):
        success, message = self.vehicle_controller.add_vehicle(vehicle_data)
        if success:
            self.vehicle_view.clear_form()
            self._show_vehicles()
            QMessageBox.information(self, "Vehículo", message)
            self._refresh_sales_selection()
        else:
            QMessageBox.warning(self, "No se guardó el vehículo", message)

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
        success, message = self.employee_controller.add_employee(employee_data)
        self._new_employee_window.show_save_result(success, message)
        if success:
            self._refresh_sales_selection()

    def _show_sales(self):
        if (
            self.current_employee is not None
            and self.current_employee.role.casefold() != "salesperson"
        ):
            return
        self.view_stack.setCurrentWidget(self.sales_view)
        self._set_active_navigation(self.btn_sales)
        self._refresh_sales_selection()

    def _refresh_sales_selection(self):
        employees = (
            [self.current_employee]
            if self.current_employee is not None
            and self.current_employee.role.casefold() == "salesperson"
            else self.employee_controller.list_active_salespeople()
        )
        self.sales_view.load_selection_data(
            self.customer_controller.list_customers(),
            self.vehicle_controller.get_inventory(available_only=True),
            employees,
        )

    def _show_sales_history(self):
        self.view_stack.setCurrentWidget(self.sales_history_view)
        self._set_active_navigation(self.btn_sales_history)
        self.sales_history_view.load_sales(
            self.sales_controller.get_sales_history()
        )

    def _process_sale(self, sale_data: dict):
        payload = dict(sale_data)
        if self.current_employee is not None:
            payload["employee_id"] = self.current_employee.employee_id
        success, message = self.sales_controller.process_sale(payload)
        self.sales_view.show_sale_result(success, message)
        if success:
            self._refresh_sales_selection()
            self._refresh_dashboard()

    def _show_sales_review(self):
        if (
            self.current_employee is not None
            and self.current_employee.role.casefold()
            not in {"manager", "administrator"}
        ):
            return
        self.view_stack.setCurrentWidget(self.sales_review_view)
        self._set_active_navigation(self.btn_sales_review)
        self.sales_review_view.load_data(
            self.sales_controller.list_reviewable_sales()
        )

    def _approve_sale(self, invoice_id: int):
        self._review_sale(self.sales_controller.approve_sale, invoice_id)

    def _reject_sale(self, invoice_id: int, reason: str):
        self._review_sale(self.sales_controller.reject_sale, invoice_id, reason)

    def _cancel_sale(self, invoice_id: int, reason: str):
        self._review_sale(self.sales_controller.cancel_sale, invoice_id, reason)

    def _review_sale(self, action, invoice_id: int, reason=None):
        supervisor_id = (
            self.current_employee.employee_id
            if self.current_employee is not None
            else self._select_supervisor_id()
        )
        if supervisor_id is None:
            return
        arguments = [invoice_id, supervisor_id]
        if reason is not None:
            arguments.append(reason)
        success, message = action(*arguments)
        if success:
            self._show_sales_review()
            self._refresh_dashboard()
            QMessageBox.information(self, "Revisión de venta", message)
        else:
            QMessageBox.warning(self, "No se pudo revisar", message)

    def _select_supervisor_id(self) -> int | None:
        supervisors = self.employee_controller.list_active_supervisors()
        if not supervisors:
            QMessageBox.warning(
                self,
                "Supervisor requerido",
                "Registra un empleado con rol Gerente o Administración "
                "antes de aprobar, rechazar o cancelar ventas.",
            )
            return None

        labels = [
            f"{employee.first_name} {employee.last_name} — {employee.role}"
            for employee in supervisors
        ]
        label, accepted = QInputDialog.getItem(
            self,
            "Supervisor responsable",
            "Selecciona el supervisor que realizará esta acción:",
            labels,
            0,
            False,
        )
        if not accepted:
            return None
        selected_index = labels.index(label)
        return supervisors[selected_index].employee_id

    def _show_dashboard(self):
        self.view_stack.setCurrentWidget(self.dashboard_view)
        self._set_active_navigation(self.btn_dashboard)
        self._refresh_dashboard()
        self.sales_history_view.load_sales(
            self.sales_controller.get_sales_history()
        )

    def _refresh_dashboard(self):
        data = self.dashboard_controller.get_dashboard_data()
        self.dashboard_view.update_metrics(data)
        self.dashboard_view.load_recent_sales(data["recent_sales"])

    def _handle_dashboard_action(self, action: str):
        actions = {
            "Registrar cliente": self._show_customers,
            "Alta de vehículo": self._show_vehicles,
            "Nueva venta": self._show_sales,
        }
        handler = actions.get(action)
        if handler is not None:
            handler()

    def _set_active_navigation(self, active_button: QPushButton):
        for button in self.nav_buttons:
            button.setProperty("active", button is active_button)
            button.style().unpolish(button)
            button.style().polish(button)
