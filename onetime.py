import praw
from prawoauth2 import PrawOAuth2Server

from tokens import app_key, app_secret
from settings import user_agent, scopes


r = praw.Reddit(user_agent=user_agent)

oauthserver = PrawOAuth2Server(r,app_key=app_key,app_secret=app_secret,state=user_agent,scopes=scopes)


#starting the server, opens web browser
#asking to authinticate
oauthserver.start()
tokens = oauthserver.get_access_codes()
print(tokens)
