import logging
import urllib.request
from urllib.error import URLError
import json
from pydblite.pydblite import Base


logger = logging.getLogger()


class AmazonProfile(object):
    def __init__(self, access_token=None):
        if access_token is not None:
            self._profile = self.get_profile(access_token)
        else:
            self._profile = None

    def get_profile(self, access_token):
        url = "https://api.amazon.com/user/profile?access_token={}".format(access_token)
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        try:
            req = urllib.request.Request(url,headers=headers)
            with urllib.request.urlopen(req) as response:
                data = response.read()
                encoding = response.info().get_content_charset('utf-8')
                self._profile = json.loads(data.decode(encoding))
                logger.critical('amazon_profile found {}'.format(self._profile))
        except URLError as e:
            self._profile = None
            if hasattr(e, 'reason'):
                logger.critical('We failed to reach a server.')
                logger.critical('Reason: ', e.reason)
            elif hasattr(e, 'code'):
                logger.critical('The server couldn\'t fulfill the request.')
                logger.critical('Error code: ', e.code)
        return self._profile

    def get_zip_code(self):
        zip_code = 'not known'
        if self._profile is not None:
            if 'postal_code' in self._profile.keys():
                zip_code = self._profile['postal_code']
                if len(zip_code) > 5:
                    zip_code = zip_code[:5]
        return zip_code






