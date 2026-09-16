# PyNest service

This is a template for a PyNest service.

## Environment variables

Copy `.env.example` to `.env` and adjust the values.

### Browser (Selenium)

| Variable | Default | Description |
| --- | --- | --- |
| `SELENIUM_REMOTE_URL` | - | URL of a remote browser (Selenium Grid / `selenium/standalone-chromium` container). If set, no local Chromium/ChromeDriver is needed. |
| `SELENIUM_HEADLESS` | `False` | `True` runs the browser in the background (no visible window). Also accepts `1`, `yes`, `on`, `si`. |
| `SELENIUM_WINDOW_WIDTH` | `1920` | Window/viewport width. In headless mode it defines the real viewport, and the bank's DOM is responsive. |
| `SELENIUM_WINDOW_HEIGHT` | `1080` | Window/viewport height. |
| `SELENIUM_WINDOW_POSITION` | - | `x,y` window position (visible mode only). |
| `CHROMIUM_BINARY_PATH` | - | Custom Chrome/Chromium binary path (local browser mode). |
| `CHROME_DRIVER_PATH` | - | Custom chromedriver path (local browser mode). |

### Banks

| Bank | Variables |
| --- | --- |
| BNC (0191) | `BNC_URL`, `BNC_CARD_NUMBER`, `DNI`, `BNC_PASS` |
| Bancamiga (0172) | `BANCAMIGA_URL`, `BANCAMIGA_USER`, `BANCAMIGA_PASS` |

If a credential is missing from the environment, the service asks for it on the console.

## Start Service

## Step 1 - Create environment

- install requirements:

```bash
pip install -r requirements.txt
```

## Step 2 - start service local

1. Run service with main method

```bash
python main.py
```

2. Run service using uvicorn

```bash
uvicorn "app:app" --host "0.0.0.0" --port "8000" --reload
```

## Step 3 - Send requests

Go to the fastapi docs and use your api endpoints - http://127.0.0.1/docs
