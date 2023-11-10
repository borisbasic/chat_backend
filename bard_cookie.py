import browser_cookie3

def _extract_bard_cookie() -> dict:
    cookie_dict = {}
    
    cj = browser_cookie3.chrome(cookie_file=r'C:\Users\<your user>\AppData\Local\Google\Chrome\User Data\Default\Network\Cookies',domain_name=".google.com")

    for cookie in cj:
        if cookie.name == "__Secure-1PSID" and cookie.value.endswith("."):
            cookie_dict["__Secure-1PSID"] = cookie.value
        if cookie.name == "__Secure-1PSIDTS":
            cookie_dict["__Secure-1PSIDTS"] = cookie.value
        if cookie.name == "__Secure-1PSIDCC":
            cookie_dict["__Secure-1PSIDCC"] = cookie.value

    logging.info(cookie_dict)
    return cookie_dict

_extract_bard_cookie()