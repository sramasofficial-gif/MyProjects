from services.repo_tools import (
    resolve_repository_file
)

from services.flow_audit import (
    audit_contact_flow_file
)

path = resolve_repository_file(
    "contact-flows/cfAccountStatus.json"
)

report = audit_contact_flow_file(path)

import json

print(
    json.dumps(
        report,
        indent=2
    )
)