import os
from dotenv import load_dotenv
from fyers_apiv3 import fyersModel
load_dotenv()
session = fyersModel.SessionModel(
    client_id=os.getenv("client_id"),
    secret_key=os.getenv("secret_key"), 
    redirect_uri="https://trade.fyers.in/api-login/redirect-uri/index.html",
    response_type="code", 
    grant_type="authorization_code")
session.set_token(os.getenv("auth_code"))
response = session.generate_token()
print(response)

