"""Ejemplos locales para el prototipo de recepción de encuestas."""


class SurveyController:
	"""Proporciona mensajes demostrativos, sin conectarse a canales reales."""

	@staticmethod
	def get_prototype_messages() -> list[dict[str, object]]:
		"""Retorna ejemplos ilustrativos de respuestas por distintos medios."""
		return [
			{
				"id": "whatsapp",
				"channel": "WhatsApp",
				"sender": "Laura Méndez",
				"address": "+1 (555) 014-2201",
				"received_at": "15 oct 2026 · 9:42 a. m.",
				"subject": "Respuesta a encuesta de compra",
				"message": (
					"Hola, ya recibí mi Honda Civic. La atención fue excelente. "
					"Califico el vehículo con 5, el concesionario con 4 y al "
					"vendedor con 5. ¡Gracias!"
				),
				"ratings": {
					"Vehículo": 5,
					"Concesionario": 4,
					"Vendedor": 5,
				},
				"reference": "Venta #1042 · Honda Civic",
			},
			{
				"id": "email",
				"channel": "Correo electrónico",
				"sender": "Carlos Ramírez",
				"address": "carlos.ramirez@example.com",
				"received_at": "14 oct 2026 · 4:18 p. m.",
				"subject": "Encuesta de satisfacción — compra #1038",
				"message": (
					"Gracias por contactarme. Mi experiencia con la compra fue "
					"buena. El vehículo está en excelentes condiciones; el "
					"proceso en el concesionario podría ser más rápido."
				),
				"ratings": {
					"Vehículo": 5,
					"Concesionario": 3,
					"Vendedor": 4,
				},
				"reference": "Venta #1038 · Toyota Corolla",
			},
			{
				"id": "sms",
				"channel": "Mensaje SMS",
				"sender": "María Torres",
				"address": "+1 (555) 014-7730",
				"received_at": "14 oct 2026 · 11:06 a. m.",
				"subject": "Respuesta por mensaje de texto",
				"message": (
					"Respuesta a la encuesta: Vehículo 4/5, concesionario 5/5, "
					"vendedor 5/5. Comentario: Muy amables, gracias."
				),
				"ratings": {
					"Vehículo": 4,
					"Concesionario": 5,
					"Vendedor": 5,
				},
				"reference": "Venta #1035 · Nissan Sentra",
			},
			{
				"id": "web",
				"channel": "Formulario web",
				"sender": "Jorge Castillo",
				"address": "Formulario enviado desde el enlace de encuesta",
				"received_at": "13 oct 2026 · 2:31 p. m.",
				"subject": "Encuesta completada en línea",
				"message": (
					"El cliente abrió el enlace enviado después de la entrega y "
					"completó las calificaciones del formulario."
				),
				"ratings": {
					"Vehículo": 5,
					"Concesionario": 5,
					"Vendedor": 5,
				},
				"reference": "Venta #1029 · Hyundai Tucson",
			},
		]
