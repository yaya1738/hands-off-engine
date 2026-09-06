# Communication checkpoint

The autonomous system is considered low-intervention only when routine work
continues without a human operator while material decisions and blockers are
communicated through a durable, authenticated channel.

Required properties:

- authenticated inbound human messages
- ordinary messages become autonomous requests rather than being discarded
- durable inbound/outbound correlation IDs
- concise acknowledgements
- explicit blocker/decision messages when human input is genuinely required
- existing authority and approval boundaries remain in force
- no secrets or execution credentials are transmitted as conversational data
