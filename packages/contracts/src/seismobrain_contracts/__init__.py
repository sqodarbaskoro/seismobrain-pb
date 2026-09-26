"""
File: __init__.py
Description: seismobrain-contracts package root
Author: Sri Yanto Qodarbaskoro
Contact: sqodarbaskoro@gmail.com
LinkedIn: https://www.linkedin.com/in/sqodarbaskoro/
Website: https://www.seismopilot.com
Created: 2026-09-16
Modified: 2026-09-16
Version: 0.1.0
Copyright: © 2026 Sri Yanto Qodarbaskoro
"""

from seismobrain_contracts.health import HealthResponse, ReadyResponse

__version__ = "0.1.0"

__all__ = ["HealthResponse", "ReadyResponse", "__version__"]
