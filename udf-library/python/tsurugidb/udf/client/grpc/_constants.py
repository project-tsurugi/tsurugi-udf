
# metadata keys for BLOB client configurations
KEY_PREFIX = "x-tsurugi-blob-"
KEY_TRANSPORT = KEY_PREFIX + "transport"
KEY_SESSION = KEY_PREFIX + "session"
KEY_ENDPOINT = KEY_PREFIX + "endpoint"
KEY_SECURE = KEY_PREFIX + "secure"

DEFAULT_SECURE = False

__all__ = [
    KEY_PREFIX,
    KEY_TRANSPORT,
    KEY_SESSION,
    KEY_ENDPOINT,
    KEY_SECURE,
    DEFAULT_SECURE,
]