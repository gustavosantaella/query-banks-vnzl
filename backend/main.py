import uvicorn
from dotenv import load_dotenv

if __name__ == '__main__':
    load_dotenv()
    uvicorn.run(
        'src.app_module:http_server',
        host="0.0.0.0",
        port=8000,
        reload=True
    )
    
