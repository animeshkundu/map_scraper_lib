import requests
import fake_useragent

ua = fake_useragent.UserAgent()

def scrape(url, **kwargs):
    headers = {'User-Agent': ua.random}
    resp = requests.get(url, headers=headers, params=kwargs)
    return resp.text


def scrape_helper(args):
    return scrape(args[0], **args[1])
