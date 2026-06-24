from sys import prefix
from nest.core import PyNestFactory, Module
from src.modules.query.query_module import QueryModule
        


@Module(imports=[
    QueryModule
], controllers=[], providers=[])
class AppModule:
    pass


app = PyNestFactory.create(
    AppModule,
    description="This is my PyNest app.",
    title="PyNest Application",
    version="1.0.0",
    debug=True,
)

http_server = app.get_server()

http_server.root_path = "/api"


                