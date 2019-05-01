from channels.routing import ProtocolTypeRouter
from channels import Group


# def ws_connect(message):
#     print("connect", message)
#     Group('users').add(message.reply_channel)


# def ws_disconnect(message):
#     Group('users').discard(message.reply_channel)   


# channel_routing = [
#     route('websocket.connect', ws_connect),
#     route('websocket.disconnect', ws_disconnect),
# ]
