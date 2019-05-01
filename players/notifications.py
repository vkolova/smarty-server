from exponent_server_sdk import DeviceNotRegisteredError
from exponent_server_sdk import PushClient
from exponent_server_sdk import PushResponseError
from exponent_server_sdk import PushServerError
from requests.exceptions import ConnectionError
from requests.exceptions import HTTPError

def send_push_message(message):
    try:
        response = PushClient().publish(message)
    except PushServerError as exc:
        raise
    except (ConnectionError, HTTPError) as exc:
        raise
    try:
        response.validate_response()
    except DeviceNotRegisteredError:
        pass
        # from notifications.models import PushToken
        # PushToken.objects.filter(token=token).update(active=False)
    except PushResponseError as exc:
        raise