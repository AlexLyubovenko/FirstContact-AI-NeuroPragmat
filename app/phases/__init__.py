# app/phases/__init__.py
from .phase1 import handle_phase1
from .phase2a import handle_phase2a
from .phase3a import handle_phase3a
from .phase4a import handle_phase4a
from .phase5a import handle_phase5a
from .phase6a import handle_phase6a
from .phase7 import handle_phase7

def get_phase_handler(phase: str):
    handlers = {
        "phase1": handle_phase1,
        "phase2A": handle_phase2a,
        "phase3A": handle_phase3a,
        "phase4A": handle_phase4a,
        "phase5A": handle_phase5a,
        "phase6A": handle_phase6a,
        "phase7": handle_phase7,
    }
    return handlers.get(phase)