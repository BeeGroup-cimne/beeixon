# beeixon

API client to access [Ixon Cloud](https://developer.ixon.cloud/docs/how-to-use-the-apiv2),
used to resolve agent/device network configuration (public IPs, 1-on-1 NAT
rules...) for BMS devices reachable through Ixon routers.

HTTP calls go through `beelib.beerest.session_with_retries`, so a transient
connection reset from the Ixon API retries with backoff instead of failing
the whole caller job on a single flaky call.

## Installation

```bash
pip install git+https://github.com/BeeGroup-cimne/beeixon[@<version>]
```

## Usage

```python
from beeixon import Ixon

client = Ixon(application_id, email, password)
company_id = client.get_companies()[0]['publicId']
agents = client.get_agents(company_id)

for agent in agents:
    nat_rules = client.get_1on1_nat_config(agent['publicId'], company_id)
```

## Methods

- `get_companies()`: list companies visible to the account.
- `get_agents(company_id)`: list agents (routers) of a company, paginated.
- `get_network_config(agent, company_id)`: network/VPN/device config of an agent.
- `get_1on1_nat_config(agent, company_id)`: 1-on-1 NAT rules of an agent (public/local IP mapping for `vpn`-type rules).
- `get_groups(company_id)` / `get_group_types(company_id)`: groups and group types of a company.
