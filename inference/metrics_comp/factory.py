import importlib
from parser.customparser import PROMPT_VERSIONS, normalize_prompt_version

class ModuleFactory:
    """
    A factory for creating version-specific parser and error investigation objects.
    """
    def __init__(self, version: str):
        version = normalize_prompt_version(version)
        if version not in PROMPT_VERSIONS:
            raise ValueError(f"Unsupported version: {version}")
        self.version = version
        self._load_modules()

    def _load_modules(self):
        """Dynamically import modules based on the version string."""
        def _import_class(module_path_prefix, class_name):
            module_path = f"{module_path_prefix}{self.version}"
            module = importlib.import_module(module_path)
            return getattr(module, class_name)

        self.ParserLateralMovement = _import_class("parser.parser_lm", "ParserLateralMovement")
        self.ParserPersistence = _import_class("parser.parser_persistence", "ParserPersistence")
        self.ParserExfiltration = _import_class("parser.parser_exfiltration", "ParserExfiltration")
        self.ParserClassification = _import_class("parser.parser_classification", "ParserClassification")
        self.ErrorInvestigation = _import_class("error_analysis.errorinvestigation_", "ErrorInvestigation")