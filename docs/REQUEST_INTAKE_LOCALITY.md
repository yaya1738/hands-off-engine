# RequestIntake checkout-locality boundary

`RequestIntake(repo_root=...)` derives its coordination bus, admission state, and party registry from the supplied checkout root. The admission gate must not cross-contaminate independent checkouts through module-global filesystem paths.

The regression in `tests/test_factory_request_intake.py` creates two independent roots, admits one request in each, and verifies both admission sets and persisted state remain isolated.

This boundary is observation/admission only: it does not introduce a second transport, dispatch path, or execution authority.
