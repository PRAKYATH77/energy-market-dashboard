"""Shared configuration for the energy market dashboard."""
import tempfile
from pathlib import Path

DB_PATH = Path(tempfile.gettempdir()) / "energy_market_dashboard" / "energy_data.db"
