"""
Spintax processing for message personalization.

Bulk expansion prefers the optional Rust native accelerator (`tmms_native`)
when available; single expansions and missing binaries use pure Python.
"""

import re
import random
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from .native_accel import spintax_expand_batch


@dataclass
class SpintaxResult:
    """Result of spintax processing."""

    text: str
    variables_used: List[str]
    variants_count: int
    backend: str = "python"


class SpintaxProcessor:
    """Processes spintax syntax for message personalization."""

    def __init__(self, seed: Optional[int] = None):
        """Initialize spintax processor with optional seed for reproducibility."""
        self.seed = seed
        self._random = random.Random(seed) if seed is not None else random

    def process(self, text: str) -> SpintaxResult:
        """Process spintax text and return result."""
        if not text or not isinstance(text, str):
            return SpintaxResult(text="", variables_used=[], variants_count=0)

        # Find all spintax patterns
        patterns = self._find_spintax_patterns(text)
        if not patterns:
            return SpintaxResult(text=text, variables_used=[], variants_count=1)

        # Process each pattern
        result_text = text
        variables_used = []
        total_variants = 1

        for pattern in patterns:
            variants = self._extract_variants(pattern)
            if variants:
                selected = self._random.choice(variants)
                result_text = result_text.replace(pattern, selected, 1)
                variables_used.extend(variants)
                total_variants *= len(variants)

        return SpintaxResult(
            text=result_text,
            variables_used=list(set(variables_used)),
            variants_count=total_variants,
            backend="python",
        )

    def expand_batch(self, text: str, count: int) -> List[str]:
        """
        Expand the same template `count` times.

        Uses Rust+rayon for larger batches when the native binary is present;
        otherwise expands in pure Python (same semantics as `process`).
        """
        if count <= 0:
            return []
        if not text or not isinstance(text, str):
            return [""] * count

        native_texts = spintax_expand_batch(text, count, seed=self.seed)
        if native_texts is not None:
            return native_texts

        return [self.process(text).text for _ in range(count)]

    def _find_spintax_patterns(self, text: str) -> List[str]:
        """Find all spintax patterns in text."""
        # Pattern: {option1|option2|option3}
        pattern = r"\{[^{}]*\}"
        return re.findall(pattern, text)

    def _extract_variants(self, pattern: str) -> List[str]:
        """Extract variants from a spintax pattern."""
        # Remove outer braces
        content = pattern[1:-1]

        # Split by pipe, handling nested braces
        variants = self._split_by_pipe(content)

        # Clean up variants but keep empty ones
        return [v.strip() for v in variants]

    def _split_by_pipe(self, text: str) -> List[str]:
        """Split text by pipe, respecting nested braces."""
        variants = []
        current = ""
        brace_count = 0

        for char in text:
            if char == "{":
                brace_count += 1
            elif char == "}":
                brace_count -= 1
            elif char == "|" and brace_count == 0:
                variants.append(current)
                current = ""
                continue

            current += char

        variants.append(current)

        return variants

    def get_preview_samples(self, text: str, count: int = 10) -> List[str]:
        """Get preview samples of processed spintax."""
        if count <= 0:
            return []
        # Prefer native for multi-sample previews (force skips small-batch skip).
        native_texts = spintax_expand_batch(text, count, seed=self.seed, force=True)
        if native_texts is not None:
            return native_texts
        return [self.process(text).text for _ in range(count)]

    def get_variants_count(self, text: str) -> int:
        """Get total number of possible variants."""
        result = self.process(text)
        return result.variants_count

    def validate_spintax(self, text: str) -> Dict[str, Any]:
        """Validate spintax syntax."""
        errors = []
        warnings = []

        # Check for unmatched braces
        open_braces = text.count("{")
        close_braces = text.count("}")

        if open_braces != close_braces:
            errors.append(f"Unmatched braces: {open_braces} open, {close_braces} close")

        # Check for empty variants
        patterns = self._find_spintax_patterns(text)
        for pattern in patterns:
            variants = self._extract_variants(pattern)
            if not variants:
                errors.append(f"Empty spintax pattern: {pattern}")
            elif any(not v.strip() for v in variants):
                errors.append(f"Empty variant in pattern: {pattern}")

        # Check for nested patterns (not supported)
        brace_depth = 0
        has_nested_spintax = False
        for char in text:
            if char == "{":
                brace_depth += 1
                if brace_depth > 1:
                    has_nested_spintax = True
            elif char == "}":
                brace_depth = max(0, brace_depth - 1)

        if has_nested_spintax:
            message = "Nested spintax not supported"
            errors.append(message)
            warnings.append(message)

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "patterns_count": len(patterns),
            "variants_count": self.get_variants_count(text),
        }
