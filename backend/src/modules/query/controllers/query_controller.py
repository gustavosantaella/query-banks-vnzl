
from src.config.app.http.response import Response
from nest.core import Get
from nest.core import Controller
from src.modules.query.services.bnc_service import BncService
@Controller("/query")
class QueryController: 

    def __init__(self, bnc_service: BncService):
        self.bnc_service = bnc_service

    @Get("/")
    def get_all_queries(self):
        balance = self.bnc_service.balance()
        return Response(data=balance).to_dict()

        
