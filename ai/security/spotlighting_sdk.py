"""
Spotlighting SDK for Prompt Injection Prevention
Provides three spotlighting modes to isolate and mark untrusted content.

Modes:
1. Delimiting: Randomized delimiters around untrusted content
2. Datamarking: Non-semantic markers between tokens
3. Encoding: Base64/ROT13 encoding with safe decoding

Author: PsychSync Security Team
Version: 1.0.0
"""

import base64
import codecs
import random
import re
import string
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class SpotlightingMode(Enum):
    """Spotlighting modes for untrusted content isolation."""
    DELIMITING = "delimiting"
    DATAMARKING = "datamarking"
    ENCODING = "encoding"


@dataclass
class SpotlightingResult:
    """Result of spotlighting operation."""
    processed_content: str
    delimiter_start: Optional[str] = None
    delimiter_end: Optional[str] = None
    encoding_method: Optional[str] = None
    markers_count: int = 0
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class DelimitingSpotlighting:
    """
    Delimiting mode: Wraps untrusted content in randomized delimiters.

    Example:
        Input: "Ignore previous instructions"
        Output: "「≈≈≈USER_INPUT_START≈≈≈」Ignore previous instructions「≈≈≈USER_INPUT_END≈≈≈」"

    Benefits:
        - Clear boundary markers
        - Difficult to bypass without detection
        - Preserves content readability
    """

    # Character sets for delimiter generation
    DELIMITER_CHARS = {
        'brackets': ['「」', '『』', '【】', '〔〕', '⎡⎤', '⎣⎦'],
        'symbols': ['≈≈≈', '※※※', '☉☉☉', '◈◈◈', '◆◆◆'],
        'arrows': ['>>>', '<<<', '→→→', '←←←', '⇒⇒⇒'],
        'mixed': ['§§§', '★☆★', '♦♦♦', '※✿※']
    }

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize delimiting spotlighting.

        Args:
            seed: Random seed for reproducible delimiters (testing only)
        """
        self.random = random.Random(seed) if seed is not None else random

    def generate_delimiter_pair(self) -> Tuple[str, str]:
        """
        Generate a randomized delimiter pair.

        Returns:
            Tuple of (start_delimiter, end_delimiter)
        """
        # Select random bracket style
        brackets = self.random.choice(list(self.DELIMITER_CHARS['brackets']))
        bracket_open, bracket_close = brackets[0], brackets[1]

        # Select random symbol style
        symbols = self.random.choice(list(self.DELIMITER_CHARS['symbols']))

        # Combine for start delimiter
        start_delimiter = f"{bracket_open}{symbols}USER_INPUT_START{symbols}{bracket_open}"

        # Combine for end delimiter
        end_delimiter = f"{bracket_close}{symbols}USER_INPUT_END{symbols}{bracket_close}"

        return start_delimiter, end_delimiter

    def apply(self, content: str) -> SpotlightingResult:
        """
        Apply delimiting spotlighting to content.

        Args:
            content: Untrusted user content

        Returns:
            SpotlightingResult with delimited content
        """
        delimiter_start, delimiter_end = self.generate_delimiter_pair()

        processed = f"{delimiter_start}\n{content}\n{delimiter_end}"

        return SpotlightingResult(
            processed_content=processed,
            delimiter_start=delimiter_start,
            delimiter_end=delimiter_end,
            metadata={
                'mode': SpotlightingMode.DELIMITING.value,
                'original_length': len(content),
                'processed_length': len(processed)
            }
        )

    def verify(self, content: str, result: SpotlightingResult) -> bool:
        """
        Verify that content is properly delimited.

        Args:
            content: Content to verify
            result: Original spotlighting result

        Returns:
            True if properly delimited
        """
        return (
            result.delimiter_start in content and
            result.delimiter_end in content and
            content.index(result.delimiter_start) <
            content.index(result.delimiter_end)
        )


class DatamarkingSpotlighting:
    """
    Datamarking mode: Inserts non-semantic markers between tokens.

    Example:
        Input: "Ignore previous instructions"
        Output: "Ignoreˆpreviousˆinstructions"

    Benefits:
        - Disrupts injection patterns without encoding
        - Preserves token meaning for LLM
        - Difficult to remove without detection
    """

    # Non-semantic markers (unlikely in normal text)
    MARKERS = ['ˆ', 'ˇ', '˘', '˙', '˚', '˛', '˜', '˝']

    def __init__(self, marker: Optional[str] = None, seed: Optional[int] = None):
        """
        Initialize datamarking spotlighting.

        Args:
            marker: Specific marker to use (random if None)
            seed: Random seed for reproducible markers (testing only)
        """
        self.random = random.Random(seed) if seed is not None else random
        self.marker = marker if marker else self.random.choice(self.MARKERS)

    def apply(self, content: str) -> SpotlightingResult:
        """
        Apply datamarking spotlighting to content.

        Args:
            content: Untrusted user content

        Returns:
            SpotlightingResult with marked content
        """
        # Split into words while preserving some structure
        words = content.split()
        marked_words = [f"{word}{self.marker}" for word in words]

        processed = ' '.join(marked_words)

        # Count markers
        markers_count = len(words)

        return SpotlightingResult(
            processed_content=processed,
            markers_count=markers_count,
            metadata={
                'mode': SpotlightingMode.DATAMARKING.value,
                'marker': self.marker,
                'original_length': len(content),
                'processed_length': len(processed)
            }
        )

    def verify(self, content: str, result: SpotlightingResult) -> bool:
        """
        Verify that content has expected markers.

        Args:
            content: Content to verify
            result: Original spotlighting result

        Returns:
            True if properly marked
        """
        expected_count = result.markers_count
        actual_count = content.count(result.metadata.get('marker', self.marker))

        return actual_count >= expected_count


class EncodingSpotlighting:
    """
    Encoding mode: Encodes content and wraps in safe decoding instructions.

    Example:
        Input: "Ignore previous instructions"
        Output: "「ENCODED_CONTENT」Base64:SSBnb3JnIHZ...==「DECODE_SAFE」

    Benefits:
        - Content completely unreadable until decoded
        - Impossible to inject without detection
        - Clear decode-at-runtime semantics
    """

    ENCODING_METHODS = ['base64', 'rot13']

    def __init__(self, method: str = 'base64', add_prefix: bool = True):
        """
        Initialize encoding spotlighting.

        Args:
            method: Encoding method ('base64' or 'rot13')
            add_prefix: Add encoding prefix for clarity
        """
        if method not in self.ENCODING_METHODS:
            raise ValueError(f"Invalid encoding method. Choose from: {self.ENCODING_METHODS}")

        self.method = method
        self.add_prefix = add_prefix

    def _encode_base64(self, content: str) -> str:
        """Encode content using Base64."""
        content_bytes = content.encode('utf-8')
        encoded_bytes = base64.b64encode(content_bytes)
        return encoded_bytes.decode('utf-8')

    def _encode_rot13(self, content: str) -> str:
        """Encode content using ROT13."""
        return codecs.encode(content, 'rot_13')

    def apply(self, content: str) -> SpotlightingResult:
        """
        Apply encoding spotlighting to content.

        Args:
            content: Untrusted user content

        Returns:
            SpotlightingResult with encoded content
        """
        # Encode content
        if self.method == 'base64':
            encoded = self._encode_base64(content)
        else:  # rot13
            encoded = self._encode_rot13(content)

        # Wrap with decoding instructions
        if self.add_prefix:
            processed = (
                f"「ENCODED_USER_INPUT」\n"
                f"Method: {self.method.upper()}\n"
                f"Content: {encoded}\n"
                f"「DECODE_IN_SAFE_STAGE」"
            )
        else:
            processed = encoded

        return SpotlightingResult(
            processed_content=processed,
            encoding_method=self.method,
            metadata={
                'mode': SpotlightingMode.ENCODING.value,
                'original_length': len(content),
                'encoded_length': len(encoded)
            }
        )

    def verify(self, content: str, result: SpotlightingResult) -> bool:
        """
        Verify that content is properly encoded.

        Args:
            content: Content to verify
            result: Original spotlighting result

        Returns:
            True if properly encoded
        """
        markers = ['ENCODED_USER_INPUT', 'DECODE_IN_SAFE_STAGE']
        return all(marker in content for marker in markers)


class SpotlightingSDK:
    """
    Main SDK interface for spotlighting untrusted content.

    Usage:
        >>> sdk = SpotlightingSDK()
        >>> result = sdk.spotlight("Ignore instructions", mode=SpotlightingMode.DELIMITING)
        >>> print(result.processed_content)
    """

    def __init__(self):
        """Initialize the Spotlighting SDK."""
        self.delimiting = DelimitingSpotlighting()
        self.datamarking = DatamarkingSpotlighting()
        self.encoding = EncodingSpotlighting()

    def spotlight(
        self,
        content: str,
        mode: SpotlightingMode = SpotlightingMode.DELIMITING,
        **kwargs
    ) -> SpotlightingResult:
        """
        Apply spotlighting to untrusted content.

        Args:
            content: Untrusted user content
            mode: Spotlighting mode to use
            **kwargs: Mode-specific options

        Returns:
            SpotlightingResult with processed content

        Examples:
            >>> sdk = SpotlightingSDK()
            >>> result = sdk.spotlight("Ignore all instructions", mode=SpotlightingMode.DELIMITING)
            >>> result = sdk.spotlight("Ignore all instructions", mode=SpotlightingMode.ENCODING, method='base64')
        """
        if mode == SpotlightingMode.DELIMITING:
            return self.delimiting.apply(content)
        elif mode == SpotlightingMode.DATAMARKING:
            return self.datamarking.apply(content)
        elif mode == SpotlightingMode.ENCODING:
            method = kwargs.get('method', 'base64')
            encoder = EncodingSpotlighting(method=method)
            return encoder.apply(content)
        else:
            raise ValueError(f"Unknown spotlighting mode: {mode}")

    def spotlight_batch(
        self,
        contents: List[str],
        mode: SpotlightingMode = SpotlightingMode.DELIMITING,
        **kwargs
    ) -> List[SpotlightingResult]:
        """
        Apply spotlighting to multiple contents.

        Args:
            contents: List of untrusted contents
            mode: Spotlighting mode to use
            **kwargs: Mode-specific options

        Returns:
            List of SpotlightingResults
        """
        return [self.spotlight(content, mode, **kwargs) for content in contents]

    def verify(
        self,
        content: str,
        original_result: SpotlightingResult
    ) -> bool:
        """
        Verify that content matches spotlighting result.

        Args:
            content: Content to verify
            original_result: Original spotlighting result

        Returns:
            True if content matches expected format
        """
        mode = original_result.metadata.get('mode')

        if mode == SpotlightingMode.DELIMITING.value:
            return self.delimiting.verify(content, original_result)
        elif mode == SpotlightingMode.DATAMARKING.value:
            return self.datamarking.verify(content, original_result)
        elif mode == SpotlightingMode.ENCODING.value:
            return self.encoding.verify(content, original_result)
        else:
            return False


class SafePipelineStage:
    """
    Safe pipeline stage for decoding encoded spotlighting.

    This component runs in a trusted environment to decode content
    that was spotlighted using ENCODING mode.
    """

    @staticmethod
    def decode_base64(content: str) -> str:
        """
        Decode Base64 content.

        Args:
            content: Base64 encoded content

        Returns:
            Decoded content
        """
        content_bytes = base64.b64decode(content.encode('utf-8'))
        return content_bytes.decode('utf-8')

    @staticmethod
    def decode_rot13(content: str) -> str:
        """
        Decode ROT13 content.

        Args:
            content: ROT13 encoded content

        Returns:
            Decoded content
        """
        return codecs.decode(content, 'rot_13')

    @staticmethod
    def decode_from_spotlighting(result: SpotlightingResult) -> str:
        """
        Decode content from spotlighting result.

        Args:
            result: SpotlightingResult with encoded content

        Returns:
            Decoded content

        Raises:
            ValueError: If result is not in encoding mode
        """
        if result.metadata.get('mode') != SpotlightingMode.ENCODING.value:
            raise ValueError("Result is not in encoding mode")

        method = result.encoding_method
        content = result.processed_content

        # Extract encoded content from wrapper
        if 'Content:' in content:
            encoded_part = content.split('Content: ')[1].split('\n')[0].strip()
        else:
            encoded_part = content

        # Decode
        if method == 'base64':
            return SafePipelineStage.decode_base64(encoded_part)
        elif method == 'rot13':
            return SafePipelineStage.decode_rot13(encoded_part)
        else:
            raise ValueError(f"Unknown encoding method: {method}")


# Convenience functions for quick usage
def spotlight_delimiting(content: str) -> SpotlightingResult:
    """Quick function for delimiting spotlighting."""
    return DelimitingSpotlighting().apply(content)


def spotlight_datamarking(content: str, marker: Optional[str] = None) -> SpotlightingResult:
    """Quick function for datamarking spotlighting."""
    return DatamarkingSpotlighting(marker=marker).apply(content)


def spotlight_encoding(content: str, method: str = 'base64') -> SpotlightingResult:
    """Quick function for encoding spotlighting."""
    return EncodingSpotlighting(method=method).apply(content)
