from rest_framework.throttling import AnonRateThrottle


class RegisterAnonThrottle(AnonRateThrottle):
    scope = "register"


class EsicAnonThrottle(AnonRateThrottle):
    scope = "esic"

