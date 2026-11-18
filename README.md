# Django M-Pesa Daraja API Integration (STK Push)

A clean, end-to-end **Python Django** web application integrated with the **Safaricom Daraja API (Lipa Na M-Pesa Online / STK Push)**. It triggers real-time M-Pesa PIN prompts on a customer's phone, receives asynchronous payment confirmations via webhooks, and stores transaction records with M-Pesa receipt numbers in a database.

---

## Features

* **OAuth 2.0 Authentication:** Automatically generates Bearer access tokens from Safaricom's Daraja Sandbox using HTTP Basic Authentication.
* **Lipa Na M-Pesa STK Push:** Sends encrypted Base64 password payloads (`BusinessShortCode + Passkey + Timestamp`) to initiate mobile payment prompts.
* **Webhook Callback Handling:** Listens for Safaricom's asynchronous JSON callback responses via **ngrok** to update transaction statuses (`Pending` → `Completed` or `Failed`).
* **Database Persistence:** Saves phone numbers, amounts, `CheckoutRequestID`, timestamps, and official `MpesaReceiptNumber` codes using Django's ORM.
* **Live Transaction History & Admin Panel:** Displays a clean confirmation screen, a live frontend transaction table, and full record management via Django Admin.

---

## Tech Stack

* **Backend:** Python 3, Django
* **HTTP Client:** `requests`
* **API:** Safaricom Daraja 3.0 (M-Pesa Express / STK Push)
* **Tunneling (Local Webhooks):** ngrok
* **Database:** SQLite3

---

## Project Structure

```text
mpesa_project/
├── .gitignore
├── README.md
└── myproject/
    ├── manage.py
    ├── myproject/
    │   ├── settings.py
    │   └── urls.py
    └── mpesa_app/
        ├── admin.py
        ├── credentials.py      # Excluded from Git via .gitignore
        ├── models.py
        ├── urls.py
        ├── views.py
        └── templates/
            ├── pay.html
            └── status.html
```

---

## Local Setup & Installation

### 1. Clone the Repository
```bash
git clone https://github.com
cd django-mpesa-stk-push
```

### 2. Create & Activate a Virtual Environment
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install django requests pyngrok
```

### 4. Configure Safaricom Daraja Credentials
Create a `credentials.py` file inside `myproject/mpesa_app/` and add your keys from the [Safaricom Developer Portal](https://safaricom.co.ke):

```python
import requests
import base64
from datetime import datetime
from requests.auth import HTTPBasicAuth

class MpesaC2bCredential:
    consumer_key = 'YOUR_CONSUMER_KEY'
    consumer_secret = 'YOUR_CONSUMER_SECRET'
    api_URL = 'https://safaricom.co.ke'

class MpesaAccessToken:
    @staticmethod
    def get_access_token():
        headers = {
            "User-Agent": "Daraja-Client/1.0",
            "Accept": "application/json"
        }
        r = requests.get(
            MpesaC2bCredential.api_URL,
            headers=headers,
            auth=HTTPBasicAuth(
                MpesaC2bCredential.consumer_key.strip(),
                MpesaC2bCredential.consumer_secret.strip()
            )
        )
        return r.json()['access_token']

class LipanaMpesaPpassword:
    Business_short_code = "174379"
    passkey = 'YOUR_SANDBOX_PASSKEY'

    @classmethod
    def generate_password(cls):
        lipa_time = datetime.now().strftime('%Y%m%d%H%M%S')
        data_to_encode = cls.Business_short_code + cls.passkey.strip() + lipa_time
        online_password = base64.b64encode(data_to_encode.encode())
        return online_password.decode('utf-8'), lipa_time
```

### 5. Start ngrok for Callback Webhooks
In a separate terminal window, expose port `8000`:
```bash
ngrok http 8000
```
Copy your generated `https://...` forwarding URL and update `callback_url` in `myproject/mpesa_app/views.py`:
```python
callback_url = "https://ngrok-free.dev"
```

### 6. Run Migrations & Start the Server
```bash
cd myproject
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

Visit `http://127.0.0` in your browser, enter a Safaricom test number in the format `2547XXXXXXXX`, and click **Pay Now**.

---

## Security Notes

* Never commit `credentials.py`, `.env`, or `db.sqlite3` to version control.
* Before moving to production, switch endpoints from `sandbox.safaricom.co.ke` to `api.safaricom.co.ke`, replace test credentials with live Paybill/Till credentials, and set `DEBUG = False` in `settings.py`.
