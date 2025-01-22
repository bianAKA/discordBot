import discord
from discord.ext import commands
from discord import app_commands
import os
import os.path

from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/drive"]

class Write(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("commands ready")
    
    @app_commands.command(name="testing", description="see if bot is working")
    async def hi(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Hi, {interaction.user.mention}")

async def setup(bot):
    await bot.add_cog(Write(bot))