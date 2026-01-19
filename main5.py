import flet as ft
import threading
import time
import datetime
import json
import os
import random
from cajaAzul import BlueBox
from configuracion import ConfiguracionContainer
from excel5 import ExcelUnicoArchivo
from alertas import SistemaAlertas, AlertasView
from paguina1 import UMA


class RelojGlobal:
    def __init__(self):
        self.horas_registradas = []
        self.archivo_horas = "horas.json"
        self.historial_registros = []
        self.archivo_historial = "historial_registros.json"
        self.reloj_activo = True
        self.ultima_ejecucion = {}
        self.callbacks = []
        self.historial_callbacks = []
        
        # Cargar horas guardadas
        self.cargar_horas()
        self.cargar_historial()
        self.iniciar()

    def agregar_callback(self, callback):
        """Agrega una función que se ejecutará cuando suene una alarma"""
        self.callbacks.append(callback)
    
    def agregar_callback_historial(self, callback):
        """Agrega una función que se ejecutará cuando se agregue un nuevo registro al historial"""
        self.historial_callbacks.append(callback)

    def cargar_horas(self):
        """Carga las horas desde archivo JSON"""
        if os.path.exists(self.archivo_horas):
            try:
                with open(self.archivo_horas, "r") as file:
                    datos = json.load(file)
                    self.horas_registradas = [
                        datetime.datetime.strptime(h, "%H:%M").time()
                        for h in datos
                    ]
                print(f"RelojGlobal: Horas cargadas: {[h.strftime('%I:%M %p') for h in self.horas_registradas]}")
            except Exception as e:
                print(f"RelojGlobal: Error cargando horas: {e}")
                self.horas_registradas = []
    
    def cargar_historial(self):
        """Carga el historial desde archivo JSON"""
        if os.path.exists(self.archivo_historial):
            try:
                with open(self.archivo_historial, "r") as file:
                    self.historial_registros = json.load(file)
                print(f"RelojGlobal: Historial cargado ({len(self.historial_registros)} registros)")
            except Exception as e:
                print(f"RelojGlobal: Error cargando historial: {e}")
                self.historial_registros = []
        else:
            self.guardar_historial()

    def guardar_horas(self):
        """Guarda las horas en archivo JSON"""
        try:
            datos = [h.strftime("%H:%M") for h in self.horas_registradas]
            with open(self.archivo_horas, "w") as file:
                json.dump(datos, file)
        except Exception as e:
            print(f"RelojGlobal: Error guardando horas: {e}")
    
    def guardar_historial(self):
        """Guarda el historial en archivo JSON"""
        try:
            if len(self.historial_registros) > 100:  # Aumentado a 100 registros
                self.historial_registros = self.historial_registros[-100:]
            
            with open(self.archivo_historial, "w") as file:
                json.dump(self.historial_registros, file, indent=2)
        except Exception as e:
            print(f"RelojGlobal: Error guardando historial: {e}")

    def agregar_hora(self, hora_time):
        """Agrega una hora a la lista global"""
        if hora_time not in self.horas_registradas:
            self.horas_registradas.append(hora_time)
            self.guardar_horas()
            print(f"RelojGlobal: Hora agregada: {hora_time.strftime('%I:%M %p')}")
            return True
        return False

    def eliminar_hora(self, hora_time):
        """Elimina una hora de la lista global"""
        if hora_time in self.horas_registradas:
            self.horas_registradas.remove(hora_time)
            self.guardar_horas()
            print(f"RelojGlobal: Hora eliminada: {hora_time.strftime('%I:%M %p')}")
            return True
        return False
    
    def agregar_al_historial(self, datos, tipo="registro_automatico", fuente="Reloj Global"):
        """Agrega un registro al historial"""
        registro = {
            "fecha": datetime.datetime.now().strftime("%d/%m/%y"),
            "hora": datetime.datetime.now().strftime("%H:%M"),
            "datos": datos,
            "tipo": tipo,
            "fuente": fuente
        }
        self.historial_registros.append(registro)
        self.guardar_historial()
        
        # Notificar a todos los callbacks
        for callback in self.historial_callbacks:
            try:
                callback(registro)  # Ahora pasamos el registro como parámetro
            except Exception as e:
                print(f"RelojGlobal: Error en callback de historial: {e}")
        
        return registro
    
    def limpiar_historial(self):
        """Limpia todo el historial"""
        self.historial_registros = []
        self.guardar_historial()
        print("RelojGlobal: Historial limpiado")
        
        # Notificar a los callbacks
        for callback in self.historial_callbacks:
            try:
                callback(None)  # Pasamos None para indicar limpieza
            except Exception as e:
                print(f"RelojGlobal: Error en callback de limpieza: {e}")

    def iniciar(self):
        """Inicia el reloj global en un hilo separado"""
        if not hasattr(self, 'thread') or not self.thread.is_alive():
            self.thread = threading.Thread(target=self._loop, daemon=True)
            self.thread.start()
            print("RelojGlobal: Iniciado")

    def _loop(self):
        """Loop principal del reloj"""
        while self.reloj_activo:
            try:
                ahora = datetime.datetime.now()
                
                for hora_obj in self.horas_registradas:
                    hora_actual_minuto = ahora.strftime("%I:%M %p")
                    segundos = ahora.strftime("%S")
                    hora_objetivo_str = hora_obj.strftime("%I:%M %p")

                    if hora_actual_minuto == hora_objetivo_str and segundos == "00":
                        h_obj = datetime.datetime.combine(ahora.date(), hora_obj)
                        clave = h_obj.strftime("%Y-%m-%d %H:%M")

                        if clave not in self.ultima_ejecucion:
                            self.ultima_ejecucion[clave] = True
                            self._ejecutar_alarma(hora_objetivo_str)
                            print(f"RelojGlobal: ✓ Alarma: {hora_objetivo_str}")
                
                hoy = datetime.datetime.now().date()
                claves_a_eliminar = [k for k in self.ultima_ejecucion 
                                    if datetime.datetime.strptime(k.split(" ")[0], "%Y-%m-%d").date() < hoy]
                for k in claves_a_eliminar:
                    del self.ultima_ejecucion[k]

                time.sleep(1)
                
            except Exception as e:
                print(f"RelojGlobal: Error en loop: {e}")
                time.sleep(1)

    def _ejecutar_alarma(self, hora):
        """Ejecuta todos los callbacks registrados"""
        for callback in self.callbacks:
            try:
                callback(hora)
            except Exception as e:
                print(f"RelojGlobal: Error en callback: {e}")

    def detener(self):
        """Detiene el reloj global"""
        self.reloj_activo = False


class LoginScreen:
    def __init__(self, page, on_login_success):
        self.page = page
        self.on_login_success = on_login_success
        self.usuarios_file = "usuarios.json"
        
        # Cargar usuarios existentes
        self.cargar_usuarios()
        
        # Crear controles
        self.username_field = ft.TextField(
            label="Usuario",
            prefix_icon=ft.Icons.PERSON,
            width=300,
            text_size=16,
            border_color=ft.Colors.BLUE_700,
            focused_border_color=ft.Colors.BLUE_900,
        )
        
        self.password_field = ft.TextField(
            label="Contraseña",
            prefix_icon=ft.Icons.LOCK,
            width=300,
            password=True,
            can_reveal_password=True,
            text_size=16,
            border_color=ft.Colors.BLUE_700,
            focused_border_color=ft.Colors.BLUE_900,
        )
        
        self.login_button = ft.ElevatedButton(
            text="Iniciar Sesión",
            icon=ft.Icons.LOGIN,
            on_click=self.verificar_login,
            width=300,
            height=45,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE_700,
                color=ft.Colors.WHITE,
            )
        )
        
        self.register_button = ft.TextButton(
            text="¿No tienes cuenta? Regístrate",
            on_click=self.mostrar_registro,
            width=300,
        )
        
        self.error_text = ft.Text(
            color=ft.Colors.RED,
            size=14,
            text_align=ft.TextAlign.CENTER,
        )
        
        # Contenedor principal
        self.content = ft.Container(
            width=400,
            height=500,
            bgcolor=ft.Colors.WHITE,
            border_radius=20,
            padding=30,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color=ft.Colors.GREY_400,
            ),
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=25,
                controls=[
                    ft.Icon(ft.Icons.SECURITY, size=80, color=ft.Colors.BLUE_700),
                    ft.Text(
                        "Sistema de Monitoreo",
                        size=28,
                        weight=ft.FontWeight.BOLD,
                        color=ft.Colors.BLUE_900,
                    ),
                    ft.Text(
                        "Inicia sesión para continuar",
                        size=16,
                        color=ft.Colors.GREY_600,
                    ),
                    self.username_field,
                    self.password_field,
                    self.error_text,
                    self.login_button,
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                    self.register_button,
                ]
            )
        )
        
        # Variables para registro
        self.registro_username = None
        self.registro_password = None
        self.registro_confirm_password = None
        
    def cargar_usuarios(self):
        """Carga los usuarios desde el archivo JSON"""
        if os.path.exists(self.usuarios_file):
            try:
                with open(self.usuarios_file, "r") as f:
                    datos = json.load(f)
                    # Verificar si es el formato antiguo (solo contraseñas)
                    if isinstance(datos, dict) and all(isinstance(v, str) for v in datos.values()):
                        # Convertir formato antiguo a nuevo (con roles)
                        nuevos_datos = {}
                        for usuario, password in datos.items():
                            if usuario == "admin":
                                nuevos_datos[usuario] = {"password": password, "rol": "admin"}
                            else:
                                nuevos_datos[usuario] = {"password": password, "rol": "usuario"}
                        self.usuarios = nuevos_datos
                    else:
                        self.usuarios = datos
            except:
                self.usuarios = {}
        else:
            self.usuarios = {}
            # Crear usuario admin por defecto si no existe
            self.usuarios["admin"] = {"password": "admin123", "rol": "admin"}
            self.guardar_usuarios()
    
    def guardar_usuarios(self):
        """Guarda los usuarios en el archivo JSON"""
        try:
            with open(self.usuarios_file, "w") as f:
                json.dump(self.usuarios, f, indent=2)
        except Exception as e:
            print(f"Error guardando usuarios: {e}")
    
    def verificar_login(self, e):
        """Verifica las credenciales del usuario"""
        username = self.username_field.value.strip()
        password = self.password_field.value.strip()
        
        if not username or not password:
            self.error_text.value = "Por favor, completa todos los campos"
            self.page.update()
            return
        
        if username in self.usuarios and self.usuarios[username]["password"] == password:
            self.error_text.value = ""
            # Guardar sesión actual con rol
            self.usuario_actual = username
            self.rol_actual = self.usuarios[username]["rol"]
            self.mostrar_notificacion("✓ Inicio de sesión exitoso", ft.Colors.GREEN)
            
            # Esperar un momento antes de redirigir
            import time
            time.sleep(0.5)
            
            # Llamar al callback de éxito con usuario y rol
            self.on_login_success(username, self.rol_actual)
        else:
            self.error_text.value = "Usuario o contraseña incorrectos"
            self.page.update()
    
    def mostrar_registro(self, e):
        """Muestra el formulario de registro"""
        # Crear campos de registro
        self.registro_username = ft.TextField(
            label="Nuevo usuario",
            prefix_icon=ft.Icons.PERSON_ADD,
            width=300,
            text_size=16,
            border_color=ft.Colors.BLUE_700,
        )
        
        self.registro_password = ft.TextField(
            label="Nueva contraseña",
            prefix_icon=ft.Icons.LOCK,
            width=300,
            password=True,
            can_reveal_password=True,
            text_size=16,
            border_color=ft.Colors.BLUE_700,
        )
        
        self.registro_confirm_password = ft.TextField(
            label="Confirmar contraseña",
            prefix_icon=ft.Icons.LOCK,
            width=300,
            password=True,
            can_reveal_password=True,
            text_size=16,
            border_color=ft.Colors.BLUE_700,
        )
        
        # Crear diálogo de registro
        self.registro_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Crear nueva cuenta"),
            content=ft.Column(
                width=350,
                height=250,
                spacing=15,
                controls=[
                    self.registro_username,
                    self.registro_password,
                    self.registro_confirm_password,
                    ft.Text(
                        "",
                        color=ft.Colors.RED,
                        size=14,
                        id="registro_error"
                    )
                ]
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=self.cerrar_registro),
                ft.ElevatedButton(
                    "Registrar",
                    on_click=self.registrar_usuario,
                    bgcolor=ft.Colors.BLUE_700,
                    color=ft.Colors.WHITE,
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.dialog = self.registro_dialog
        self.registro_dialog.open = True
        self.page.update()
    
    def registrar_usuario(self, e):
        """Registra un nuevo usuario (siempre como usuario normal)"""
        username = self.registro_username.value.strip()
        password = self.registro_password.value.strip()
        confirm_password = self.registro_confirm_password.value.strip()
        
        error_text = self.registro_dialog.content.controls[-1]
        
        if not username or not password or not confirm_password:
            error_text.value = "Todos los campos son obligatorios"
            self.page.update()
            return
        
        if password != confirm_password:
            error_text.value = "Las contraseñas no coinciden"
            self.page.update()
            return
        
        if len(password) < 6:
            error_text.value = "La contraseña debe tener al menos 6 caracteres"
            self.page.update()
            return
        
        if username in self.usuarios:
            error_text.value = "El usuario ya existe"
            self.page.update()
            return
        
        # Registrar nuevo usuario como "usuario" (no admin)
        self.usuarios[username] = {"password": password, "rol": "usuario"}
        self.guardar_usuarios()
        
        # Cerrar diálogo y mostrar mensaje de éxito
        self.registro_dialog.open = False
        
        # Auto-completar campos de login
        self.username_field.value = username
        self.password_field.value = password
        self.error_text.value = ""
        
        self.mostrar_notificacion("✓ Usuario registrado exitosamente", ft.Colors.GREEN)
        self.page.update()
    
    def cerrar_registro(self, e):
        """Cierra el diálogo de registro"""
        self.registro_dialog.open = False
        self.page.update()
    
    def mostrar_notificacion(self, mensaje, color):
        """Muestra una notificación temporal"""
        snackbar = ft.SnackBar(
            content=ft.Text(mensaje, color=ft.Colors.WHITE),
            bgcolor=color,
            duration=2000,
        )
        self.page.snack_bar = snackbar
        snackbar.open = True
        self.page.update()


class UI(ft.Container):
    def __init__(self, page):
        super().__init__(expand=True)
        self.page = page
        self.usuario_actual = None
        self.rol_actual = None
        
        # Guardar referencia en la página para que otros componentes puedan acceder
        self.page.ui_instance = self
        
        # Primero mostrar pantalla de login
        self.mostrar_login()
    
    def mostrar_login(self):
        """Muestra la pantalla de inicio de sesión"""
        self.login_screen = LoginScreen(
            page=self.page,
            on_login_success=self.on_login_success
        )
        
        # Configurar la página para login
        self.page.clean()
        self.page.add(
            ft.Container(
                width=self.page.width,
                height=self.page.height,
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_center,
                    end=ft.alignment.bottom_center,
                    colors=[ft.Colors.BLUE_50, ft.Colors.GREY_100]
                ),
                content=ft.Column(
                    expand=True,
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[self.login_screen.content]
                )
            )
        )
        self.page.update()
    
    def on_login_success(self, username, rol):
        """Se ejecuta cuando el login es exitoso"""
        self.usuario_actual = username
        self.rol_actual = rol
        
        # Inicializar la aplicación principal
        self.inicializar_aplicacion()
    
    def inicializar_aplicacion(self):
        """Inicializa la aplicación principal después del login"""
        # Limpiar la página
        self.page.clean()
        
        # Inicializar todos los componentes como antes
        self.datos_tiempo_real = {
            'temperatura': 0,
            'humedad': 0, 
            'presion1': 0,
            'presion2': 0,
            'presion3': 0,
        }

        self.excel_manager = ExcelUnicoArchivo()
        
        self.reloj_global = RelojGlobal()
        self.sistema_alertas = SistemaAlertas()
        self.alertas_view = None

        self.reloj_global.agregar_callback(self._on_alarma)
        # Agregar callback para historial
        self.reloj_global.agregar_callback_historial(self._on_nuevo_registro)
        
        self.color_teal = ft.Colors.GREY_300

        # Agregar barra de usuario en la parte superior
        self.barra_usuario = self.crear_barra_usuario()
        
        self._initialize_ui_components()
        
        # Crear layout principal con barra de usuario
        layout_principal = ft.Column(
            expand=True,
            controls=[
                self.barra_usuario,
                ft.Container(
                    expand=True,
                    content=self.resp_container
                )
            ]
        )
        
        self.content = layout_principal
        
        self.configurar_banner()
        self.inicializar_alertas_view()
        
        # Agregar a la página
        self.page.add(self)
        self.page.update()
    
    def crear_barra_usuario(self):
        """Crea la barra superior con información del usuario"""
        # Determinar color según el rol
        rol_color = ft.Colors.GREEN if self.rol_actual == "admin" else ft.Colors.BLUE
        rol_texto = "Administrador" if self.rol_actual == "admin" else "Usuario"
        
        return ft.Container(
            height=60,
            bgcolor=ft.Colors.BLUE_700,
            padding=ft.padding.symmetric(horizontal=20),
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.PERSON, color=ft.Colors.WHITE, size=24),
                            ft.Text(
                                f"{self.usuario_actual}",
                                color=ft.Colors.WHITE,
                                size=18,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Container(
                                content=ft.Text(
                                    rol_texto,
                                    color=ft.Colors.WHITE,
                                    size=12,
                                ),
                                bgcolor=rol_color,
                                padding=ft.padding.symmetric(horizontal=8, vertical=3),
                                border_radius=10,
                            ),
                        ],
                        spacing=10,
                    ),
                    ft.Row(
                        controls=[
                            ft.Text(
                                datetime.datetime.now().strftime("%d/%m/%Y %H:%M"),
                                color=ft.Colors.WHITE,
                                size=16,
                            ),
                            ft.IconButton(
                                icon=ft.Icons.LOGOUT,
                                icon_color=ft.Colors.WHITE,
                                tooltip="Cerrar sesión",
                                on_click=self.cerrar_sesion,
                            ),
                        ],
                        spacing=15,
                    ),
                ]
            )
        )
    
    def cerrar_sesion(self, e):
        """Cierra la sesión actual y vuelve al login"""
        self.mostrar_login()
    
    def inicializar_alertas_view(self):
        """Inicializa AlertasView después de que todo esté listo"""
        self.alertas_view = AlertasView(self.sistema_alertas, self.page)
        self.actualizar_setting_container()

    def actualizar_setting_container(self):
        """Actualiza el contenedor de settings con el AlertasView"""
        if self.alertas_view is None:
            return
            
        self.setting_container_1.content = ft.Column(
            expand=True,
            controls=[
                ft.Container(
                    padding=10,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=10,
                    shadow=ft.BoxShadow(
                        spread_radius=1,
                        blur_radius=5,
                        color=ft.Colors.GREY_300,
                    ),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[
                            ft.Icon(ft.Icons.NOTIFICATIONS_ACTIVE, color=ft.Colors.RED_700, size=28),
                            ft.Text(
                                "Historial de Alertas del Sistema",
                                size=20,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.BLUE_900
                            ),
                        ],
                        spacing=15
                    )
                ),
                ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                ft.Container(
                    expand=True,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=15,
                    padding=10,
                    shadow=ft.BoxShadow(
                        spread_radius=1,
                        blur_radius=5,
                        color=ft.Colors.GREY_300,
                    ),
                    content=self.alertas_view
                )
            ]
        )

    def _on_nuevo_registro(self, registro):
        """Se ejecuta cuando se agrega un nuevo registro al historial"""
        # Actualizar el historial en la configuración si existe
        if hasattr(self, 'config_container') and hasattr(self.config_container, 'actualizar_historial_desde_externo'):
            def actualizar():
                self.config_container.actualizar_historial_desde_externo()
            
            # Ejecutar en el hilo de la UI
            if self.page:
                self.page.run_thread(actualizar)

    def registrar_manual(self, e=None):
        """Registra un dato manualmente desde el botón en Home"""
        print("Registro manual solicitado")
        datos_actuales = self.obtener_datos_actuales_redondeados()
        
        registro = self.reloj_global.agregar_al_historial(
            datos_actuales, 
            tipo="registro_manual", 
            fuente="Manual (Home)"
        )
        
        self.sistema_alertas.agregar_alerta(
            causa="Registro manual ejecutado desde Home",
            pagina="UMA",
            datos_adicionales={
                "fecha": registro["fecha"],
                "hora": registro["hora"]
            }
        )
        
        self.mostrar_notificacion("✓ Registro manual agregado", ft.Colors.GREEN)
    
    def limpiar_historial_completamente(self, e=None):
        """Limpia todo el historial"""
        def confirmar_limpieza(e):
            self.reloj_global.limpiar_historial()
            dlg_modal.open = False
            self.page.update()
            self.mostrar_notificacion("✓ Historial limpiado", ft.Colors.GREEN)
            self.sistema_alertas.agregar_alerta(
                causa="Historial de registros limpiado",
                pagina="UMA"
            )
        
        def cancelar_limpieza(e):
            dlg_modal.open = False
            self.page.update()
        
        dlg_modal = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmar limpieza"),
            content=ft.Text("¿Está seguro que desea eliminar TODOS los registros del historial?\nEsta acción no se puede deshacer."),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar_limpieza),
                ft.ElevatedButton(
                    "Limpiar Todo", 
                    on_click=confirmar_limpieza,
                    bgcolor=ft.Colors.RED,
                    color=ft.Colors.WHITE
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.dialog = dlg_modal
        dlg_modal.open = True
        self.page.update()
    
    def mostrar_notificacion(self, mensaje, color):
        """Muestra una notificación temporal"""
        snackbar = ft.SnackBar(
            content=ft.Text(mensaje, color=ft.Colors.WHITE),
            bgcolor=color,
            duration=2000,
        )
        self.page.snack_bar = snackbar
        snackbar.open = True
        self.page.update()

    def configurar_banner(self):
        self.banner = ft.Banner(
            bgcolor=ft.Colors.AMBER_100,
            leading=ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=ft.Colors.AMBER, size=40),
            content=ft.Text(
                "Sistema de monitoreo iniciado",
                color=ft.Colors.BLACK,
            ),
            actions=[
                ft.TextButton("OK", on_click=self.cerrar_banner)
            ],
        )
        self.page.banner = self.banner
        self.mostrar_banner_inicio()

    def mostrar_banner_inicio(self):
        self.page.banner.open = True
        self.page.update()

    def cerrar_banner(self, e):
        self.page.banner.open = False
        self.page.update()

    def _on_alarma(self, hora):
        """Se ejecuta cuando el reloj global detecta una alarma"""
        print(f"UI: Alarma recibida: {hora}")
        
        datos_actuales = self.obtener_datos_actuales_redondeados()
        
        if hasattr(self, 'excel_manager'):
            self.excel_manager.guardar_todos(datos_actuales)
            
        registro = self.reloj_global.agregar_al_historial(
            datos_actuales, 
            tipo="registro_automatico", 
            fuente=f"Alarma {hora}"
        )
        
        # FORZAR ACTUALIZACIÓN DE UMA INMEDIATAMENTE
        if hasattr(self, 'uma_instance'):
            self.page.run_thread(lambda: self.uma_instance.actualizar_lista())
        
        self.sistema_alertas.agregar_alerta(
            causa=f"Registro automático ejecutado a las {hora}",
            pagina="Reloj Global",
        )
        
        self.mostrar_notificacion(f"✓ Registro automático a las {hora}", ft.Colors.BLUE)

    def obtener_datos_actuales_redondeados(self):
        """Obtiene los datos actuales redondeados"""
        datos = self.datos_tiempo_real.copy()
        datos['temperatura'] = round(datos['temperatura'], 1)
        datos['humedad'] = round(datos['humedad'])
        datos['presion1'] = round(datos['presion1'], 1)
        datos['presion2'] = round(datos['presion2'], 1)
        datos['presion3'] = round(datos['presion3'], 1)
        return datos

    def _initialize_ui_components(self):
        """Inicializa todos los componentes de la interfaz de usuario"""
        # 1. Crear controles de texto para UMA
        self.txt_temp_home = ft.Text("-- °C", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800)
        self.txt_hum_home = ft.Text("-- %", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800)
        self.txt_pres_home = ft.Text("-- Pa", size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE_800)
        
        # 2. Crear UMA
        self.uma_instance = UMA(
            txt_temp=self.txt_temp_home,
            txt_hum=self.txt_hum_home,
            txt_pres=self.txt_pres_home,
            page=self.page,
            reloj_global=self.reloj_global
        )

        self.blue_box_presion1 = BlueBox(texto_titulo="MANOMETRO 1",texto=f"{self.datos_tiempo_real['presion1']} Pa", mostrar_boton=False)
        self.blue_box_presion2 = BlueBox(texto_titulo="MANOMETRO 2",texto=f"{self.datos_tiempo_real['presion2']} Pa", mostrar_boton=False)
        self.blue_box_presion3 = BlueBox(texto_titulo="MANOMETRO 3",texto=f"{self.datos_tiempo_real['presion3']} Pa", mostrar_boton=False)
        
        self.blue_boxes = {
            'presion1': self.blue_box_presion1,
            'presion2': self.blue_box_presion2,
            'presion3': self.blue_box_presion3,
        }

        # SOLO crear config_container si es admin
        if self.rol_actual == "admin":
            print(f"DEBUG: Creando ConfiguracionContainer para admin: {self.usuario_actual}")
            self.config_container = ConfiguracionContainer(
                page=self.page,
                reloj_global=self.reloj_global,
                usuario_actual=self.usuario_actual,
                rol_actual=self.rol_actual
            )
            print("DEBUG: ConfiguracionContainer creado para admin")
        else:
            self.config_container = ft.Container(
                bgcolor=ft.Colors.WHITE,
                border_radius=20,
                expand=True,
                alignment=ft.alignment.center,
                content=ft.Column(
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=20,
                    controls=[
                        ft.Icon(ft.Icons.LOCK, size=80, color=ft.Colors.GREY_400),
                        ft.Text(
                            "Acceso Restringido",
                            size=28,
                            weight=ft.FontWeight.BOLD,
                            color=ft.Colors.GREY_600,
                        ),
                        ft.Text(
                            "Esta sección solo está disponible\npara usuarios administradores",
                            size=16,
                            color=ft.Colors.GREY_500,
                            text_align=ft.TextAlign.CENTER,
                        ),
                    ]
                )
            )

        # PAGUINA 1 (UMA)
        self.home_container_1 = ft.Container(
            bgcolor=self.color_teal,
            border_radius=20,
            expand=True,
            padding=20,
            alignment=ft.alignment.center,
            content=ft.Column(
                expand=True,
                controls=[
                    self.uma_instance,
                ]
            )
        )

        # PAGUINA 2 (MANOMETROS)
        self.location_container_1 = ft.Container(
            bgcolor=self.color_teal,
            border_radius=20,
            expand=True,
            padding=20,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
                controls=[
                    ft.Container(
                        expand=True,
                        bgcolor=ft.Colors.WHITE,
                        border_radius=20,
                        alignment=ft.alignment.center,
                        padding=20,
                        shadow=ft.BoxShadow(
                            spread_radius=1,
                            blur_radius=10,
                            color=ft.Colors.GREY_300,
                        ),
                        content=ft.Column(
                            scroll=ft.ScrollMode.AUTO,
                            spacing=30,
                            controls=[
                                ft.Row(
                                    alignment=ft.MainAxisAlignment.CENTER,
                                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                                    spacing=30,
                                    controls=[
                                        self.blue_box_presion1,
                                        self.blue_box_presion2,
                                        self.blue_box_presion3,
                                    ]
                                )
                            ]
                        )
                    )
                ]
            )
        )

        # PAGUINA 3 (CONFIGURACION)
        self.calendar_container_1 = ft.Container(
            bgcolor=self.color_teal,
            border_radius=20,
            expand=True,
            padding=20,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
                controls=[self.config_container]
            )
        )

        # PAGUINA 4 (ALERTAS)
        self.setting_container_1 = ft.Container(
            bgcolor=self.color_teal,
            border_radius=20,
            expand=True,
            padding=20,
            content=ft.Container()  # Contenedor temporal vacío
        )

        # Lista de contenedores - MODIFICADO según rol
        if self.rol_actual == "admin":
            # Admin: UMA, Manómetros, Configuración, Alertas
            self.container_list_1 = [
                self.home_container_1,          # 0: UMA
                self.location_container_1,      # 1: Manómetros
                self.calendar_container_1,      # 2: Configuración
                self.setting_container_1        # 3: Alertas
            ]
        else:
            # Usuario normal: UMA, Manómetros, Alertas (NO Configuración)
            self.container_list_1 = [
                self.home_container_1,          # 0: UMA
                self.location_container_1,      # 1: Manómetros
                self.setting_container_1        # 2: Alertas
            ]
        
        self.container_1 = ft.Container(
            content=self.container_list_1[0], 
            expand=True,
            animate=ft.Animation(300, ft.AnimationCurve.EASE_IN_OUT)
        )

        # Botones de navegación - MODIFICADO según rol
        botones_navegacion = []
        
        # Botón UMA (siempre visible)
        self.btn_connect = ft.Container(
            width=130,
            height=50,
            bgcolor=ft.Colors.AMBER,
            border_radius=50,
            alignment=ft.alignment.center,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            animate=ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
            on_hover=self.Check_On_Hover,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                controls=[
                    ft.Text("UMA", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)
                ]
            ),
            on_click=lambda e: self.change_page_manual(0)
        )
        botones_navegacion.append(self.btn_connect)
        
        # Botón Manómetros (siempre visible)
        self.btn_connect2 = ft.Container(
            width=130,
            height=50,
            bgcolor=ft.Colors.BLUE,
            border_radius=50,
            alignment=ft.alignment.center,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            animate=ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
            on_hover=self.Check_On_Hover,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                controls=[
                    ft.Text("Manometros", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)
                ]
            ),
            on_click=lambda e: self.change_page_manual(1)
        )
        botones_navegacion.append(self.btn_connect2)
        
        # Botón Alertas (siempre visible)
        self.btn_connect3 = ft.Container(
            width=130,
            height=50,
            bgcolor=ft.Colors.GREEN,
            border_radius=50,
            alignment=ft.alignment.center,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            animate=ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
            on_hover=self.Check_On_Hover,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
                controls=[
                    ft.Text("Alertas", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)
                ]
            ),
            on_click=lambda e: self.change_page_manual(2 if self.rol_actual != "admin" else 3)
        )
        botones_navegacion.append(self.btn_connect3)
        
        # Botón Configuración (SOLO para admin)
        if self.rol_actual == "admin":
            self.btn_connect4 = ft.Container(
                width=130,
                height=50,
                bgcolor=ft.Colors.RED,
                border_radius=50,
                alignment=ft.alignment.center,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                animate=ft.Animation(200, ft.AnimationCurve.EASE_IN_OUT),
                on_hover=self.Check_On_Hover,
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.CENTER,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=10,
                    controls=[
                        ft.Text("Configuracion", color=ft.Colors.WHITE, weight=ft.FontWeight.BOLD)
                    ]
                ),
                on_click=lambda e: self.change_page_manual(2)
            )
            botones_navegacion.append(self.btn_connect4)
        
        self.navigation_container = ft.Container(
            col=1.6,
            expand=True,
            bgcolor=self.color_teal,
            border_radius=10,
            padding=ft.padding.only(top=20),
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.Colors.GREY_400,
            ),
            content=ft.Column(
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
                spacing=15,
                controls=botones_navegacion
            )
        )

        self.frame_2 = ft.Container(
            col=10,
            alignment=ft.alignment.center,
            bgcolor=self.color_teal,
            expand=True,
            content=ft.Column(
                expand=True,
                controls=[
                    self.container_1,
                ]
            )   
        )
        
        self.resp_container = ft.ResponsiveRow(
            vertical_alignment=ft.CrossAxisAlignment.STRETCH,
            controls=[
                self.navigation_container,
                self.frame_2,
            ]
        )

        self.iniciar_home_random()
        self.actualizar_colores_botones(0)

    def redondear_entero_desde_6(self, valor):
        """Redondea hacia arriba desde 0.6"""
        parte_entera = int(valor)
        decimal = valor - parte_entera
        return parte_entera + 1 if decimal >= 0.6 else parte_entera
    
    def generar_datos_random(self):
        """Genera datos aleatorios con verificación de alertas"""
        temp_original = random.uniform(15, 35)
        hum_original = random.uniform(30, 90)
        pres1_original = random.uniform(80, 110)
        pres2_original = random.uniform(80, 110)
        pres3_original = random.uniform(80, 110)

        temp = self.redondear_entero_desde_6(temp_original)
        hum = self.redondear_entero_desde_6(hum_original)
        pres1 = self.redondear_entero_desde_6(pres1_original)
        pres2 = self.redondear_entero_desde_6(pres2_original)
        pres3 = self.redondear_entero_desde_6(pres3_original)

        self.datos_tiempo_real = {
            'temperatura': temp,
            'humedad': hum, 
            'presion1': pres1,
            'presion2': pres2,
            'presion3': pres3,
        }

        # Actualizar manómetros
        for key, box in self.blue_boxes.items():
            if hasattr(box, 'actualizar_valor'):
                valor = self.datos_tiempo_real[key]
                box.actualizar_valor(f"{valor} Pa")

        # Verificar alertas
        if temp > 30:
            self.sistema_alertas.agregar_alerta(
                causa=f"Temperatura CRÍTICA: {temp}°C (supera 30°C)",
                pagina="UMA"
            )
        
        if hum > 85:
            self.sistema_alertas.agregar_alerta(
                causa=f"Humedad ALTA: {hum}% (superior a 85%)",
                pagina="UMA"
            )
        
        if pres1 > 108:
            self.sistema_alertas.agregar_alerta(
                causa=f"Presión ALTA: {pres1}Pa (supera 108 Pa)",
                pagina="UMA"
            )
        
        if pres2 > 108:
            self.sistema_alertas.agregar_alerta(
                causa=f"Presión ALTA: {pres2}Pa (supera 108 Pa)",
                pagina="UMA"
            )
        
        if pres3 > 108:
            self.sistema_alertas.agregar_alerta(
                causa=f"Presión ALTA: {pres3}Pa (supera 108 Pa)",
                pagina="UMA"
            )
        
        return {"presion1": pres1, "presion2": pres2, "presion3": pres3, "temperatura": temp, "humedad": hum}
    
    def iniciar_home_random(self):
        """Inicia la generación aleatoria de datos"""
        def loop():
            while True:
                datos = self.generar_datos_random()
                
                def actualizar():
                    # Actualiza los controles que UMA usa
                    self.txt_temp_home.value = f"{datos['temperatura']} °C"
                    self.txt_hum_home.value = f"{datos['humedad']} %"
                    self.txt_pres_home.value = f"{datos['presion1']} Pa"
                    self.page.update()
                
                self.page.run_thread(actualizar)
                time.sleep(2)
        
        threading.Thread(target=loop, daemon=True).start()

    def change_page_manual(self, index):
        """Cambia entre páginas de la aplicación"""
        if index < len(self.container_list_1):
            self.container_1.content = self.container_list_1[index]
            self.actualizar_colores_botones(index)
            
            if self.alertas_view is not None:
                # Determinar índice de alertas según rol
                alertas_index = 2 if self.rol_actual != "admin" else 3
                if index == alertas_index:  # Página de alertas
                    if hasattr(self.alertas_view, 'entrar_a_pagina'):
                        self.alertas_view.entrar_a_pagina()
                else:
                    if hasattr(self.alertas_view, 'salir_de_pagina'):
                        self.alertas_view.salir_de_pagina()

            self.page.update()
    
    def actualizar_colores_botones(self, index_activo):
        """Actualiza los colores y formas de los botones de navegación"""
        # Determinar qué botones están presentes según rol
        botones = []
        botones.append(self.btn_connect)  # UMA (siempre)
        botones.append(self.btn_connect2)  # Manómetros (siempre)
        
        if self.rol_actual == "admin":
            botones.append(self.btn_connect4)  # Configuración (solo admin)
        
        botones.append(self.btn_connect3)  # Alertas (siempre)
        
        for i, btn in enumerate(botones):
            if i == index_activo:
                # Botón activo: VERDE con bordes REDONDEADOS y DESHABILITADO
                btn.bgcolor = ft.Colors.GREEN_700
                btn.border_radius = 50
                btn.scale = ft.Scale(1.05)
                btn.disabled = True
                self.boton_activo_actual = btn
                btn.shadow = ft.BoxShadow(
                    spread_radius=2,
                    blur_radius=10,
                    color=ft.Colors.GREEN_400,
                )
            else:
                # Botones inactivos: TODOS AZULES con bordes CUADRADOS
                btn.bgcolor = ft.Colors.BLUE_700
                btn.border_radius = 5
                btn.scale = ft.Scale(1.0)
                btn.disabled = False
                btn.shadow = None
        
        # Forzar actualización de todos los botones
        for btn in botones:
            try:
                btn.update()
            except:
                pass

    def Check_On_Hover(self, e):
        ctrl = e.control
        is_hover = (e.data == "true" or e.data is True)
        
        # Si es el botón activo, no hacer nada
        if hasattr(self, 'boton_activo_actual') and ctrl == self.boton_activo_actual:
            return
        
        # Solo aplicar hover a botones inactivos
        if is_hover:
            ctrl.scale = ft.Scale(1.05)
            # Oscurecer el azul
            ctrl.bgcolor = ft.Colors.BLUE_900
            ctrl.shadow = ft.BoxShadow(
                spread_radius=2,
                blur_radius=15,
                color=ft.Colors.BLACK54,
            )
        else:
            ctrl.scale = ft.Scale(1.0)
            # Volver al azul normal
            ctrl.bgcolor = ft.Colors.BLUE_700
            ctrl.shadow = None
        
        ctrl.update()


def main(page: ft.Page):
    page.title = "Sistema de Monitoreo Inteligente"
    page.window.width = 1316
    page.window.height = 700
    page.window.resizable = True
    page.window.min_width = 1200
    page.window.min_height = 600
    page.horizontal_alignment = "center"
    page.vertical_alignment = "center"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.bgcolor = ft.Colors.GREY_200
    page.padding = 0

    # Crear la interfaz de usuario
    ui = UI(page)

if __name__ == "__main__":
    ft.app(target=main)