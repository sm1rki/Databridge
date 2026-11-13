"""DataBridge entry point for module execution: python -m databridge"""

import sys
from .cli.main import main

if __name__ == "__main__":
    sys.exit(main())
