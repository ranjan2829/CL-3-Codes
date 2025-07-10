
access_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOlsiZDoxIiwiZDoyIiwieDowIiwieDoxIiwieDoyIl0sImF0X2hhc2giOiJnQUFBQUFCb2IzLXlPTzR5NGhIcVk2YndnaG1BVFgyaDFVWWxUWG9SRl9jd2hNejJWLUFDWnVPOURqckZMSGZRTnIwVUEtWldRZVR3bGdMVlBXRTNPekJ5WGhteW1jUUNGSGxLUnRtOTZqZ0NMWHpkMmlxRk9zOD0iLCJkaXNwbGF5X25hbWUiOiIiLCJvbXMiOiJLMSIsImhzbV9rZXkiOiJkZWNhY2RhZDNmNzdjMGNkYTE0OThlNzY1MzdiMTMyYjcxNGMyZTg0NmQzNDFmMmZiYzkzZmY1YSIsImlzRGRwaUVuYWJsZWQiOiJOIiwiaXNNdGZFbmFibGVkIjoiTiIsImZ5X2lkIjoiWFIyMDE4NSIsImFwcFR5cGUiOjEwMCwiZXhwIjoxNzUyMTkzODAwLCJpYXQiOjE3NTIxMzc2NTAsImlzcyI6ImFwaS5meWVycy5pbiIsIm5iZiI6MTc1MjEzNzY1MCwic3ViIjoiYWNjZXNzX3Rva2VuIn0.7iqQmH6dOyGfSMHXGPKhNYJujyD11Ku6i-_a2SyoPSE"
from fyers_apiv3.FyersWebsocket.tbt_ws import FyersTbtSocket, SubscriptionModes

def onopen():
    """
    Callback function to subscribe to data type and symbols upon WebSocket connection.

    """
    print("Connection opened")
    mode = SubscriptionModes.DEPTH
    Channel = '1'
    symbols = ['NIFTY25JUNFUT']
    
    fyers.subscribe(symbol_tickers=symbols, channelNo=Channel, mode=mode)
    fyers.switchChannel(resume_channels=[Channel], pause_channels=[])
    fyers.keep_running()

def on_depth_update(ticker, message):
    """
    Callback function to handle incoming messages from the FyersDataSocket WebSocket.

    Parameters:
        ticker (str): The ticker symbol of the received message.
        message (Depth): The received message from the WebSocket.

    """
    print("ticker", ticker)
    print("depth response:", message)
    print("total buy qty:", message.tbq)
    print("total sell qty:", message.tsq)
    print("bids:", message.bidprice)
    print("asks:", message.askprice)
    print("bidqty:", message.bidqty)
    print("askqty:", message.askqty)
    print("bids ord numbers:", message.bidordn)
    print("asks ord numbers:", message.askordn)
    print("issnapshot:", message.snapshot)
    print("tick timestamp:", message.timestamp)


def onerror(message):
    """
    Callback function to handle WebSocket errors.

    Parameters:
        message (dict): The error message received from the WebSocket.

    """
    print("Error:", message)
def onclose(message):
    """
    Callback function to handle WebSocket connection close events.
    """
    print("Connection closed:", message)
def onerror_message(message):
    """
    Callback function for error message events from the server

    Parameters:
        message (dict): The error message received from the Server.

    """
    print("Error Message:", message)


fyers = FyersTbtSocket(
    access_token=access_token,
    write_to_file=False,
    log_path="",
    on_open=onopen,
    on_close=onclose,
    on_error=onerror,
    on_depth_update=on_depth_update,
    on_error_message=onerror_message
)
fyers.connect()
