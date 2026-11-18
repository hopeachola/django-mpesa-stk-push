import json
import requests
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .credentials import MpesaAccessToken, LipanaMpesaPpassword
from .models import Transaction

def home(request):
    transactions = Transaction.objects.all().order_by('-created_at')
    return render(request, 'pay.html', {'transactions': transactions})


def pay(request):
    if request.method == "POST":
        phone = request.POST.get('phone').strip()
        amount = request.POST.get('amount').strip()

        # 1. Paste your FULL Forwarding URL from the ngrok terminal + /callback/
        callback_url = "https://chunk-flagship-cryptic.ngrok-free.dev"

        try:
            access_token = MpesaAccessToken.get_access_token()
            password, timestamp = LipanaMpesaPpassword.generate_password()
        except Exception as e:
            return render(request, 'status.html', {'success': False, 'message': str(e)})

        api_url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "Daraja-Client/1.0"
        }

        payload = {
            "BusinessShortCode": LipanaMpesaPpassword.Business_short_code,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": int(amount),
            "PartyA": phone,
            "PartyB": LipanaMpesaPpassword.Business_short_code,
            "PhoneNumber": phone,
            "CallBackURL": callback_url,
            "AccountReference": "TestPayment",
            "TransactionDesc": "Payment for goods"
        }

        response = requests.post(api_url, json=payload, headers=headers)
        data = response.json()

        if data.get("ResponseCode") == "0":
            Transaction.objects.create(
                checkout_request_id=data["CheckoutRequestID"],
                phone_number=phone,
                amount=amount,
                status="Pending"
            )
            return render(request, 'status.html', {
                'success': True,
                'message': data.get("CustomerMessage"),
                'phone': phone,
                'amount': amount
            })
        else:
            return render(request, 'status.html', {
                'success': False,
                'message': data.get("errorMessage", "Request rejected by M-Pesa.")
            })

    return render(request, 'pay.html')

@csrf_exempt
def mpesa_callback(request):
    if request.method == "POST":
        body = json.loads(request.body.decode('utf-8'))
        stk_callback = body.get('Body', {}).get('stkCallback', {})
        checkout_id = stk_callback.get('CheckoutRequestID')
        result_code = stk_callback.get('ResultCode')

        transaction = Transaction.objects.filter(checkout_request_id=checkout_id).first()
        if transaction:
            if result_code == 0:
                items = stk_callback.get('CallbackMetadata', {}).get('Item', [])
                receipt = next((i['Value'] for i in items if i['Name'] == 'MpesaReceiptNumber'), None)
                transaction.mpesa_receipt_number = receipt
                transaction.status = "Completed"
            else:
                transaction.status = "Failed"
            transaction.save()

        return JsonResponse({"ResultCode": 0, "ResultDesc": "Accepted"})
    return JsonResponse({"error": "Invalid method"}, status=400)
