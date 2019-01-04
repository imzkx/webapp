#config.py
import config_default
configs = config_default.configs

try:
    import config_overrude
    configs = merge(configs, config_override.configs)
except ImportError:
    pass