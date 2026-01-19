import flet as ft
import json
import os
import datetime

class SistemaHistorial:
    def __init__(self, archivo="historial_registros.json"):
        self.archivo = archivo
        self.registros = []
        self.proximo_id = 1
        self.cargar_registros()

    def cargar_registros(self):
        """Carga los registros desde el archivo JSON - Lee el formato correcto"""
        if os.path.exists(self.archivo):
            try:
                with open(self.archivo, "r", encoding='utf-8') as f:
                    self.registros = json.load(f)
                
                # Asignar IDs si no existen
                for i, registro in enumerate(self.registros):
                    if "id" not in registro:
                        registro["id"] = i + 1
                
                # Calcular próximo ID
                if self.registros:
                    max_id = max(reg.get("id", 0) for reg in self.registros)
                    self.proximo_id = max_id + 1
                else:
                    self.proximo_id = 1
                    
                # print(f"Historial: {len(self.registros)} registros cargados")
            except Exception as e:
                print(f"Error cargando registros: {e}")
                self.registros = []
        else:
            # print(f"Creando nuevo archivo: {self.archivo}")
            self.registros = []
        
        return self.registros
    
    def guardar_registros(self):
        """Guarda los registros en el archivo JSON"""
        try:
            with open(self.archivo, "w", encoding='utf-8') as f:
                json.dump(self.registros, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error guardando: {e}")
    
    def agregar_registro(self, temperatura, humedad, presion, tipo="manual", fuente="UMA"):
        """Agrega un nuevo registro al historial - EN EL MISMO FORMATO que RelojGlobal"""
        ahora = datetime.datetime.now()
        
        registro = {
            "id": self.proximo_id,
            "fecha": ahora.strftime("%d/%m/%y"),
            "hora": ahora.strftime("%H:%M"),
            "datos": {  # <-- MISMO FORMATO: datos dentro de "datos"
                "temperatura": temperatura,
                "humedad": humedad,
                "presion1": presion  # <-- presion1 para coincidir
            },
            "tipo": tipo,
            "fuente": fuente
        }
        
        self.registros.append(registro)
        self.proximo_id += 1
        self.guardar_registros()
        print(f"✓ Registro #{registro['id']} agregado")
        return registro
    
    def eliminar_todos_registros(self):
        """Elimina todos los registros"""
        total = len(self.registros)
        self.registros.clear()
        self.proximo_id = 1
        self.guardar_registros()
        #print(f"{total} registros eliminados")
    
    def obtener_registros(self):
        """Devuelve todos los registros (siempre actualizados)"""
        self.cargar_registros()  # Siemrecargar para tener datos frescos
        return self.registros.copy()
    
    def contar_registros(self):
        """Cuenta el número de registros"""
        return len(self.registros)


class UMA(ft.Container):
    def __init__(self, txt_temp, txt_hum, txt_pres, page=None, reloj_global=None,  on_registro_manual=None):
        super().__init__(expand=True)
        
        self.page = page
        self.txt_temp = txt_temp
        self.txt_hum = txt_hum
        self.txt_pres = txt_pres
        self.reloj_global = reloj_global

        self.bandera_btn_registro = False
        self.on_registro_manual = on_registro_manual  # Callback
        
        # Sistema de historial
        self.historial = SistemaHistorial()
        
        # Registrar callback para actualizaciones automáticas
        if self.reloj_global:
            self.reloj_global.agregar_callback_historial(self.actualizar_lista)
        
        # Botones
        self.btn_registro = ft.ElevatedButton(
            "Registrar",
            # on_click=self.registrar_manual,
            on_click=None,
            bgcolor=ft.Colors.GREEN,
            color=ft.Colors.WHITE
        )
        
        self.btn_limpiar = ft.ElevatedButton(
            "Limpiar TODO",
            on_click=self.limpiar_todo,
            bgcolor=ft.Colors.RED,
            color=ft.Colors.WHITE
        )
        
        # Lista de historial
        self.lista_historial = ft.Column(
            spacing=5,
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )
        
        # Contador
        self.contador = ft.Text("0 registros", size=14, color=ft.Colors.GREY_700)
        
        # Construir UI
        self._construir_ui()
        
        # Cargar datos iniciales
        self.cargar_datos_despues_de_ui()
    
    def cargar_datos_despues_de_ui(self):
        """Carga los datos después de que la UI esté lista"""
        self.actualizar_lista()
    
    def _construir_ui(self):
        """Construye la interfaz de usuario"""
        self.content = ft.Column(
            expand=True,
            controls=[
                # Cabecera con botones
                ft.Container(
                    padding=20,
                    bgcolor=ft.Colors.WHITE,
                    border_radius=10,
                    margin=ft.margin.only(bottom=15),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(ft.Icons.HISTORY, color=ft.Colors.BLUE_700),
                                    ft.Text("UMA - Historial de Registros", 
                                           size=20, weight=ft.FontWeight.BOLD),
                                ]
                            ),
                            # ft.Row(
                            #     spacing=10,
                            #     controls=[self.btn_registro, self.btn_limpiar]
                            # )
                        ]
                    )
                ),
                
                # Cuerpo principal
                ft.Row(
                    expand=True,
                    spacing=20,
                    controls=[
                        # Panel izquierdo - Datos actuales
                        ft.Container(
                            width=300,
                            padding=20,
                            bgcolor=ft.Colors.WHITE,
                            border_radius=10,
                            content=ft.Column(
                                spacing=15,
                                controls=[
                                    ft.Text("Datos en Tiempo Real", 
                                           size=18, weight=ft.FontWeight.BOLD),
                                    
                                    # Temperatura
                                    ft.Container(
                                        padding=15,
                                        bgcolor=ft.Colors.BLUE_50,
                                        border_radius=10,
                                        content=ft.Column(
                                            spacing=5,
                                            controls=[
                                                ft.Text("Temperatura", 
                                                       size=14, weight=ft.FontWeight.BOLD),
                                                self.txt_temp
                                            ]
                                        )
                                    ),
                                    
                                    # Humedad
                                    ft.Container(
                                        padding=15,
                                        bgcolor=ft.Colors.GREEN_50,
                                        border_radius=10,
                                        content=ft.Column(
                                            spacing=5,
                                            controls=[
                                                ft.Text("Humedad", 
                                                       size=14, weight=ft.FontWeight.BOLD),
                                                self.txt_hum
                                            ]
                                        )
                                    ),
                                    
                                    # Presión
                                    ft.Container(
                                        padding=15,
                                        bgcolor=ft.Colors.ORANGE_50,
                                        border_radius=10,
                                        content=ft.Column(
                                            spacing=5,
                                            controls=[
                                                ft.Text("Presión", 
                                                       size=14, weight=ft.FontWeight.BOLD),
                                                self.txt_pres
                                            ]
                                        )
                                    ),
                                    
                                    # Información
                                    ft.Container(
                                        padding=10,
                                        bgcolor=ft.Colors.BLUE_100,
                                        border_radius=10,
                                        content=ft.Column(
                                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                                            spacing=5,
                                            controls=[
                                                ft.Icon(ft.Icons.UPDATE, 
                                                       size=24, color=ft.Colors.BLUE_700),
                                                ft.Text("Actualización automática", 
                                                       size=12, weight=ft.FontWeight.W_500),
                                                ft.Text("Cada 2 segundos", 
                                                       size=10, color=ft.Colors.GREY_600)
                                            ]
                                        )
                                    )
                                ]
                            )
                        ),
                        
                        # Panel derecho - Historial
                        ft.Container(
                            expand=True,
                            padding=20,
                            bgcolor=ft.Colors.WHITE,
                            border_radius=10,
                            content=ft.Column(
                                expand=True,
                                spacing=10,
                                controls=[
                                    ft.Row(
                                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                                        controls=[
                                            ft.Text("Historial de Registros", 
                                                   size=18, weight=ft.FontWeight.BOLD),
                                            self.contador,
                                            ft.Row(
                                                spacing=10,
                                                controls=[self.btn_registro, self.btn_limpiar]
                                            )
                                        ]
                                    ),
                                    
                                    ft.Divider(height=1, color=ft.Colors.GREY_300),
                                    
                                    # Área de historial
                                    ft.Container(
                                        expand=True,
                                        border=ft.border.all(1, ft.Colors.GREY_300),
                                        border_radius=10,
                                        padding=10,
                                        content=self.lista_historial
                                    ),
                                    
                                    # Leyenda
                                    ft.Container(
                                        padding=10,
                                        content=ft.Row(
                                            spacing=15,
                                            alignment=ft.MainAxisAlignment.CENTER,
                                            controls=[
                                                ft.Row([
                                                    ft.Container(width=12, height=12, 
                                                               bgcolor=ft.Colors.BLUE_50, 
                                                               border_radius=6),
                                                    ft.Text("Automático", size=10),
                                                ]),
                                                ft.Row([
                                                    ft.Container(width=12, height=12, 
                                                               bgcolor=ft.Colors.GREEN_50, 
                                                               border_radius=6),
                                                    ft.Text("Manual", size=10),
                                                ]),
                                            ]
                                        )
                                    )
                                ]
                            )
                        )
                    ]
                )
            ]
        )
    def registrar_manual(self, e):
        """Usa el callback si existe, sino versión local"""
        if self.on_registro_manual:
            self.on_registro_manual(e)
        # else:
        #     # Versión local de respaldo
        #     self.registrar_manual_local(e)

    # def registrar_manual(self, e):
        # """Registra datos manualmente"""
        #  # Activar la bandera para indicar que se presionó el botón
        # self.bandera_btn_registro = True
        # print("✓ Botón de registro manual presionado - Bandera activada")
        # try:
        #     # Obtener valores
        #     temp_val = self.txt_temp.value
        #     hum_val = self.txt_hum.value
        #     pres_val = self.txt_pres.value
            
        #     # Convertir a números
        #     temp = float(temp_val.replace("°C", "").replace("--", "0").strip())
        #     hum = float(hum_val.replace("%", "").replace("--", "0").strip())
        #     pres = float(pres_val.replace("Pa", "").replace("--", "0").strip())
            
        #     # Agregar registro al historial local (ahora en el mismo formato)
        #     registro = self.historial.agregar_registro(temp, hum, pres, tipo="registro_manual", fuente="UMA (Manual)")
            
        #     # También agregar al RelojGlobal (mismo formato)
        #     if self.reloj_global:
        #         datos = {
        #             'temperatura': temp,
        #             'humedad': hum,
        #             'presion1': pres,
        #             'presion2': pres,  # Mismo valor para consistencia
        #             'presion3': pres   # Mismo valor para consistencia
        #         }
        #         self.reloj_global.agregar_al_historial(
        #             datos, 
        #             tipo="registro_manual", 
        #             fuente="UMA (Manual)"
        #         )
            
        #     # Actualizar lista
        #     self.actualizar_lista()
            
        #     # Mostrar mensaje
        #     self.mostrar_notificacion(f"✓ Registro #{registro['id']} agregado", ft.Colors.GREEN)

        #     # Devolver la bandera para que la UI principal la vea
        #     return True
            
        # except Exception as ex:
        #     print(f"Error registrando: {ex}")
        #     self.mostrar_notificacion("Error al registrar", ft.Colors.RED)
        #     return False
        # pass
    
    def limpiar_todo(self, e):
        """Limpia todo el historial"""
        # Limpiar el historial local
        self.historial.eliminar_todos_registros()
        
        # También limpiar el historial del RelojGlobal
        if self.reloj_global:
            self.reloj_global.limpiar_historial()
        
        # Actualizar la lista
        self.actualizar_lista()
        
        # Mostrar mensaje
        self.mostrar_notificacion("✓ Historial completamente limpiado", ft.Colors.GREEN)
        
    
    def mostrar_notificacion(self, mensaje, color):
        """Muestra una notificación"""
        if self.page:
            snackbar = ft.SnackBar(
                content=ft.Text(mensaje, color=ft.Colors.WHITE),
                bgcolor=color,
                duration=2000
            )
            self.page.snack_bar = snackbar
            snackbar.open = True
            self.page.update()
    
    def actualizar_lista(self):
        """Actualiza la lista de historial - Lee datos desde la clave 'datos'"""
        try:
            # Limpiar lista
            self.lista_historial.controls.clear()
            
            # Obtener registros actualizados
            registros = self.historial.obtener_registros()
            
            # Actualizar contador
            total = len(registros)
            self.contador.value = f"{total} registros"
            
            # Ordenar por ID (más recientes primero)
            registros.sort(key=lambda x: x.get("id", 0), reverse=True)
            
            # Mostrar últimos 15 registros
            for registro in registros[:15]:
                # OBTENER DATOS DESDE LA CLAVE 'datos'
                datos = registro.get("datos", {})
                temp = datos.get("temperatura", "N/A")
                hum = datos.get("humedad", "N/A")
                pres = datos.get("presion1", "N/A")  # presion1, no presion
                
                tipo = registro.get("tipo", "desconocido")
                fuente = registro.get("fuente", "Sistema")
                
                # Determinar color según tipo
                if tipo in ["registro_automatico", "automatico"]:
                    bgcolor = ft.Colors.BLUE_50
                    icono = "🔄"
                elif tipo == "registro_manual":
                    bgcolor = ft.Colors.GREEN_50
                    icono = "👆"
                else:
                    bgcolor = ft.Colors.GREY_50
                    icono = "❓"
                
                # Formatear valores
                temp_str = f"{temp}°C" if temp != "N/A" else "N/A°C"
                hum_str = f"{hum}%" if hum != "N/A" else "N/A%"
                pres_str = f"{pres}Pa" if pres != "N/A" else "N/APa"
                
                # Crear tarjeta
                card = ft.Container(
                    padding=10,
                    margin=ft.margin.only(bottom=5),
                    bgcolor=bgcolor,
                    border_radius=8,
                    border=ft.border.all(1, ft.Colors.GREY_200),
                    content=ft.Column(
                        spacing=5,
                        controls=[
                            # Fila 1: ID, Fecha/Hora, Tipo
                            ft.Row(
                                controls=[
                                    ft.Text(f"#{registro.get('id', 'N/A')}", 
                                        size=12, weight=ft.FontWeight.BOLD),
                                    ft.Text(f"{registro.get('fecha', '')} {registro.get('hora', '')}",
                                        size=11, color=ft.Colors.GREY_600),
                                    ft.Container(expand=True),
                                    ft.Text(f"{icono} {fuente}", 
                                        size=11, color=ft.Colors.GREY_600)
                                ]
                            ),
                            # Fila 2: Valores
                            ft.Row(
                                spacing=20,
                                controls=[
                                    ft.Text(temp_str, 
                                        size=12, weight=ft.FontWeight.W_500),
                                    ft.Text(hum_str, 
                                        size=12, weight=ft.FontWeight.W_500),
                                    ft.Text(pres_str, 
                                        size=12, weight=ft.FontWeight.W_500),
                                ]
                            )
                        ]
                    )
                )
                
                self.lista_historial.controls.append(card)
            
            # Si no hay registros, mostrar mensaje
            if total == 0:
                self.lista_historial.controls.append(
                    ft.Container(
                        height=100,
                        alignment=ft.alignment.center,
                        content=ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=10,
                            controls=[
                                ft.Icon(ft.Icons.HISTORY, size=40, color=ft.Colors.GREY_400),
                                ft.Text("No hay registros aún", 
                                    size=14, color=ft.Colors.GREY_500),
                                ft.Text("Haz clic en 'Registrar' para agregar uno", 
                                    size=12, color=ft.Colors.GREY_400)
                            ]
                        )
                    )
                )
            
            # Actualizar UI
            if self.page:
                try:
                    self.lista_historial.update()
                    self.contador.update()
                except:
                    pass  # Ignorar errores de actualización
                    
        except Exception as ex:
            print(f"Error en actualizar_lista: {ex}")