
from src.modules.query.services.bancamiga_service import BancamigaService
from src.modules.query.services.bnc_service import BncService
from src.modules.query.controllers.query_controller import QueryController
from nest.core import Module


@Module(
    imports=[],
    controllers=[QueryController],
    providers=[
        BncService,
        BancamigaService
    ],
    exports=[]
)
class QueryModule:
    pass