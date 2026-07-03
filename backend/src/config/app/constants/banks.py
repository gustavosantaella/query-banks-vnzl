from src.modules.query.services.bancamiga_service import BancamigaService
from src.modules.query.services.bnc_service import BncService
BANKS = [
    {
        "label": "Bancamiga",
        "code": "0172",
        "config": [
            {
                "label": "Google Authenticator",
                "key": "google-auth",
                "required": True,
            }
        ],
        "callback": BancamigaService().login
    },

    {
        "label": "Banco Nacional de Credito",
        "code": "0191",
        "callback": BncService().balance 
    }
]