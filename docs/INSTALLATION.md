# Installation Guide

Complete installation instructions for PrunArr.

## Table of Contents

- [Requirements](#requirements)
- [Install from PyPI](#install-from-pypi-recommended)
- [Install from Source](#install-from-source-development)
- [Verify Installation](#verify-installation)
- [Next Steps](#next-steps)

---

## Requirements

- **Python 3.9 or higher**
- **Radarr** (for movies) and/or **Sonarr** (for TV shows)
- **Tautulli** (for watch history)
- **API keys** for all three services

---

## Install from PyPI (Recommended)

The easiest way to install PrunArr is via pip:

```bash
pip install prunarr
```

That's it! PrunArr is now installed and ready to configure.

---

## Install from Source (Development)

If you want to contribute or use the latest development version:

```bash
# Clone the repository
git clone https://github.com/haijeploeg/prunarr
cd prunarr

# Create virtual environment
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate

# Install in development mode
pip install -e .

# Optional: Install development dependencies
pip install -e ".[dev]"
```

---

## Verify Installation

Check that PrunArr is installed correctly:

```bash
prunarr --help
```

You should see the help message with available commands.

---

## Next Steps

1. **Configure PrunArr**: See [CONFIGURATION.md](CONFIGURATION.md) to set up your API keys
2. **Set up tags**: Read about the [Tag System](TAG_SYSTEM.md) (or use Overseerr)
3. **Start using**: Check the [Quick Start Guide](QUICK_START.md)
4. **Learn commands**: Browse the [Command Reference](COMMANDS.md)

---

[← Back to README](../README.md)
