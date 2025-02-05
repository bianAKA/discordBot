# discordBot
A discordBot that can write bullet points in a google doc by using python and mongodb

async def monitorExpired():
when the bot is running, we check if the user session ends or not.

/login: authorise discord bot to have the permission to access
- mongodb allows a discord user to have multiple email addresses authroised
- mongodb avoids the multiple of token json files

/activate: let bot focuses on one google account
- it checks if the email address is authorized or not
- it checks if user already has 'activated' email or not. If user doesn't have then we will activate it

/end: let the bot stops focusing on that google acount
- it checks if the email address is authorized or not
- it checks that email address is deactivated or not. If it is activated, we will turn into deactivated

/create_file: create a file, can put in a specific directory

limitations: 
1) (https://developers.google.com/docs/api/quickstart/python), the account needs to be added as a test user while configure the OAuth consent screen, otherwise it blocks the account.
2) the URL for authorizing is opened locally
