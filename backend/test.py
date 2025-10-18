# import requests

# url = "http://172.20.46.18:8088/v1/datasets/fba4f435-1d75-48a8-84b1-4eeb550d2bea"

# headers = {"Authorization": "Bearer dataset-XGhjOXFbkSkJqagNLbs0SDEy"}

# response = requests.get(url, headers=headers)

# print(response.json())
# import requests

# url = "http://172.20.46.18:8088/v1/datasets"

# querystring = {"page":"1","limit":"20"}

# headers = {"Authorization": "Bearer dataset-XGhjOXFbkSkJqagNLbs0SDEy"}

# response = requests.get(url, headers=headers, params=querystring)

# print(response.json())

import requests

url = "http://172.20.46.18:8088/v1/datasets/fba4f435-1d75-48a8-84b1-4eeb550d2bea/documents"

querystring = {"page":"1","limit":"20"}

headers = {"Authorization": "Bearer dataset-XGhjOXFbkSkJqagNLbs0SDEy"}

response = requests.get(url, headers=headers, params=querystring)

print(response.json())