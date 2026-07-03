
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
    def get_all_queries(self):
        results = {}

        def worker(bank):
            try:
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
    def query_by_bank(self, code: str):
        bank = next((bank for bank in BANKS if bank["code"] == code), None)
        if not bank:
            return Response(code=404, message="Bank not found").to_dict()
        return Response(data=bank["callback"]()).to_dict()
    

        
