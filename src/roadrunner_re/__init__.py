"""Propulsion reverse-engineering study: all physics lives here (ADR-0002)."""
from roadrunner_re.atmosphere import AirState, IsaAtmosphere
from roadrunner_re.config import CONFIG_DIR, REPO_ROOT, ConfigError
from roadrunner_re.engine_catalogue import Engine, load_engine_catalogue
from roadrunner_re.evidence import Claim, load_claims
from roadrunner_re.mission_profile import MissionProfile, Segment, load_mission
from roadrunner_re.uncertain import Uncertain

try:
    from roadrunner_re._version import __version__
except ImportError:  # bare checkout, package not installed
    __version__ = "0+unknown"
