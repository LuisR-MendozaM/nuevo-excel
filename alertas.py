import flet as ft
import json
import os
import datetime
import threading
import time

class SistemaAlertas:
    def __init__(self, archivo="alertas.json"):
        self.archivo = archivo
        self.alertas = []
        self.proximo_id = 1
        self.cargar_alertas()
        self.ultima_modificacion = time.time()
        
    def cargar_alertas(self):
        """Carga las alertas desde archivo JSON"""
        if os.path.exists(self.archivo):
            try:
                with open(self.archivo, "r", encoding='utf-8') as f:
                    self.alertas = json.load(f)
                
                if self.alertas:
                    max_id = max(alerta.get("id", 0) for alerta in self.alertas)
                    self.proximo_id = max_id + 1
                else:
                    self.proximo_id = 1
                    
                print(f"SistemaAlertas: {len(self.alertas)} alertas cargadas, próximo ID: {self.proximo_id}")
            except Exception as e:
                print(f"SistemaAlertas: Error cargando alertas: {e}")
                self.alertas = []
                self.proximo_id = 1
        return self.alertas
    
    def guardar_alertas(self):
        """Guarda las alertas en archivo JSON"""
        try:
            with open(self.archivo, "w", encoding='utf-8') as f:
                json.dump(self.alertas, f, ensure_ascii=False, indent=4)
            self.ultima_modificacion = time.time()
        except Exception as e:
            print(f"SistemaAlertas: Error guardando alertas: {e}")
    
    def agregar_alerta(self, causa, pagina, elemento=None, valor=None, tipo=None):
        """Agrega una nueva alerta con información detallada"""
        ahora = datetime.datetime.now()
        fecha = ahora.strftime("%Y-%m-%d")
        hora = ahora.strftime("%H:%M")
        
        alerta = {
            "id": self.proximo_id,
            "causa": causa,
            "pagina": pagina,
            "elemento": elemento if elemento else "General",
            "valor": str(valor) if valor is not None else "N/A",
            "tipo": tipo if tipo else "advertencia",
            "fecha": fecha,
            "hora": hora,
            "fecha_hora_completa": ahora.isoformat()
        }
        self.alertas.append(alerta)
        self.proximo_id += 1
        self.guardar_alertas()
        
        # Log detallado
        elemento_info = f" [{elemento}]" if elemento else ""
        valor_info = f" (Valor: {valor})" if valor else ""
        print(f"Alerta #{alerta['id']} agregada: {pagina}{elemento_info} - {causa}{valor_info}")
        return alerta
    
    def eliminar_alerta(self, id_alerta):
        """Elimina una alerta por su ID"""
        for i, alerta in enumerate(self.alertas):
            if alerta["id"] == id_alerta:
                self.alertas.pop(i)
                self.guardar_alertas()
                print(f"Alerta {id_alerta} eliminada")
                return True
        return False
    
    def eliminar_todas_alertas(self):
        """Elimina todas las alertas"""
        self.alertas.clear()
        self.proximo_id = 1
        self.guardar_alertas()
        print("Todas las alertas eliminadas, IDs reiniciados")
    
    def obtener_alertas(self, filtro_pagina=None, filtro_elemento=None):
        """Obtiene todas las alertas, opcionalmente filtradas por página y elemento"""
        alertas_filtradas = self.alertas.copy()
        
        if filtro_pagina:
            alertas_filtradas = [a for a in alertas_filtradas if a["pagina"] == filtro_pagina]
        
        if filtro_elemento:
            alertas_filtradas = [a for a in alertas_filtradas if a["elemento"] == filtro_elemento]
        
        return alertas_filtradas
    
    def contar_alertas(self, filtro_pagina=None, filtro_elemento=None):
        """Cuenta el total de alertas, opcionalmente filtradas"""
        if filtro_pagina or filtro_elemento:
            return len(self.obtener_alertas(filtro_pagina, filtro_elemento))
        return len(self.alertas)
    
    def obtener_timestamp_modificacion(self):
        """Obtiene el timestamp de última modificación"""
        return self.ultima_modificacion
    
    def obtener_max_id(self):
        """Obtiene el ID máximo actual"""
        if not self.alertas:
            return 0
        return max(alerta.get("id", 0) for alerta in self.alertas)
    
    def obtener_elementos_unicos(self):
        """Obtiene una lista de elementos únicos que han generado alertas"""
        elementos = set()
        for alerta in self.alertas:
            if alerta.get("elemento") and alerta["elemento"] != "General":
                elementos.add(alerta["elemento"])
        return sorted(list(elementos))

# ---------- UI MEJORADA ----------
class AlertasView(ft.Container):
    def __init__(self, sistema_alertas=None, page=None):
        super().__init__()
        self.sistema = sistema_alertas or SistemaAlertas()
        self.page = page
        self.filtro_actual = None
        self.filtro_elemento_actual = None
        self.ultimo_timestamp = self.sistema.obtener_timestamp_modificacion()
        self.en_pagina = False
        self.ui_inicializada = False
        
        # Componentes UI
        self.punto_estado = ft.Container(
            width=10,
            height=10,
            bgcolor=ft.Colors.GREEN_200,
            border_radius=5,
            opacity=0.5
        )

        self.contador = ft.Text("0 alertas", size=14, color=ft.Colors.GREY_700)

        self.lista_alertas = ft.ListView(
            expand=True,
            spacing=5,
            padding=10,
            auto_scroll=False
        )
        
        # Construir UI
        self.build_ui()
    
    def build_ui(self):
        """Construye la interfaz de usuario"""
        # Panel de control superior con filtros
        panel_superior = ft.Container(
            padding=15,
            bgcolor=ft.Colors.BLUE_50,
            border_radius=10,
            content=ft.Column([
                # Fila 1: Título y contador
                ft.Row([
                    ft.Text("Sistema de Alertas", size=20, weight=ft.FontWeight.BOLD),
                    ft.Container(expand=True),
                    ft.Row([
                        self.punto_estado,
                        self.contador,
                    ], spacing=5)
                ]),
                
                # Fila 2: Filtros por página
                ft.Text("Filtrar por Página:", size=12, color=ft.Colors.GREY_700),
                ft.Row([
                    ft.ElevatedButton(
                        "Todas",
                        icon=ft.Icons.LIST,
                        on_click=self.aplicar_filtro_todas,
                        bgcolor=ft.Colors.BLUE_200
                    ),
                    ft.ElevatedButton(
                        "UMA",
                        icon=ft.Icons.HOME,
                        on_click=lambda e: self.aplicar_filtro_pagina("UMA"),
                        bgcolor=ft.Colors.GREEN_200
                    ),
                    ft.ElevatedButton(
                        "Manómetros",
                        icon=ft.Icons.SPEED,
                        on_click=lambda e: self.aplicar_filtro_pagina("Manómetros"),
                        bgcolor=ft.Colors.ORANGE_200
                    ),
                    ft.ElevatedButton(
                        "Reloj Global",
                        icon=ft.Icons.ACCESS_TIME,
                        on_click=lambda e: self.aplicar_filtro_pagina("Reloj Global"),
                        bgcolor=ft.Colors.PURPLE_200
                    ),
                ], spacing=10),
                
                # Fila 3: Botones de acción
                ft.Row([
                    ft.Container(expand=True),
                    ft.ElevatedButton(
                        "Limpiar Todo",
                        icon=ft.Icons.DELETE_FOREVER,
                        on_click=self.eliminar_todo,
                        bgcolor=ft.Colors.RED_400,
                        color=ft.Colors.WHITE
                    ),
                ], spacing=10)
            ])
        )
        
        # ENCABEZADO DE TABLA MEJORADO
        self.encabezado_tabla = ft.Container(
            padding=10,
            bgcolor=ft.Colors.BLUE_100,
            border_radius=5,
            margin=ft.margin.only(bottom=5),
            content=ft.Row([
                # ID (5%)
                ft.Container(
                    width=50,
                    content=ft.Text("ID", 
                                   weight=ft.FontWeight.BOLD,
                                   color=ft.Colors.BLUE_800,
                                   size=12)
                ),
                # Elemento (15%)
                ft.Container(
                    width=100,
                    content=ft.Text("Elemento", 
                                   weight=ft.FontWeight.BOLD,
                                   color=ft.Colors.BLUE_800,
                                   size=12)
                ),
                # Causa (30%)
                ft.Container(
                    width=200,
                    content=ft.Text("Causa", 
                                   weight=ft.FontWeight.BOLD,
                                   color=ft.Colors.BLUE_800,
                                   size=12)
                ),
                # Valor (10%)
                ft.Container(
                    width=80,
                    content=ft.Text("Valor", 
                                   weight=ft.FontWeight.BOLD,
                                   color=ft.Colors.BLUE_800,
                                   size=12)
                ),
                # Página (10%)
                ft.Container(
                    width=100,
                    content=ft.Text("Página", 
                                   weight=ft.FontWeight.BOLD,
                                   color=ft.Colors.BLUE_800,
                                   size=12)
                ),
                # Fecha (10%)
                ft.Container(
                    width=80,
                    content=ft.Text("Fecha", 
                                   weight=ft.FontWeight.BOLD,
                                   color=ft.Colors.BLUE_800,
                                   size=12)
                ),
                # Hora (10%)
                ft.Container(
                    width=60,
                    content=ft.Text("Hora", 
                                   weight=ft.FontWeight.BOLD,
                                   color=ft.Colors.BLUE_800,
                                   size=12)
                ),
                ft.Container(expand=True),
                # Acción (10%)
                ft.Container(
                    width=100,
                    content=ft.Text("Acción", 
                                   weight=ft.FontWeight.BOLD,
                                   color=ft.Colors.BLUE_800,
                                   size=12)
                ),
            ])
        )
        
        # Contenedor principal
        self.expand = True
        self.content = ft.Column(
            expand=True,
            controls=[
                panel_superior,
                ft.Divider(height=1),
                ft.Container(
                    expand=True,
                    padding=10,
                    content=ft.Column(
                        expand=True,
                        controls=[
                            self.encabezado_tabla,
                            ft.Container(
                                expand=True,
                                border=ft.border.all(1, ft.Colors.GREY_300),
                                border_radius=10,
                                padding=5,
                                content=self.lista_alertas
                            )
                        ]
                    )
                )
            ]
        )
    
    def entrar_a_pagina(self):
        """Se llama cuando entramos a la página de alertas"""
        self.en_pagina = True
        self.ui_inicializada = True
        print("Entrando a página de Alertas")
        
        # Cargar datos iniciales
        self.cargar_ui()
        
        # Iniciar verificación periódica
        self.iniciar_verificacion()
    
    def salir_de_pagina(self):
        """Se llama cuando salimos de la página de alertas"""
        self.en_pagina = False
        self.ui_inicializada = False
        print("Saliendo de página de Alertas")
    
    def iniciar_verificacion(self):
        """Inicia la verificación periódica de cambios"""
        def verificar():
            print("Iniciando verificación de cambios...")
            
            while self.en_pagina:
                try:
                    time.sleep(0.5)
                    
                    if not self.en_pagina:
                        break
                    
                    timestamp_actual = self.sistema.obtener_timestamp_modificacion()
                    
                    if timestamp_actual > self.ultimo_timestamp:
                        print(f"Cambio detectado! {self.ultimo_timestamp} -> {timestamp_actual}")
                        self.ultimo_timestamp = timestamp_actual
                        
                        # Animación del puntito
                        self.animar_puntito_seguro()
                        
                        # Actualizar UI
                        if self.page and self.ui_inicializada:
                            try:
                                self.page.run_thread(self.actualizar_inmediato_seguro)
                            except:
                                pass
                            
                except Exception as e:
                    print(f"Error en verificación: {e}")
                    time.sleep(1)
        
        threading.Thread(target=verificar, daemon=True).start()
    
    def animar_puntito_seguro(self):
        """Hace parpadear el puntito verde de forma segura"""
        try:
            if not self.ui_inicializada or not self.page:
                return
                
            def actualizar_ui():
                try:
                    self.punto_estado.opacity = 1
                    self.punto_estado.bgcolor = ft.Colors.GREEN_500
                    self.punto_estado.update()
                except Exception as e:
                    print(f"Error animando puntito: {e}")
            
            self.page.run_thread(actualizar_ui)

            def desvanecer():
                time.sleep(1)
                if self.ui_inicializada and self.page:
                    def desvanecer_ui():
                        try:
                            self.punto_estado.opacity = 0.5
                            self.punto_estado.update()
                        except Exception as e:
                            print(f"Error desvaneciendo puntito: {e}")
                    self.page.run_thread(desvanecer_ui)
            
            threading.Thread(target=desvanecer, daemon=True).start()
        except Exception as e:
            print(f"Error en animar_puntito_seguro: {e}")
    
    def actualizar_inmediato_seguro(self):
        """Actualiza la UI inmediatamente de forma segura"""
        try:
            self.cargar_ui()
        except Exception as e:
            print(f"Error al actualizar: {e}")
    
    def cargar_ui(self, e=None):
        """Carga las alertas en la interfaz"""
        try:
            # Obtener alertas filtradas
            alertas = self.sistema.obtener_alertas(self.filtro_actual, self.filtro_elemento_actual)
            alertas.sort(key=lambda x: x.get("id", 0), reverse=True)
            
            # Limpiar y recrear la lista
            nuevos_controles = []
            for alerta in alertas:
                nuevos_controles.append(self._crear_fila_alerta(alerta))
            
            self.lista_alertas.controls = nuevos_controles
            
            # Actualizar contador
            self.actualizar_contador_seguro()
            
            # Actualizar UI
            if self.ui_inicializada:
                try:
                    self.update()
                except:
                    pass
            
        except Exception as ex:
            print(f"Error al cargar UI: {ex}")
    
    def _crear_fila_alerta(self, alerta):
        """Crea una fila de datos de alerta con información detallada"""
        causa = alerta.get("causa", "Sin causa")
        pagina = alerta.get("pagina", "Desconocida")
        elemento = alerta.get("elemento", "General")
        valor = alerta.get("valor", "N/A")
        alerta_id = alerta.get("id", "N/A")
        
        # Obtener fecha y hora
        fecha = alerta.get("fecha", "Fecha desconocida")
        hora = alerta.get("hora", "Hora desconocida")
        
        # Formatear fecha como DD/MM/YY
        try:
            fecha_dt = datetime.datetime.strptime(fecha, "%Y-%m-%d")
            fecha_formateada = fecha_dt.strftime("%d/%m/%y")
        except:
            fecha_formateada = fecha
        
        # Determinar color según tipo y gravedad
        tipo = alerta.get("tipo", "advertencia")
        
        if tipo == "critica":
            bgcolor = ft.Colors.RED_50
            color_borde = ft.Colors.RED_200
            color_icono = ft.Colors.RED_600
            icono = ft.Icons.ERROR_OUTLINE
        elif tipo == "advertencia":
            # Color según elemento
            if "Manómetro" in elemento:
                bgcolor = ft.Colors.ORANGE_50
                color_icono = ft.Colors.ORANGE_600
            elif elemento in ["Termómetro", "Hidrómetro"]:
                bgcolor = ft.Colors.BLUE_50
                color_icono = ft.Colors.BLUE_600
            else:
                bgcolor = ft.Colors.YELLOW_50
                color_icono = ft.Colors.YELLOW_600
            color_borde = ft.Colors.GREY_300
            icono = ft.Icons.WARNING_AMBER
        else:
            bgcolor = ft.Colors.GREY_50
            color_borde = ft.Colors.GREY_300
            color_icono = ft.Colors.GREY_600
            icono = ft.Icons.INFO
        
        # Crear botón de eliminar
        def eliminar_click(e, id=alerta_id):
            if self.eliminar_alerta(id):
                self.cargar_ui()
        
        btn_eliminar = ft.ElevatedButton(
            "Eliminar",
            icon=ft.Icons.DELETE_OUTLINED,
            on_click=eliminar_click,
            bgcolor=ft.Colors.RED_400,
            color=ft.Colors.WHITE,
            height=35,
            width=90
        )
        
        # Crear fila con los datos
        fila = ft.Row([
            # Columna ID - 50px
            ft.Container(
                width=50,
                padding=10,
                content=ft.Text(
                    f"#{alerta_id}",
                    size=12,
                    color=ft.Colors.GREY_800,
                    weight=ft.FontWeight.BOLD
                )
            ),
            
            # Columna Elemento - 100px (con icono)
            ft.Container(
                width=100,
                padding=10,
                content=ft.Row([
                    ft.Icon(icono, color=color_icono, size=14),
                    ft.Text(
                        elemento,
                        size=12,
                        color=ft.Colors.GREY_800
                    )
                ], spacing=5, vertical_alignment=ft.CrossAxisAlignment.CENTER)
            ),
            
            # Columna Causa - 200px
            ft.Container(
                width=200,
                padding=10,
                content=ft.Text(
                    causa,
                    size=12,
                    color=ft.Colors.GREY_800
                )
            ),
            
            # Columna Valor - 80px
            ft.Container(
                width=80,
                padding=10,
                content=ft.Text(
                    valor,
                    size=12,
                    color=ft.Colors.GREY_700
                )
            ),
            
            # Columna Página - 100px
            ft.Container(
                width=100,
                padding=10,
                content=ft.Text(
                    pagina,
                    size=12,
                    color=ft.Colors.GREY_700
                )
            ),
            
            # Columna Fecha - 80px
            ft.Container(
                width=80,
                padding=10,
                content=ft.Text(
                    fecha_formateada,
                    size=12,
                    color=ft.Colors.GREY_700
                )
            ),
            
            # Columna Hora - 60px
            ft.Container(
                width=60,
                padding=10,
                content=ft.Text(
                    hora,
                    size=12,
                    color=ft.Colors.GREY_700
                )
            ),
            
            ft.Container(expand=True),
            
            # Columna Acción - 100px
            ft.Container(
                width=100,
                padding=10,
                content=btn_eliminar
            )
        ], spacing=0, vertical_alignment=ft.CrossAxisAlignment.CENTER)
        
        return ft.Container(
            bgcolor=bgcolor,
            border_radius=5,
            border=ft.border.all(1, color_borde),
            margin=ft.margin.only(bottom=3),
            content=fila
        )
    
    def aplicar_filtro_pagina(self, pagina):
        """Aplica un filtro por página"""
        self.filtro_actual = pagina
        self.filtro_elemento_actual = None
        self.cargar_ui()
        print(f"Filtro aplicado: Página = {pagina}")
    
    def aplicar_filtro_todas(self, e):
        """Aplica filtro para mostrar todas las alertas"""
        self.filtro_actual = None
        self.filtro_elemento_actual = None
        self.cargar_ui()
        print("Filtro aplicado: Todas las alertas")
    
    def eliminar_alerta(self, id_alerta):
        """Elimina una alerta específica"""
        try:
            if isinstance(id_alerta, str):
                if '#' in id_alerta:
                    id_str = id_alerta.split('#')[1]
                    id_alerta = int(id_str) if id_str.isdigit() else 0
                else:
                    id_alerta = int(id_alerta) if id_alerta.isdigit() else 0
            
            if self.sistema.eliminar_alerta(id_alerta):
                print(f"Alerta #{id_alerta} eliminada")
                return True
            else:
                print(f"No se encontró alerta #{id_alerta}")
                return False
                
        except Exception as ex:
            print(f"Error al eliminar alerta: {ex}")
            return False
    
    def eliminar_todo(self, e):
        """Elimina todas las alertas"""
        print("Eliminando todas las alertas...")
        
        if self.sistema.contar_alertas() == 0:
            print("No hay alertas para eliminar")
            return
        
        self.sistema.eliminar_todas_alertas()
        print("Todas las alertas eliminadas")
        self.cargar_ui()
    
    def actualizar_contador_seguro(self):
        """Actualiza el contador de alertas de forma segura"""
        try:
            total = self.sistema.contar_alertas()
            filtradas = self.sistema.contar_alertas(self.filtro_actual, self.filtro_elemento_actual)
            
            if self.filtro_actual or self.filtro_elemento_actual:
                self.contador.value = f"{filtradas} de {total} alertas"
            else:
                self.contador.value = f"{total} alertas"
            
            # Actualizar estado del punto
            if self.ui_inicializada:
                try:
                    if total > 0:
                        self.punto_estado.bgcolor = ft.Colors.GREEN_500
                        self.punto_estado.opacity = 1
                    else:
                        self.punto_estado.bgcolor = ft.Colors.GREEN_200
                        self.punto_estado.opacity = 0.5
                except Exception as e:
                    print(f"Error actualizando punto: {e}")
        except Exception as e:
            print(f"Error actualizando contador: {e}")

# Función de compatibilidad
def agregar_alerta(causa, pagina, elemento=None, valor=None, tipo=None):
    """Función de compatibilidad para agregar alertas"""
    sistema = SistemaAlertas()
    return sistema.agregar_alerta(causa, pagina, elemento, valor, tipo)