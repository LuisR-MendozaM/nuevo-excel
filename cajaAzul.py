import flet as ft
import time

class BlueBox(ft.Container):
    def __init__(
        self,
        texto_titulo: str,
        texto: str,
        on_click_fn=None,
        mostrar_boton=True,
        ancho=200,
        alto=200,
        # NUEVO: Parámetro para callback de página
        on_grafica_click=None
    ):
        
        self.texto_titulo = ft.Text(
            value=texto_titulo,
            size=20,
            weight=ft.FontWeight.BOLD,
            font_family="Arial"
        )
        
        # ==========================
        #   TEXTO PRINCIPAL (este es el que queremos actualizar)
        # ==========================
        self.texto_principal = ft.Text(
            value=texto,
            size=20,
            weight=ft.FontWeight.BOLD,
            font_family="Arial"
        )

        # ==========================
        #   ICONO DE CARGA / CHECK
        # ==========================
        self.textCheck = ft.Text(
            "",
            color=ft.Colors.WHITE,
            size=14,
            weight="w700",
            offset=ft.Offset(0, 0),
            animate_offset=ft.Animation(900, ft.AnimationCurve.DECELERATE),
            animate_opacity=200
        )

        # NUEVO: Guardar el callback de gráfica
        self.on_grafica_click = on_grafica_click

        # ==========================
        #       BOTÓN DE CONEXIÓN
        # ==========================
        self.btn_connect = ft.Container(
            width=150,
            height=50,
            bgcolor=ft.Colors.GREY,
            border_radius=0,
            alignment=ft.alignment.center,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            scale=ft.Scale(1),
            animate_opacity=ft.Animation(900, ft.AnimationCurve.DECELERATE),
            animate_scale=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
            animate=ft.Animation(200, ft.AnimationCurve.DECELERATE),
            on_hover=self.Check_On_Hover,
            # NUEVO: Usar el método modificado que maneja el callback
            on_click=self.Check_On_Click,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    self.textCheck,
                ]
            )
        )

        # ==========================
        #   CONTENIDO DEL BLUEBOX
        # ==========================
        controls = [
            self.texto_titulo,
            self.texto_principal,  # Usamos la referencia guardada
            self.btn_connect,
        ]

        if mostrar_boton and on_click_fn:
            controls.append(
                ft.ElevatedButton(
                    text="Acción",
                    on_click=on_click_fn
                )
            )

        super().__init__(
            bgcolor="yellow",
            border_radius=100,
            width=ancho,
            height=alto,
            alignment=ft.alignment.center,
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=controls
            )
        )

    # ============================================================
    #                    MÉTODOS REALES
    # ============================================================
    
    def actualizar_valor(self, nuevo_texto: str):
        """Actualiza el texto principal del BlueBox"""
        self.texto_principal.value = nuevo_texto
        # No llamamos a update() aquí, lo hará el componente padre

    def Check_On_Hover(self, e):
        # Cuando el mouse entra
        if e.data == "true":
            self.btn_connect.bgcolor = ft.Colors.GREEN_700
            self.textCheck.value = "Ver gráfica"
            self.btn_connect.border_radius = 50
            self.btn_connect.scale = ft.Scale(1.08)
        # Cuando el mouse sale
        else:
            self.btn_connect.bgcolor = ft.Colors.GREY
            self.textCheck.value = ""
            self.btn_connect.border_radius = 0
            self.btn_connect.scale = ft.Scale(1)

        self.btn_connect.update()
        self.textCheck.update()

    # def Check_On_Click(self, e):
    #     self.btn_connect.scale = ft.Scale(0.90)
    #     self.btn_connect.update()
    #     time.sleep(0.20)
    #     self.btn_connect.scale = ft.Scale(1)
    #     self.btn_connect.update()
    #     print("Botón de Check presionado")

     # NUEVO: Método modificado para manejar el callback
    def Check_On_Click(self, e):
        self.btn_connect.scale = ft.Scale(0.90)
        self.btn_connect.update()
        time.sleep(0.20)
        self.btn_connect.scale = ft.Scale(1)
        self.btn_connect.update()
        print(f"Botón de Check presionado - {self.texto_titulo.value}")
        
        # NUEVO: Llamar al callback si existe
        if self.on_grafica_click:
            self.on_grafica_click(self.texto_titulo.value)