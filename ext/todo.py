from typing import TypeVar, List, Iterator

import re
import discord
import discord.components
from discord import app_commands
from discord.ext import commands

T = TypeVar("T")


def iter_components(components: List[T]) -> Iterator[T]:
    for component in components:
        if isinstance(component, discord.Button):
            yield component
        elif isinstance(component, discord.ActionRow):
            yield from iter_components(component.children)  # type: ignore


class TodoEntry(discord.ui.Button["TodoListView"]):
    async def callback(self, interaction: discord.Interaction):
        view = TodoListView()
        view.clear_items()

        if not interaction.message:
            return
        for item in iter_components(interaction.message.components):
            if not isinstance(item, discord.Button):
                print(f"Got item {item}")
                continue
            style = item.style
            if item.custom_id == self.custom_id:
                if style == discord.ButtonStyle.green:
                    style = discord.ButtonStyle.red
                else:
                    style = discord.ButtonStyle.green
            view.add_item(
                TodoEntry(style=style, label=item.label, custom_id=item.custom_id)
            )
        await interaction.response.edit_message(view=view)


def subber(m):
    amt = int(m.group(0))
    if amt < 64:
        return str(amt)
    return f"({amt//64} stack{amt//64 > 1 and 's' or ''}" + (
        amt % 64 > 0 and f" + {amt % 64})" or ")"
    )


class TodoListView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        for i in range(25):
            self.add_item(TodoEntry(label="", custom_id=f"item-{i}"))

    def fill_labels(self, items: list[str]):
        self.clear_items()
        for i, item in enumerate(items):
            self.add_item(
                TodoEntry(
                    label=re.sub(r"\d+", subber, item)[:80],
                    style=discord.ButtonStyle.red,
                    custom_id=f"item-{i}",
                )
            )


class CreateTodoListView(discord.ui.Modal, title="New Todo List"):
    entries = discord.ui.TextInput(
        label="Todo list entries",
        style=discord.TextStyle.paragraph,
        placeholder="Max 80 characters each.\nSeparated by a new line.",
    )

    async def on_submit(self, interaction: discord.Interaction) -> None:
        entries = [l.strip()[:80] for l in self.entries.value.splitlines()]
        if not entries:
            return await interaction.response.send_message(
                "You did not provide any entries!", ephemeral=True
            )
        await interaction.response.send_message("Creating to-do list.", ephemeral=True)
        for entry in discord.utils.as_chunks(entries, max_size=25):
            view = TodoListView()
            view.fill_labels(entry)
            await interaction.channel.send(view=view)  # type: ignore


class ClickMe(discord.ui.View):
    def __init__(self, author: discord.abc.User):
        super().__init__(timeout=15)
        self.author = author
        self.message: discord.Message | None = None

    @discord.ui.button(label="click me")
    async def click_me(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        await interaction.response.send_modal(CreateTodoListView())
        await interaction.delete_original_response()

    async def on_timeout(self) -> None:
        if self.message:
            self.click_me.disabled = True
            self.click_me.label = "Prompt Timed Out"
            await self.message.edit(view=self)

    async def interaction_check(self, interaction: discord.Interaction, /):
        if interaction.user == self.author:
            return True
        await interaction.response.send_message(
            "that is not your button", ephemeral=True
        )


class TodoList(commands.Cog):
    @commands.hybrid_command(name="new-todo", aliases=["nt"])
    async def newTodoListView(self, ctx: commands.Context):
        """Creates a new to-do list"""
        if ctx.interaction:
            await ctx.interaction.response.send_modal(CreateTodoListView())
            try:
                await ctx.interaction.followup.send("", ephemeral=True)
            except:
                pass
        else:
            view = ClickMe(ctx.author)
            view.message = await ctx.send(ctx.author.mention, view=view)
            await ctx.message.delete()


async def setup(bot: commands.Bot):
    await bot.add_cog(TodoList())
    bot.add_view(TodoListView())
