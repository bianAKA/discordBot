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
        self.password = None
    
    @commands.Cog.listener()
    async def on_ready(self):
        print("commands ready")
    
    @app_commands.command(name="testing", description="see if bot is working")
    async def hi(self, interaction: discord.Interaction):
        await interaction.response.send_message(f"Hi, {interaction.user.mention}")

    @app_commands.command(name="password", description="authorize the program to access the google drive")
    async def password(self, interaction: discord.Interaction, message: str):
        self.password = message
        await interaction.response.send_message(f"Thanks, we got it!")
        
        self.creds = self.flow.fetch_token(code=self.password)
        with open("token.json", "w") as token:
            token.write(self.creds.to_json())

    @app_commands.command(name="login", description="get token of google account")
    async def getCreds(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        if os.path.exists("token.json"):
            self.creds = Credentials.from_authorized_user_file("token.json", SCOPES)
         
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                self.flow = InstalledAppFlow.from_client_secrets_file(
                    "./credentials.json", SCOPES,
                    redirect_uri='urn:ietf:wg:oauth:2.0:oob' 
                )

                auth_url = flow.authorization_url()
                
                await interaction.response.send_message(f"Hi, please go to this link: {auth_url[0]}, and give us the password by using slash command password", ephemeral=True)
                return
        
async def setup(bot):
    await bot.add_cog(Write(bot))