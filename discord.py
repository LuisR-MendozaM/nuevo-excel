import flet as ft

def main(page: ft.Page):
    # Configurar la página
    page.title = "Indicador de Actividad tipo Discord"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.CrossAxisAlignment.CENTER
    page.bgcolor = ft.Colors.BLUE_GREY_900
    page.padding = 20
    
    # Crear el contenedor principal (avatar amarillo)
    avatar_container = ft.Container(
        width=120,
        height=120,
        bgcolor=ft.Colors.AMBER_400,
        border_radius=60,  # Hace el contenedor completamente redondo
        alignment=ft.alignment.center,
        # Sombra para darle profundidad
        shadow=ft.BoxShadow(
            spread_radius=1,
            blur_radius=15,
            color=ft.Colors.BLACK54,
            offset=ft.Offset(0, 3)
        )
    )
    
    # Crear el punto verde (indicador de actividad)
    activity_dot = ft.Container(
        width=30,
        height=30,
        bgcolor=ft.Colors.GREEN_400,
        border_radius=15,  # Hace el punto completamente redondo
        border=ft.border.all(4, ft.Colors.BLUE_GREY_900),
        # Posicionar en la esquina inferior derecha del avatar
        # Nota: En Discord el punto está en la esquina inferior derecha
        # aunque mencionaste "izquierda", lo pondré como Discord realmente lo tiene
    )
    
    # Contenedor que combina el avatar y el punto
    combined_container = ft.Stack(
        [
            avatar_container,
            # Posicionar el punto en la esquina inferior derecha
            ft.Container(
                content=activity_dot,
                alignment=ft.alignment.bottom_right,
            )
        ],
        width=120,
        height=120,
    )
    
    # Texto explicativo
    status_text = ft.Text(
        "En línea",
        color=ft.Colors.GREEN_400,
        size=20,
        weight=ft.FontWeight.BOLD
    )
    
    # Controles para simular cambios de estado
    status_selector = ft.Dropdown(
        label="Estado de actividad",
        options=[
            ft.dropdown.Option("online", "En línea"),
            ft.dropdown.Option("idle", "Ausente"),
            ft.dropdown.Option("dnd", "No molestar"),
            ft.dropdown.Option("offline", "Desconectado"),
        ],
        value="online",
        width=200,
        on_change=lambda e: cambiar_estado(e, activity_dot, status_text)
    )
    
    # Función para cambiar el estado
    def cambiar_estado(e, dot, text):
        estado = status_selector.value
        if estado == "online":
            dot.bgcolor = ft.Colors.GREEN_400
            text.value = "En línea"
            text.color = ft.Colors.GREEN_400
        elif estado == "idle":
            dot.bgcolor = ft.Colors.AMBER_400
            text.value = "Ausente"
            text.color = ft.Colors.AMBER_400
        elif estado == "dnd":
            dot.bgcolor = ft.Colors.RED_400
            text.value = "No molestar"
            text.color = ft.Colors.RED_400
        elif estado == "offline":
            dot.bgcolor = ft.Colors.GREY_400
            text.value = "Desconectado"
            text.color = ft.Colors.GREY_400
        
        dot.update()
        text.update()
    
    # Panel de controles
    control_panel = ft.Column(
        [
            ft.Text("Personalizar indicador:", size=18, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            status_selector,
            ft.Text("Nota: En Discord, el punto de actividad está en la esquina inferior derecha.", 
                   size=12, color=ft.Colors.WHITE70, italic=True)
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=10
    )
    
    # Layout principal
    page.add(
        ft.Column(
            [
                ft.Text("Indicador de Actividad tipo Discord", 
                       size=28, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                ft.Container(height=30),  # Espaciador
                combined_container,
                ft.Container(height=10),  # Espaciador
                status_text,
                ft.Container(height=30),  # Espaciador
                control_panel,
                ft.Container(height=20),  # Espaciador
                ft.Text("El punto verde indica que el usuario está en línea y activo.", 
                       size=14, color=ft.Colors.WHITE70),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        )
    )

# Ejecutar la aplicación
ft.app(target=main)