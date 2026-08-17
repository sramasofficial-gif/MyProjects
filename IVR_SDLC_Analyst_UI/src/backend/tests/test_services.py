import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).parent.parent

sys.path.insert(0, str(BACKEND_ROOT))

from services.repo_tools import find_files
from services.repo_tools import read_file

print(find_files(".json"))

content = read_file(
    "contact-flows/cfAccountStatus.json"
)

print(content[:500])