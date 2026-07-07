import re
from pathlib import Path

from src.models.testcase import Module, Scenario
from src.utils.formatter import format_smart_list


# Max file size: 10 MB (prevents OOM from accidental huge files)
_MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

# Pre-compiled regex patterns
_RE_MODULE = re.compile(r'^#\s*Module:\s*(.*)', re.MULTILINE)
_RE_SCENARIO_SPLIT = re.compile(r'^##\s*Scenario:\s*', re.MULTILINE)
_RE_GLOBAL_META = re.compile(r'^([^\*]+?):\s*(.*)$')
_RE_LOCAL_META = re.compile(r'^\*\*(.*?)\*\*:\s*(.+)$')
_RE_TRIGGER = re.compile(r'^\*\*(Precondition|Test Steps|Expected Result)\*\*:\s*$')

class MarkdownParser:
    def __init__(self, filepath: str | Path):
        self.filepath = Path(filepath)
        
    def parse(self) -> Module:
        file_size = self.filepath.stat().st_size
        if file_size > _MAX_FILE_SIZE_BYTES:
            raise ValueError(
                f"File '{self.filepath}' is {file_size / 1024 / 1024:.1f} MB, "
                f"exceeds the {_MAX_FILE_SIZE_BYTES / 1024 / 1024:.0f} MB limit."
            )

        with open(self.filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        module_match = _RE_MODULE.search(content)
        module_name = module_match.group(1).strip() if module_match else "Unknown Module"
        
        module = Module(name=module_name)
        
        # Split by ## Scenario:
        parts = _RE_SCENARIO_SPLIT.split(content)
        
        from src.core.config import ConfigManager
        config = ConfigManager.get()
        allowed_keys_lower = {k.lower(): k for k in config.global_metadata_keys}

        # Parse global metadata (before first scenario)
        global_section = parts[0]
        for line in global_section.split('\n'):
            line = line.strip()
            # Match Key: Value (NO bold)
            match = _RE_GLOBAL_META.match(line)
            if match and not line.startswith('#'):
                raw_key = match.group(1).strip()
                val = match.group(2).strip()
                key_lower = raw_key.lower()
                
                if key_lower in allowed_keys_lower:
                    # Save using the exact case from config
                    module.global_metadata[allowed_keys_lower[key_lower]] = val
                
        # Parse scenarios
        for part in parts[1:]:
            lines = part.split('\n')
            scenario_name = lines[0].strip()
            
            scenario = Scenario(name=scenario_name)
            current_trigger = None
            current_text = []
            
            for line in lines[1:]:
                # Check for LOCAL METADATA: **Key**: Value
                meta_match = _RE_LOCAL_META.match(line.strip())
                if meta_match:
                    if current_trigger:
                        self._save_trigger(scenario, current_trigger, current_text)
                        current_trigger = None
                        current_text = []
                    
                    key = meta_match.group(1).strip()
                    val = meta_match.group(2).strip()
                    scenario.local_metadata[key] = val
                    continue
                    
                # Check for TRIGGER WORDS: **Precondition**:, **Test Steps**:, **Expected Result**:
                trigger_match = _RE_TRIGGER.match(line.strip())
                if trigger_match:
                    if current_trigger:
                        self._save_trigger(scenario, current_trigger, current_text)
                    current_trigger = trigger_match.group(1)
                    current_text = []
                    continue
                    
                if current_trigger is not None:
                    current_text.append(line)
                    
            if current_trigger:
                self._save_trigger(scenario, current_trigger, current_text)
                
            module.scenarios.append(scenario)
            
        return module

    def _save_trigger(self, scenario: Scenario, trigger: str, lines: list[str]) -> None:
        text = '\n'.join(lines).strip()
        formatted = format_smart_list(text)
        if trigger == "Precondition":
            scenario.precondition = formatted
        elif trigger == "Test Steps":
            scenario.test_steps = formatted
        elif trigger == "Expected Result":
            scenario.expected_result = formatted
