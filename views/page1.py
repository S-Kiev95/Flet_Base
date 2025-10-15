import flet as ft
import asyncio


class Page1:
    """Primera página - Usuarios"""
    
    def __init__(self, state, api, page):
        self.state = state
        self.api = api
        self.page = page
        self.users_list = ft.Column()
        self.loading = ft.ProgressRing(visible=False)
        self.container = None
    
    def build(self):
        self.state.subscribe("users", self._on_users_changed)
        self.state.subscribe("loading", self._on_loading_changed)
        
        self.container = ft.Container(
            content=ft.Column([
                ft.Text("Página 1 - Usuarios", size=24, weight=ft.FontWeight.BOLD),
                ft.ElevatedButton(
                    "Cargar Usuarios",
                    icon=ft.Icons.REFRESH,
                    on_click=self._load_users
                ),
                self.loading,
                ft.Divider(),
                self.users_list,
            ]),
            padding=20,
        )
        
        return self.container
    
    def _load_users(self, e):
        asyncio.create_task(self.api.load_users())
    
    def _on_users_changed(self, users):
        self.users_list.controls.clear()
        
        if users:
            for user in users:
                self.users_list.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.ListTile(
                                leading=ft.Icon(ft.Icons.PERSON),
                                title=ft.Text(user["name"]),
                                subtitle=ft.Text(user.get("email", "")),
                            ),
                            padding=10,
                        )
                    )
                )
        
        self.page.update()
    
    def _on_loading_changed(self, loading):
        self.loading.visible = loading
        self.page.update()