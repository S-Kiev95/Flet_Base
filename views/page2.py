import flet as ft
import asyncio


class Page2:
    """Segunda página - Items"""
    
    def __init__(self, state, api, page):
        self.state = state
        self.api = api
        self.page = page
        self.items_list = ft.Column()
        self.loading = ft.ProgressRing(visible=False)
        self.counter = ft.Text("Contador: 0", size=20)
        self.container = None
    
    def build(self):
        self.state.subscribe("items", self._on_items_changed)
        self.state.subscribe("loading", self._on_loading_changed)
        self.state.subscribe("counter", self._on_counter_changed)
        
        self.container = ft.Container(
            content=ft.Column([
                ft.Text("Página 2 - Items", size=24, weight=ft.FontWeight.BOLD),
                ft.Row([
                    ft.ElevatedButton(
                        "Cargar Items",
                        icon=ft.Icons.DOWNLOAD,
                        on_click=self._load_items
                    ),
                    ft.ElevatedButton(
                        "Incrementar Contador",
                        icon=ft.Icons.ADD,
                        on_click=self._increment_counter
                    ),
                ]),
                self.counter,
                self.loading,
                ft.Divider(),
                self.items_list,
            ]),
            padding=20,
        )
        
        return self.container
    
    def _load_items(self, e):
        asyncio.create_task(self.api.load_items())
    
    def _increment_counter(self, e):
        current = self.state.get("counter", 0)
        self.state.set("counter", current + 1)
    
    def _on_items_changed(self, items):
        self.items_list.controls.clear()
        
        if items:
            for item in items:
                self.items_list.controls.append(
                    ft.Card(
                        content=ft.Container(
                            content=ft.ListTile(
                                leading=ft.Icon(ft.Icons.SHOPPING_BAG),
                                title=ft.Text(item["title"]),
                                subtitle=ft.Text(f"Cantidad: {item['count']}"),
                            ),
                            padding=10,
                        )
                    )
                )
        
        self.page.update()
    
    def _on_loading_changed(self, loading):
        self.loading.visible = loading
        self.page.update()
    
    def _on_counter_changed(self, value):
        self.counter.value = f"Contador: {value}"
        self.page.update()
