
import threading
from src.config.app.constants.banks import BANKS
from src.modules.query.services.bancamiga_service import BancamigaService
from src.config.app.http.response import Response
from nest.core import Get
from nest.core import Controller
from src.modules.query.services.bnc_service import BncService
@Controller("/query")
class QueryController: 

    def __init__(self, bnc_service: BncService, bancamiga_service: BancamigaService):
        self.bnc_service = bnc_service
        self.bancamiga_service = bancamiga_service

    @Get("/")
    def get_all_queries(self, google_auth: str = None):
        results = {}
        config = {}
        if google_auth:
            config["google-auth"] = google_auth

        def worker(bank):
            try:
                if bank["code"] == "0172":
                    results[bank["code"]] = bank["callback"](config=config)
                else:
                    results[bank["code"]] = bank["callback"]()
            except Exception as e:
                print(f"Error executing callback for {bank['label']}: {str(e)}")
                results[bank["code"]] = None

        threads: list[threading.Thread] = []

        for bank in BANKS:
            thread = threading.Thread(target=worker, args=(bank,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        response_data = []
        for bank in BANKS:
            response_data.append({
                "label": bank["label"],
                "code": bank["code"],
                "data": results.get(bank["code"])
            })

        return Response(data=response_data).to_dict()


    @Get("/by-bank")
    def query_by_bank(self, code: str, google_auth: str = None, card_number: str = None, dni: str = None, password: str = None):
        bank = next((bank for bank in BANKS if bank["code"] == code), None)
        if not bank:
            return Response(code=404, message="Bank not found").to_dict()
        
        config = {}
        if google_auth:
            config["google-auth"] = google_auth
        # Credenciales opcionales para BNC (si no se envían se leen del .env o por consola)
        if card_number:
            config["BNC_CARD_NUMBER"] = card_number
        if dni:
            config["DNI"] = dni
        if password:
            config["BNC_PASS"] = password
            
        try:
            if code == "0172":
                data = bank["callback"](config=config)
            elif code == "0191":
                data = bank["callback"](config=config or None)
            else:
                data = bank["callback"]()
            return Response(data=data).to_dict()
        except Exception as e:
            return Response(code=500, message=str(e)).to_dict()


    @Get("/banks")
    def banks(self):
        serialized_banks = []
        for bank in BANKS:
            b_copy = {k: v for k, v in bank.items() if k != "callback"}
            serialized_banks.append(b_copy)
        return Response(data=serialized_banks).to_dict()
    

        
