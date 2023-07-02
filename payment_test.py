#request payment api
import requests

url = "https://mercury-uat.phonepe.com/v3/charge"

headers = {
    "accept": "application/json",
    "Content-Type": "application/json",
    "X-VERIFY": "2dbfabed915b9b9759bc10a3ce6ecfbeb0c1169d5eada325668fcf31be8d360e###1"
}

response = requests.post(url, headers=headers)

print(response.text)

# check payment status
import requests

url = "https://mercury-uat.phonepe.com/v3/transaction/MERCHANTUAT/TX123456789/status"

headers = {
    "accept": "application/json",
    "X-VERIFY": "90443659f151a86831b7502c797c2ee4f3bcf63cbdad141c154effc2aad5c762###1"
}

response = requests.get(url, headers=headers)

print(response.text)