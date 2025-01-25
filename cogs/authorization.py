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
        self.creds = None
        self.flow = None

    @commands.Cog.listener()
    async def on_ready(self):
        print("commands ready")

    def writingToken(self):
        with open("token.json", "w") as token:
            token.write(self.creds.to_json())

    @app_commands.command(name="login", description="get token of google account")
    async def getCreds(self, interaction: discord.Interaction):
        if os.path.exists("token.json"):
            await interaction.response.send_message(f"Hi, {interaction.user.mention}, we already got your token", ephemeral=True)
            
            self.creds = Credentials.from_authorized_user_file("token.json", SCOPES) 
            return

        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else: 
                await interaction.response.defer(ephemeral=True)
                await interaction.followup.send(
                    f"Hi, {interaction.user.mention}, starting authentication process...",
                    ephemeral=True
                )

                self.flow = InstalledAppFlow.from_client_secrets_file(
                    "./credentials.json", SCOPES
                )

                self.creds = self.flow.run_local_server(port=0)
                
                await interaction.followup.send(
                    f"Authentication successful! Credentials saved. We got your token!!!!",
                    ephemeral=True
                )

            with open("token.json", "w") as token:
                token.write(self.creds.to_json())
                
async def setup(bot):
    await bot.add_cog(Write(bot))