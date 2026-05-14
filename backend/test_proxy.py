"""import requests

username = 'omanandTest_Cpl8Q'
password = '6u8Z=7qlYzPqF'
country = 'US'
proxy = 'dc.oxylabs.io:8000'

proxies = {
   "https": ('https://user-%s-country-%s:%s@%s' % (username, country, password, proxy))
}

response=requests.get("https://ip.oxylabs.io/location", proxies=proxies)

print(response.content)
"""



"""

invoke proxyscrape proxies 


import requests

proxies = {
    "http": "http://nt8s0vopdkix:g40efiboq0kms2q@193.56.28.161:3129",
    "https": "http://nt8s0vopdkix:g40efiboq0kms2q@193.56.28.161:3129",
}

response = requests.get("https://ipinfo.io/ip", proxies=proxies)
print(response.text)


"""