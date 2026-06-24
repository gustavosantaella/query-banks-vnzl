
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
        # bnc_balance = self.bnc_service.balance()
        bancamiga_balance = self.bancamiga_service.login()
        return Response(data={
            "BNC": {
                "img": "",
                # "amount": bnc_balance
            },
            "BANCAMIGA": {
                "img": "",
                "amount": bancamiga_balance
            }
        }).to_dict()

        
