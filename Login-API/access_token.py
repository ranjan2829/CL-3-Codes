from fyers_apiv3 import fyersModel
client_id = "QGP6MO6UJQ-100"
secret_key = "2X22I3160A"
redirect_uri = "https://trade.fyers.in/api-login/redirect-uri/index.html"
response_type = "code"  
state = "sample_state"
grant_type = "authorization_code"  

auth_code = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcHBfaWQiOiJRR1A2TU82VUpRIiwidXVpZCI6ImIzMjRkMjVhNDJlNzQwY2NhNmQ1NTNmZmEwOWYwNTU2IiwiaXBBZGRyIjoiIiwibm9uY2UiOiIiLCJzY29wZSI6IiIsImRpc3BsYXlfbmFtZSI6IlhSMjAxODUiLCJvbXMiOiJLMSIsImhzbV9rZXkiOiJkZWNhY2RhZDNmNzdjMGNkYTE0OThlNzY1MzdiMTMyYjcxNGMyZTg0NmQzNDFmMmZiYzkzZmY1YSIsImlzRGRwaUVuYWJsZWQiOiJOIiwiaXNNdGZFbmFibGVkIjoiTiIsImF1ZCI6IltcImQ6MVwiLFwiZDoyXCIsXCJ4OjBcIixcIng6MVwiLFwieDoyXCJdIiwiZXhwIjoxNzQ3NDQ4MzU5LCJpYXQiOjE3NDc0MTgzNTksImlzcyI6ImFwaS5sb2dpbi5meWVycy5pbiIsIm5iZiI6MTc0NzQxODM1OSwic3ViIjoiYXV0aF9jb2RlIn0.qvY2DMXxZwZ0iBDfH4U1tcez8E5h6vfHj74E5wLJZKg"




session = fyersModel.SessionModel(
    client_id=client_id,
    secret_key=secret_key, 
    redirect_uri=redirect_uri, 
    response_type=response_type, 
    grant_type=grant_type
)
session.set_token(auth_code)
response = session.generate_token()
print(response)

