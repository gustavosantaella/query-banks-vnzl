
from src.modules.query.services.bnc_service import BncService
from src.modules.query.controllers.query_controller import QueryController
from nest.core import Module


@Module(
    imports=[],
    controllers=[QueryController],
    providers=[
        BncService
    ],
    exports=[]
)
class QueryModule:
    pass