import requests
import json

ACCESS_TOKEN = "EAAKuMdAKZBHoBQbV4Fzl6XGQQyKoQTcIb9lUEawXEpfEGhzclNnxLTmEGVh1K1oIGromaSbkuWU9TRj0HLR8qnX0yLSXLPE4RyH86GtluriBDJr5wzg037cUfhu6rQqkBKrpwfYPDiogtKl2Y3q19FC0ZB0ravIe8ShLk6DRHXV2s160ZA2TnjXoWpQcsJgIj7hahbA8kWuH5fZBB48zzVCZCng6bWSZCPi6f1rZBFwIhL81pUlDokJrqiMDNnmBkY94f23G8iCbhwN4nCozW4aWAZDZD"
PHONE_NUMBER_ID = "1006821609171166"

url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"

headers = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json"
}

payload = {
    "messaging_product": "whatsapp",
    "to": "918778021610",  # OTP verified number
    "type": "text",
    "text": {
        "body": "API Test macha ✅\nMessage from Python code"
    }
}

response = requests.post(url, headers=headers, json=payload)

print(response.status_code)
print(json.dumps(response.json(), indent=2))
