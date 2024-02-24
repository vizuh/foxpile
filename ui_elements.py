import discord
from discord.ui import Button, View




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
