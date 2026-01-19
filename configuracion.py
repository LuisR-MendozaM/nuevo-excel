import flet as ft
import datetime
import json
import os
import pandas as pd
import threading
from collections import defaultdict
import time

class ConfiguracionContainer(ft.Container):
    def __init__(self, page=None, reloj_global=None, usuario_actual=None, rol_actual=None):
        super().__init__(expand=True)
        
        self.page = page
        self.reloj_global = reloj_global
        self.usuario_actual = usuario_actual
        self.rol_actual = rol_actual
        self.hora_objetivo = None
        
        # Archivo de usuarios
        self.usuarios_file = "usuarios.json"
        
        # Diccionario para almacenar diálogos por usuario
        self.dialogos_usuarios = {}
        
        # ---------- TIME PICKER ----------
        self.time_picker = ft.TimePicker(
            confirm_text="Aceptar",
            help_text="Selecciona una hora",
            on_change=self.hora_seleccionada,
        )
        
        if page:
            page.overlay.append(self.time_picker)

        # ---------- TEXTO HORA ACTUAL ----------
        self.texto_hora = ft.Text(
            value="--:-- --",
            size=28,
            weight="bold",
            color="black",
        )

        # ---------- BOTÓN ----------
        self.btn_seleccionar = ft.ElevatedButton(
            "Seleccionar hora",
            on_click=self.abrir_time_picker,
            width=130,
            height=48,
        )

        # ---------- LISTA DE HORAS ----------
        self.lista_horas = ft.Column(spacing=5, scroll=ft.ScrollMode.AUTO)

        # ---------- GESTIÓN DE USUARIOS ----------
        self.controles_usuarios = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
        
        # ---------- HISTORIAL DE REGISTROS ----------
        self.historial_registros = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO)
        
        # ---------- PESTAÑAS ----------
        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(text="Configuración de Horas"),
                ft.Tab(text="Gestión de Usuarios"),
                ft.Tab(text="Historial de Registros"),
            ],
            on_change=self.cambiar_pestana
        )
        
        # Crear contenedores para cada pestaña
        self.contenedor_horas = self.crear_contenedor_horas()
        self.contenedor_usuarios = self.crear_contenedor_usuarios()
        self.contenedor_historial = self.crear_contenedor_historial()
        
        # Contenedor que mostrará la pestaña activa
        self.contenedor_activo = ft.Container(
            expand=True,
            content=self.contenedor_horas
        )

        # ---------- INTERFAZ PRINCIPAL ----------
        self.content = ft.Column(
            alignment=ft.MainAxisAlignment.START,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
            controls=[
                ft.Container(
                    padding=ft.padding.only(bottom=10),
                    content=self.tabs
                ),
                self.contenedor_activo
            ]
        )

        # Cargar horas desde el reloj global si existe
        self.actualizar_lista_horas()
        
        # Iniciar solo la actualización de la hora visual
        self.iniciar_actualizacion_hora_visual()
        
        # Cargar historial de registros
        self.cargar_y_mostrar_historial()

    def crear_contenedor_horas(self):
        """Crea el contenedor para la pestaña de horas"""
        return ft.Container(
            expand=True,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
                controls=[
                    ft.Container(
                        bgcolor="white",
                        height=100,
                        border_radius=20,
                        alignment=ft.alignment.center,
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_AROUND,
                            controls=[self.texto_hora, self.btn_seleccionar]
                        )
                    ),
                    ft.Divider(height=9, thickness=3, color=ft.Colors.BLACK),
                    ft.Text("Horas registradas:", size=16, weight="bold"),
                    ft.Container(
                        bgcolor="white",
                        border_radius=20,
                        expand=True,
                        padding=10,
                        content=self.lista_horas
                    )
                ]
            )
        )

    def crear_contenedor_usuarios(self):
        """Crea el contenedor para la pestaña de usuarios"""
        if self.rol_actual != "admin":
            return ft.Container(
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
        else:
            # Botón para agregar nuevo usuario
            btn_agregar_usuario = ft.ElevatedButton(
                text="Agregar Nuevo Usuario",
                icon=ft.Icons.PERSON_ADD,
                on_click=lambda e: self.abrir_dialogo_gestion_usuarios("agregar"),
                width=300,
                height=45,
                style=ft.ButtonStyle(
                    bgcolor=ft.Colors.GREEN_700,
                    color=ft.Colors.WHITE,
                )
            )
            
            # Actualizar lista de usuarios
            self.actualizar_lista_usuarios()
            
            return ft.Container(
                expand=True,
                content=ft.Column(
                    alignment=ft.MainAxisAlignment.START,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    expand=True,
                    spacing=15,
                    controls=[
                        btn_agregar_usuario,
                        ft.Divider(height=10, thickness=2, color=ft.Colors.GREY_400),
                        ft.Text("Usuarios registrados:", size=18, weight="bold", color=ft.Colors.BLUE_900),
                        ft.Container(
                            bgcolor=ft.Colors.WHITE,
                            border_radius=15,
                            padding=15,
                            expand=True,
                            content=self.controles_usuarios
                        )
                    ]
                )
            )

    def crear_contenedor_historial(self):
        """Crea el contenedor para la pestaña de historial de registros"""
        # Botón para limpiar historial
        btn_limpiar_historial = ft.ElevatedButton(
            text="Limpiar Historial",
            icon=ft.Icons.DELETE_FOREVER,
            on_click=self.limpiar_historial,
            width=200,
            height=45,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.RED_700,
                color=ft.Colors.WHITE,
            )
        )
        
        # Texto informativo
        texto_info = ft.Text(
            "Descarga archivos Excel organizados por mes con todos los registros",
            size=14,
            color=ft.Colors.GREY_600,
            text_align=ft.TextAlign.CENTER,
        )
        
        return ft.Container(
            expand=True,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
                spacing=15,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text("Historial de Registros por Mes:", size=20, weight="bold", color=ft.Colors.BLUE_900),
                            btn_limpiar_historial
                        ]
                    ),
                    texto_info,
                    ft.Divider(height=10, thickness=2, color=ft.Colors.GREY_400),
                    ft.Container(
                        bgcolor=ft.Colors.WHITE,
                        border_radius=15,
                        padding=15,
                        expand=True,
                        content=self.historial_registros
                    )
                ]
            )
        )

    def cargar_y_mostrar_historial(self):
        """Carga y muestra el historial de registros organizado por mes"""
        self.historial_registros.controls.clear()
        
        # Cargar historial desde el reloj global si existe
        if self.reloj_global and hasattr(self.reloj_global, 'historial_registros'):
            historial = self.reloj_global.historial_registros
            
            if not historial:
                self.historial_registros.controls.append(
                    ft.Container(
                        padding=20,
                        alignment=ft.alignment.center,
                        content=ft.Text(
                            "No hay registros en el historial",
                            size=16,
                            color=ft.Colors.GREY_500,
                            italic=True
                        )
                    )
                )
                return
            
            # Agrupar registros por mes
            registros_por_mes = self.agrupar_registros_por_mes(historial)
            
            if not registros_por_mes:
                self.historial_registros.controls.append(
                    ft.Container(
                        padding=20,
                        alignment=ft.alignment.center,
                        content=ft.Text(
                            "No hay registros en el historial",
                            size=16,
                            color=ft.Colors.GREY_500,
                            italic=True
                        )
                    )
                )
                return
            
            # Crear una fila para cada mes
            for mes_key, registros in registros_por_mes.items():
                fila = self.crear_fila_mes(mes_key, registros)
                self.historial_registros.controls.append(fila)

    def agrupar_registros_por_mes(self, historial):
        """Agrupa los registros por mes (YYYY-MM)"""
        registros_por_mes = defaultdict(list)
        
        for registro in historial:
            try:
                # Parsear fecha del registro
                fecha_str = registro["fecha"]
                # Formato: dd/mm/yy
                dia, mes, anio = fecha_str.split('/')
                anio_completo = f"20{anio}" if len(anio) == 2 else anio
                
                # Crear clave del mes (YYYY-MM)
                mes_key = f"{anio_completo}-{mes.zfill(2)}"
                
                # Obtener nombre del mes en español
                meses_es = {
                    "01": "Enero", "02": "Febrero", "03": "Marzo", "04": "Abril",
                    "05": "Mayo", "06": "Junio", "07": "Julio", "08": "Agosto",
                    "09": "Septiembre", "10": "Octubre", "11": "Noviembre", "12": "Diciembre"
                }
                nombre_mes = meses_es.get(mes, f"Mes {mes}")
                
                # Agregar registro al mes correspondiente
                registros_por_mes[mes_key].append({
                    "registro": registro,
                    "nombre_mes": nombre_mes,
                    "anio": anio_completo
                })
            except Exception as e:
                print(f"Error procesando registro: {e}")
                continue
        
        return dict(registros_por_mes)

    def crear_fila_mes(self, mes_key, registros_mes):
        """Crea una fila para mostrar un mes con sus registros"""
        # Obtener información del mes
        primer_registro = registros_mes[0]
        nombre_mes = primer_registro["nombre_mes"]
        anio = primer_registro["anio"]
        
        # Contar registros por tipo
        total_registros = len(registros_mes)
        automaticos = sum(1 for r in registros_mes if r["registro"]["tipo"] == "registro_automatico")
        manuales = sum(1 for r in registros_mes if r["registro"]["tipo"] == "registro_manual")
        
        # Crear botón para descargar Excel del mes
        btn_descargar = ft.ElevatedButton(
            text=f"Descargar {nombre_mes} {anio}",
            icon=ft.Icons.DOWNLOAD,
            on_click=lambda e, mes=mes_key, regs=registros_mes: self.descargar_excel_mes(mes, regs),
            width=250,
            height=45,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.GREEN_700,
                color=ft.Colors.WHITE,
            )
        )
        
        # Crear fila
        fila = ft.Container(
            padding=20,
            border_radius=12,
            bgcolor=ft.Colors.GREY_50,
            border=ft.border.all(1, ft.Colors.GREY_300),
            margin=ft.margin.only(bottom=15),
        )
        
        fila.content = ft.Column(
            spacing=12,
            controls=[
                # Fila superior: Mes y botón
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Column(
                            spacing=5,
                            controls=[
                                ft.Text(
                                    f"{nombre_mes} {anio}",
                                    size=22,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.BLUE_900,
                                ),
                                ft.Text(
                                    f"Total registros: {total_registros}",
                                    size=14,
                                    color=ft.Colors.GREY_700,
                                )
                            ]
                        ),
                        btn_descargar
                    ]
                ),
                
                # Información de tipos de registros
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=10, vertical=8),
                    bgcolor=ft.Colors.WHITE,
                    border_radius=8,
                    content=ft.Row(
                        spacing=30,
                        controls=[
                            ft.Column(
                                spacing=3,
                                controls=[
                                    ft.Text(
                                        "Registros Automáticos",
                                        size=12,
                                        color=ft.Colors.GREY_600,
                                    ),
                                    ft.Container(
                                        content=ft.Text(
                                            f"{automaticos}",
                                            size=16,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.BLUE_700,
                                        ),
                                        padding=ft.padding.symmetric(horizontal=10, vertical=4),
                                        bgcolor=ft.Colors.BLUE_50,
                                        border_radius=6,
                                    )
                                ]
                            ),
                            ft.Column(
                                spacing=3,
                                controls=[
                                    ft.Text(
                                        "Registros Manuales",
                                        size=12,
                                        color=ft.Colors.GREY_600,
                                    ),
                                    ft.Container(
                                        content=ft.Text(
                                            f"{manuales}",
                                            size=16,
                                            weight=ft.FontWeight.BOLD,
                                            color=ft.Colors.GREEN_700,
                                        ),
                                        padding=ft.padding.symmetric(horizontal=10, vertical=4),
                                        bgcolor=ft.Colors.GREEN_50,
                                        border_radius=6,
                                    )
                                ]
                            ),
                            ft.Column(
                                spacing=3,
                                controls=[
                                    ft.Text(
                                        "Periodo",
                                        size=12,
                                        color=ft.Colors.GREY_600,
                                    ),
                                    ft.Container(
                                        content=ft.Text(
                                            f"{mes_key}",
                                            size=14,
                                            color=ft.Colors.GREY_700,
                                        ),
                                        padding=ft.padding.symmetric(horizontal=10, vertical=4),
                                        bgcolor=ft.Colors.GREY_100,
                                        border_radius=6,
                                    )
                                ]
                            )
                        ]
                    )
                )
            ]
        )
        
        return fila

    def descargar_excel_mes(self, mes_key, registros_mes):
        """Descarga todos los registros de un mes como archivo Excel"""
        try:
            # Preparar datos para Excel
            datos_excel = []
            
            for item in registros_mes:
                registro = item["registro"]
                datos = registro["datos"]
                
                # Convertir fecha al formato YYYY-MM-DD para ordenamiento
                fecha_str = registro["fecha"]  # Formato: dd/mm/yy
                hora_str = registro["hora"]     # Formato: HH:MM
                
                # Parsear fecha
                dia, mes, anio = fecha_str.split('/')
                anio_completo = f"20{anio}" if len(anio) == 2 else anio
                fecha_iso = f"{anio_completo}-{mes.zfill(2)}-{dia.zfill(2)}"
                
                # Crear fila para Excel
                fila_excel = {
                    "Fecha": fecha_iso,
                    "Hora": hora_str,
                    "Tipo": "Automático" if registro["tipo"] == "registro_automatico" else "Manual",
                    "Fuente": registro.get("fuente", "Sistema"),
                    "Temperatura (°C)": datos.get('temperatura', '--'),
                    "Humedad (%)": datos.get('humedad', '--'),
                    "Presión 1 (Pa)": datos.get('presion1', '--'),
                    "Presión 2 (Pa)": datos.get('presion2', '--'),
                    "Presión 3 (Pa)": datos.get('presion3', '--')
                }
                
                datos_excel.append(fila_excel)
            
            # Ordenar por fecha y hora
            datos_excel.sort(key=lambda x: (x["Fecha"], x["Hora"]))
            
            # Crear DataFrame
            df = pd.DataFrame(datos_excel)
            
            # Obtener información del mes
            anio, mes_num = mes_key.split('-')
            meses_es = {
                "01": "Enero", "02": "Febrero", "03": "Marzo", "04": "Abril",
                "05": "Mayo", "06": "Junio", "07": "Julio", "08": "Agosto",
                "09": "Septiembre", "10": "Octubre", "11": "Noviembre", "12": "Diciembre"
            }
            nombre_mes = meses_es.get(mes_num, f"Mes_{mes_num}")
            
            # Crear nombre de archivo
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"Registros_{nombre_mes}_{anio}_{timestamp}.xlsx"
            
            # Ruta del escritorio
            desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
            filepath = os.path.join(desktop_path, filename)
            
            # Guardar como Excel con formato
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=f'{nombre_mes}_{anio}', index=False)
                
                # Ajustar ancho de columnas
                worksheet = writer.sheets[f'{nombre_mes}_{anio}']
                for column in df:
                    column_length = max(df[column].astype(str).map(len).max(), len(column))
                    col_idx = df.columns.get_loc(column)
                    worksheet.column_dimensions[chr(65 + col_idx)].width = column_length + 2
            
            # Mostrar notificación de éxito
            self.mostrar_notificacion(f"✓ Archivo guardado en Escritorio: {filename}", ft.Colors.GREEN)
            
            print(f"Archivo Excel guardado: {filepath}")
            print(f"Total registros: {len(datos_excel)}")
            
        except Exception as e:
            print(f"Error al guardar Excel: {e}")
            self.mostrar_notificacion(f"✗ Error al guardar archivo: {str(e)}", ft.Colors.RED)

    def limpiar_historial(self, e):
        """Limpia todo el historial de registros"""
        def confirmar_limpieza(e):
            if self.reloj_global and hasattr(self.reloj_global, 'limpiar_historial'):
                self.reloj_global.limpiar_historial()
                self.cargar_y_mostrar_historial()
                dlg.open = False
                self.page.update()
                self.mostrar_notificacion("✓ Historial limpiado", ft.Colors.GREEN)
        
        def cancelar_limpieza(e):
            dlg.open = False
            self.page.update()
        
        dlg = ft.AlertDialog(
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
        
        self.page.dialog = dlg
        dlg.open = True
        self.page.update()

    def cargar_usuarios(self):
        """Carga los usuarios desde el archivo JSON"""
        if os.path.exists(self.usuarios_file):
            try:
                with open(self.usuarios_file, "r") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def actualizar_lista_usuarios(self):
        """Actualiza la lista de usuarios en la interfaz"""
        self.controles_usuarios.controls.clear()
        
        usuarios = self.cargar_usuarios()
        
        for usuario, datos in usuarios.items():
            # No mostrar el usuario actual
            if usuario == self.usuario_actual:
                continue
                
            # Crear fila para cada usuario
            fila = self.crear_fila_usuario(usuario, datos)
            self.controles_usuarios.controls.append(fila)
        
        # Si no hay usuarios (excepto el actual)
        if len(self.controles_usuarios.controls) == 0:
            self.controles_usuarios.controls.append(
                ft.Container(
                    padding=20,
                    alignment=ft.alignment.center,
                    content=ft.Text(
                        "No hay otros usuarios registrados",
                        size=16,
                        color=ft.Colors.GREY_500,
                        italic=True
                    )
                )
            )

    def crear_fila_usuario(self, usuario, datos):
        """Crea una fila para mostrar un usuario"""
        # Determinar color según rol
        rol_color = ft.Colors.GREEN if datos["rol"] == "admin" else ft.Colors.BLUE
        rol_texto = "Administrador" if datos["rol"] == "admin" else "Usuario"
        
        fila = ft.Container(
            padding=10,
            border_radius=10,
            bgcolor=ft.Colors.GREY_100,
            border=ft.border.all(1, ft.Colors.GREY_300),
        )
        
        fila.content = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Column(
                    spacing=5,
                    controls=[
                        ft.Text(f"Usuario: {usuario}", size=16, weight="bold", color=ft.Colors.BLACK),
                        ft.Text(f"Contraseña: {'*' * 8}", size=14, color=ft.Colors.GREY_600),
                        ft.Container(
                            content=ft.Text(rol_texto, size=12, color=ft.Colors.WHITE),
                            bgcolor=rol_color,
                            padding=ft.padding.symmetric(horizontal=10, vertical=3),
                            border_radius=8,
                        )
                    ]
                ),
                ft.Row(
                    spacing=10,
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.EDIT,
                            icon_color=ft.Colors.BLUE,
                            tooltip="Editar usuario",
                            data=usuario,
                            on_click=lambda e: self.abrir_dialogo_gestion_usuarios("editar", e.control.data)
                        ),
                        ft.IconButton(
                            icon=ft.Icons.DELETE,
                            icon_color=ft.Colors.RED,
                            tooltip="Eliminar usuario",
                            data=usuario,
                            on_click=lambda e: self.abrir_dialogo_gestion_usuarios("eliminar", e.control.data)
                        )
                    ]
                )
            ]
        )
        
        return fila

    def abrir_dialogo_gestion_usuarios(self, accion, usuario=None):
        """Abre diálogos de gestión de usuarios - solo notifica a la UI principal"""
        # Esta función solo notifica a la UI principal para que abra el diálogo
        if hasattr(self.page, 'ui_instance'):
            ui_instance = self.page.ui_instance
            if accion == "agregar":
                ui_instance.mostrar_dialogo_agregar_usuario_main(None)
            elif accion == "editar" and usuario:
                ui_instance.mostrar_dialogo_editar_usuario_main(usuario)
            elif accion == "eliminar" and usuario:
                ui_instance.mostrar_dialogo_eliminar_usuario_main(usuario)

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

    def cambiar_pestana(self, e):
        """Cambia entre pestañas"""
        index = e.control.selected_index
        
        if index == 0:  # Pestaña de horas
            self.contenedor_activo.content = self.contenedor_horas
        elif index == 1:  # Pestaña de usuarios
            # Si es admin, actualizar lista de usuarios
            if self.rol_actual == "admin":
                self.actualizar_lista_usuarios()
                # Crear nuevo contenedor de usuarios
                self.contenedor_usuarios = self.crear_contenedor_usuarios()
            self.contenedor_activo.content = self.contenedor_usuarios
        else:  # Pestaña de historial (índice 2)
            # Cargar y mostrar historial
            self.cargar_y_mostrar_historial()
            # Crear nuevo contenedor de historial
            self.contenedor_historial = self.crear_contenedor_historial()
            self.contenedor_activo.content = self.contenedor_historial
        
        if self.page:
            self.page.update()

    def actualizar_lista_horas(self):
        """Actualiza la lista de horas desde el reloj global"""
        self.lista_horas.controls.clear()
        if self.reloj_global and hasattr(self.reloj_global, 'horas_registradas'):
            for hora_time in self.reloj_global.horas_registradas:
                hora_str = hora_time.strftime("%I:%M %p")
                
                # Usar el atributo data para pasar la hora
                btn_eliminar = ft.IconButton(
                    icon=ft.Icons.DELETE,
                    icon_color="red",
                    data=hora_time,  # Almacenar la hora en data
                    on_click=lambda e: self.eliminar_hora(e.control.data)
                )
                
                fila = ft.Container(
                    padding=10,
                    border_radius=8,
                    bgcolor=ft.Colors.GREY_100,
                )

                fila.content = ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(hora_str, size=16, color="black"),
                        btn_eliminar
                    ]
                )
                self.lista_horas.controls.append(fila)

    def iniciar_actualizacion_hora_visual(self):
        """Solo actualiza la hora visual, no las alarmas"""
        def actualizar_hora():
            while True:
                try:
                    ahora = datetime.datetime.now()
                    if self.page:
                        def update_ui():
                            self.texto_hora.value = ahora.strftime("%I:%M:%S %p")
                            self.page.update()
                        self.page.run_thread(update_ui)
                    time.sleep(1)
                except:
                    break
        
        thread = threading.Thread(target=actualizar_hora, daemon=True)
        thread.start()

    def abrir_time_picker(self, e):
        if self.page:
            self.time_picker.open = True
            self.page.update()

    def hora_seleccionada(self, e):
        if e.control.value:
            self.hora_objetivo = e.control.value
            hora_formato = self.hora_objetivo.strftime("%I:%M %p")

            # Usar el reloj global para agregar la hora
            if self.reloj_global and hasattr(self.reloj_global, 'agregar_hora'):
                if self.reloj_global.agregar_hora(self.hora_objetivo):
                    print("Hora agregada globalmente:", hora_formato)
                    # Actualizar lista local
                    self.actualizar_lista_horas()
                    if self.page:
                        self.page.update()

    def eliminar_hora(self, hora_time):
        """Elimina una hora usando el reloj global"""
        if self.reloj_global and hasattr(self.reloj_global, 'eliminar_hora'):
            if self.reloj_global.eliminar_hora(hora_time):
                self.actualizar_lista_horas()
                if self.page:
                    self.page.update()

    def mi_accion(self, hora):
        print(f"¡La hora {hora} ha sido alcanzada!")
        
    # Nueva función para actualizar el historial desde fuera
    def actualizar_historial_desde_externo(self):
        """Actualiza el historial cuando se llama desde fuera"""
        if self.tabs.selected_index == 2:  # Si está en la pestaña de historial
            self.cargar_y_mostrar_historial()
            if self.page:
                self.page.update()