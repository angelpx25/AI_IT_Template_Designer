#login.py

def login(authenticator):
    name, authentication_status, username = authenticator.login('DDE Tools Portal', 'main')
    return name, authentication_status, username
