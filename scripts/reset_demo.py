from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from data.seed.network import initialize

initialize(reset=True)
print("Demo reset. Restart the API if it was running. Operational data is synthetic.")
