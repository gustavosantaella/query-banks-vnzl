import uvicorn
from dotenv import load_dotenv
import os

if __name__ == '__main__':
    load_dotenv()
    uvicorn.run(
        'src.app_module:http_server',
        host="0.0.0.0",
        port=int(os.getenv("APP_PORT")),
        reload=True
    )
    
