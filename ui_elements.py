import discord
from discord.ui import Button, View
from typing import List
import time
from datetime import timedelta

class CustomView(View):
    def __init__(self, items):
        super().__init__()
        self.selected_item = None  # To store the selected item generically
        for item in items:
            self.add_item(CustomButton(item))


class CustomButton(Button):
    def __init__(self, item):
        label = item.name if hasattr(item, 'name') else str(item)  # Fallback to str if no name attribute
        super().__init__(label=label, style=discord.ButtonStyle.primary)
        self.item = item

    async def callback(self, interaction):
        self.view.selected_item = self.item  # Set the selected item generically
        for item in self.view.children:
            item.disabled = True
        await interaction.response.edit_message(view=self.view)
        self.view.stop()  # Important to stop the view from waiting


class ItemButton(Button):
    def __init__(self, label: str, *args, **kwargs):
        super().__init__(label=label, style=discord.ButtonStyle.primary, *args, **kwargs)

    async def callback(self, interaction: discord.Interaction):
        view: PaginatedButtonsView = self.view
        view.selected_item = self.label
        for item in view.children:
            item.disabled = True
        await interaction.response.edit_message(view=view)
        view.stop()


class NavigationButton(Button):
    def __init__(self, label: str, page_change: int, *args, **kwargs):
        super().__init__(label=label, style=discord.ButtonStyle.secondary, *args, **kwargs)
        self.page_change = page_change

    async def callback(self, interaction: discord.Interaction):
        view: PaginatedButtonsView = self.view
        view.current_page += self.page_change
        view.update_buttons()
        await interaction.response.edit_message(view=view)


class PaginatedButtonsView(View):
    def __init__(self, items: List[str], *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.items = items
        self.current_page = 0
        self.max_items_per_page = 20  # Updated to show 20 buttons per page
        self.total_pages = (len(items) - 1) // self.max_items_per_page + 1
        self.selected_item = None
        self.update_buttons()

    def get_items_for_current_page(self):
        start_index = self.current_page * self.max_items_per_page
        end_index = start_index + self.max_items_per_page
        return self.items[start_index:end_index]

    def update_buttons(self):
        self.clear_items()
        for item in self.get_items_for_current_page():
            self.add_item(ItemButton(label=item))

        # Add navigation buttons with callbacks for pagination
        if self.current_page > 0:
            self.add_item(NavigationButton(label="<<", page_change=-1))
        if self.current_page < self.total_pages - 1:
            self.add_item(NavigationButton(label=">>", page_change=1))


