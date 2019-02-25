CONFIG = {}

def generate_config(in_options):
    global CONFIG
    CONFIG.update(vars(in_options))
    if 'features' in vars(in_options):
        CONFIG['features'] = sorted(in_options.features.split(','))

