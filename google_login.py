import requests
from bs4 import BeautifulSoup
import credentials


class SessionGoogle:
    def __init__(self, url_login, url_auth, login, pwd):
        self.ses = requests.session()
        login_html = self.ses.get(url_login)
        soup_login = BeautifulSoup(login_html.content).find("form").find_all("input")
        my_dict = {}
        for u in soup_login:
            if u.has_attr("value"):
                my_dict[u["name"]] = u["value"]
        # override the inputs without login and pwd:
        my_dict["Email"] = login
        my_dict["Passwd"] = pwd
        self.ses.post(url_auth, data=my_dict)

    def get(self, URL):
        return self.ses.get(URL).text


url_login = "https://accounts.google.com/ServiceLogin"
url_auth = "https://accounts.google.com/ServiceLoginAuth"
session = SessionGoogle(url_login, url_auth, credentials.username, credentials.password)
# print(session.get("http://plus.google.com"))
with open("google_back.txt", "w") as buf:
    buf.write(session.get("http://plus.google.com"))
