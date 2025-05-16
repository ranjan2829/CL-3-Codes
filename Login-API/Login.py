from fyers_apiv3 import fyersModel
client_id = "QGP6MO6UJQ-100"
secret_key = "2X22I3160A"
redirect_uri = "https://trade.fyers.in/api-login/redirect-uri/index.html"
response_type = "code"  
state = "sample_state"
session = fyersModel.SessionModel(
    client_id=client_id,
    secret_key=secret_key,
    redirect_uri=redirect_uri,
    response_type=response_type
)
response = session.generate_authcode()
print(response)

