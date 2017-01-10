import requests as r
import getpass as gp
import sys

class auth:
    # def __init__():

    def login():
        sid = None
        def retry():
            again = input('Try again? (Y/N): ')
            if again in ('Y', 'y', 'yes'):
                return auth.login()
            elif again in ('N', 'n', 'no'):
                sys.exit(2)
            else:
                print("Please type 'yes' or 'no'.")
                retry()
        try:
            print('Backup Database Login')
            usr = input('Enter Username: ')
            pwd = gp.getpass(prompt='Enter Password: ')
        except UserWarning as warn:
            print(warn)

        try:
            payloadAuth = {"api":"SYNO.API.Auth", "version":"3", "method":"login", "account":str(usr), "passwd":str(pwd), "session":"FileStation", "format":"cookie"}
            response = r.get('http://128.218.210.52:5000/webapi/auth.cgi', params=payloadAuth)
            response.raise_for_status()
            sid = response.json()['data']['sid']
        except (KeyError, r.exceptions.HTTPError) as err:
            print('Login Failed')
            retry()
        return sid

    def logout(sid):
        try:
            payloadAuth = {"api":"SYNO.API.Auth", "version":"1", "method":"logout", "session":"FileStation", "_sid":sid}
            logout = r.get('http://128.218.210.52:5000/webapi/auth.cgi', params=payloadAuth)
            logout.raise_for_status()
        except (KeyError, r.exceptions.HTTPError) as err:
            print('Logout Failed')
