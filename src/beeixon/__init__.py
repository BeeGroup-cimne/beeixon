import base64
import json

from beelib.beerest import session_with_retries

__version__ = "0.0.1"


class Ixon:
    """
    Implementation of the Ixon API, following the documentation at
    https://developer.ixon.cloud/docs/how-to-use-the-apiv2

    All HTTP calls go through a beelib retrying session (see
    beelib.beerest.session_with_retries), so a transient connection reset
    from the Ixon API retries with backoff instead of failing the whole job
    on a single call.
    """
    api_version = '2'
    api_url = 'https://portal.ixon.cloud/api'

    def __init__(self, application_id, email, password):
        self.application_id = application_id
        self.session = session_with_retries()
        self.token, self.public_id = self.__generate_token(email, password)

    def __generate_token(self, email, password, otp=''):
        encoded_str = base64.b64encode(bytes(f"{email}:{otp}:{password}", 'utf-8')).decode('utf-8')

        headers = {"Api-Version": self.api_version,
                   "Api-Application": self.application_id,
                   "Content-Type": "application/json",
                   "Authorization": f"Basic {encoded_str}"
                   }
        res = self.session.post(url=self.api_url + '/access-tokens', headers=headers,
                                 data=json.dumps({"expiresIn": 5184000}), timeout=(5, 20))  # expiresIn (seconds) max: 60d
        if res.ok:
            res = res.json()
            token = res['data']['secretId']
            public_id = res['data']['publicId']
            return token, public_id
        else:
            raise Exception(f"Token generation failed: {res.reason}")

    def get_companies(self):
        headers = {
            "Content-Type": "application/json",
            "Api-Version": self.api_version,
            "Api-Application": self.application_id,
            "Authorization": f"Bearer {self.token}"
        }

        res = self.session.get(url=self.api_url + f'/companies?fields=publicId,name', headers=headers)
        if res.ok:
            res = res.json()
            return res['data']
        else:
            raise Exception(f"Company gather failed: {res.reason}")

    def get_agents(self, company_id):
        headers = {
            "Content-Type": "application/json",
            "Api-Version": self.api_version,
            "Api-Application": self.application_id,
            "Authorization": f"Bearer {self.token}",
            "Api-Company": company_id
        }
        more_after = True
        limit = 1000
        agents = []
        while more_after:
            if more_after is True:
                res = self.session.get(url=self.api_url + f'/agents?page-size={limit}&fields=publicId,description',
                                        headers=headers)
            else:
                res = self.session.get(
                    url=self.api_url + f'/agents?page-size={limit}&fields=publicId,description&page-after={more_after}',
                    headers=headers)
            if res.ok:
                res = res.json()
                more_after = res['moreAfter']
                agents.extend(res['data'])
            else:
                raise Exception(f"Agent gather failed: {res.reason}")
        return agents

    def get_network_config(self, agent, company_id):
        headers = {
            "Api-Version": '2',
            "Api-Application": self.application_id,
            'Authorization': f"Bearer {self.token}",
            "Api-Company": company_id
        }

        res = self.session.get(
            url=f"https://portal.ixon.cloud/api/agents/{agent}?fields=activeVpnSession.vpnAddress,"
                f"config.routerLan.*,devices.*,devices.dataProtocol.*,deviceId,description,config.routerWan.*,"
                f"*,lastSeenAgentUserAgent.*,location.*,custom.*,networkValues.*,memberships.group.name",
            headers=headers,
            timeout=20)
        if res.ok:
            return res.json()
        else:
            raise Exception(f"Network config gather failed: {res.reason}")

    def get_1on1_nat_config(self, agent, company_id):
        headers = {
            "Api-Version": '2',
            "Api-Application": self.application_id,
            'Authorization': f"Bearer {self.token}",
            "Api-Company": company_id
        }
        more_after = True
        limit = 1000
        n1n_list = []
        while more_after:
            if more_after is True:
                res = self.session.get(url=self.api_url + f'/agents/{agent}/router-one-to-one-nat-rules?page-size={limit}',
                                        headers=headers)
            else:
                res = self.session.get(url=self.api_url + f'/agents/{agent}/router-one-to-one-nat-rules?page-size={limit}&page-after={more_after}',
                                        headers=headers)
            if res.ok:
                res = res.json()
                more_after = res['moreAfter']
                n1n_list.extend(res['data'])
            else:
                raise Exception(f"Agent gather failed: {res.reason}")
        n1n_rules = []
        for n1n in n1n_list:
            res = self.session.get(url=self.api_url + f'/agents/{agent}/router-one-to-one-nat-rules/{n1n["publicId"]}',
                                    headers=headers)
            if res.ok:
                n1n_el = res.json()
                if n1n_el['data']['type'] == 'vpn':
                    n1n_rules.append(n1n_el['data'])
        return n1n_rules

    def get_groups(self, company_id):
        headers = {
            "Api-Version": '2',
            "Api-Application": self.application_id,
            'Authorization': f"Bearer {self.token}",
            "Api-Company": company_id
        }

        res = self.session.get(
            url=f"https://portal.ixon.cloud:443/api/groups?fields=name,type(name,description)&page-size=1000",
            headers=headers,
            timeout=20)
        if res.ok:
            return res.json()
        else:
            raise Exception(f"Network config gather failed: {res.reason}")

    def get_group_types(self, company_id):
        headers = {
            "Api-Version": '2',
            "Api-Application": self.application_id,
            'Authorization': f"Bearer {self.token}",
            "Api-Company": company_id
        }
        res = self.session.get(
            url=f"https://portal.ixon.cloud:443/api/group-types?page-size=1000",
            headers=headers,
            timeout=20)
        if res.ok:
            return res.json()
        else:
            raise Exception(f"Network config gather failed: {res.reason}")
