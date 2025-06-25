import os
from dotenv import load_dotenv
from fyers_apiv3 import fyersModel

load_dotenv()

session = fyersModel.SessionModel(
    client_id=os.getenv("client_id"),
    secret_key=os.getenv("secret_key"),
    redirect_uri="https://trade.fyers.in/api-login/redirect-uri/index.html",
    response_type="code"
)

response = session.generate_authcode()
print(response)

