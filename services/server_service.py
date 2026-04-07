from schemas import ServerResponse


def get_servers() -> list[ServerResponse]:
    return [
        ServerResponse(
            id="nl-ams-1",
            country="Нидерланды",
            countryCode="NL",
            city="Амстердам",
            host="nl-ams-1.example.com",
            isOnline=True,
            loadPercent=26,
        ),
        ServerResponse(
            id="de-fra-1",
            country="Германия",
            countryCode="DE",
            city="Франкфурт",
            host="de-fra-1.example.com",
            isOnline=True,
            loadPercent=34,
        ),
        ServerResponse(
            id="pl-waw-1",
            country="Польша",
            countryCode="PL",
            city="Варшава",
            host="pl-waw-1.example.com",
            isOnline=True,
            loadPercent=19,
        ),
    ]
