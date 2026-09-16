import os

import uvicorn
from dotenv import load_dotenv

if __name__ == '__main__':
    load_dotenv()

    # Railway (y otros PaaS) inyectan el puerto a escuchar en la variable PORT
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "True").strip().lower() in ("true", "1", "yes", "on", "si")

    uvicorn.run(
        'src.app_module:http_server',
        host="0.0.0.0",
        port=port,
        reload=reload,
    )
    
