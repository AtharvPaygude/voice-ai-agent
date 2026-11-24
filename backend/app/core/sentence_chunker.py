"""
Sentence chunking and token streaming utilities for Aura AI.
Splits token streams at natural sentence boundaries (. ? ! ।) and length thresholds
while detecting and buffering tool-call blocks so internal syntax is never spoken or displayed.
"""
import re
from typing import AsyncGenerator, Tuple, Optional

# Sentence ending punctuation in English, Hindi, and Marathi
SENTENCE_ENDINGS = {".", "?", "!", "।", "\n"}

# Robust regex patterns to catch LLM tool-call variations:
# :::TOOL_CALL::: ... :::END_TOOL_CALL:::
# ::TOOL_NAME:: {...} ::END_TOOL_CALL::
# =TOOL_NAME= {...} =END_TOOL_CALL=
# or bare JSON tool blocks emitted without markers
_TOOL_START_PATTERNS = [
    r":::TOOL_CALL:::",                       # canonical triple-colon
    r"::(?:TOOL_CALL|[A-Z_]{3,})(?:::|\s)",   # double-colon variants like ::LOOKUP_CUSTOMER::
    r"=(?:TOOL_CALL|[A-Z_]{3,})(?:=|\s)",     # equals variants like =GET OFFERING DETAILS=
]

_TOOL_END_PATTERNS = [
    r":::END_TOOL_CALL:::",
    r"::END_TOOL_CALL::",
    r"=END_TOOL_CALL=",
    r"\}\s*\)\s*$",   # trailing }) at end
]

_COMBINED_TOOL_START_RE = re.compile("|".join(_TOOL_START_PATTERNS))
_COMBINED_TOOL_END_RE = re.compile("|".join(_TOOL_END_PATTERNS))

# Regex to scrub any residual tool syntax from text that will be spoken
_TOOL_SCRUB_RE = re.compile(
    r"(?:"
    r":::?(?:TOOL_CALL|END_TOOL_CALL|[A-Z_]{3,}):::?"            # ::MARKER:: or :::MARKER:::
    r"|=(?:TOOL_CALL|END_TOOL_CALL|GET[_ ]OFFERING[_ ]DETAILS|[A-Z_]{3,})=?"  # =MARKER= variants
    r"|::(?:[A-Z_]{3,})::"                                        # ::NAME::
    r")"
)

_JSON_TOOL_BLOCK_RE = re.compile(
    r'\{\s*"tool"\s*:\s*"[^"]+"\s*,\s*"parameters"\s*:\s*\{[^}]*\}\s*\}',
    re.DOTALL,
)

def sanitize_spoken_text(text: str) -> str:
    """Remove any tool-call syntax or JSON tool blocks from text before speaking."""
    # Remove tool markers
    cleaned = _TOOL_SCRUB_RE.sub("", text)
    # Remove JSON tool blocks
    cleaned = _JSON_TOOL_BLOCK_RE.sub("", cleaned)
    # Remove stray colons or equals at word boundaries from marker remnants
    cleaned = re.sub(r'\b::+\b', ' ', cleaned)
    cleaned = re.sub(r'\b=+\b', ' ', cleaned)
    # Collapse whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def _extract_tool_json(raw: str) -> Optional[str]:
    """Extract the JSON tool call from a raw tool block string."""
    # Try canonical format first
    match = re.search(r":::TOOL_CALL:::\s*(.*?)\s*:::END_TOOL_CALL:::", raw, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Try to find bare JSON with "tool" key
    match = _JSON_TOOL_BLOCK_RE.search(raw)
    if match:
        return match.group(0).strip()
    return None


async def chunk_into_sentences(
    token_stream: AsyncGenerator[str, None]
) -> AsyncGenerator[Tuple[str, Optional[str]], None]:
    """
    Consumes a stream of tokens and yields (spoken_sentence, tool_call_block).
    - If a sentence is complete and not inside a tool call, yields (sentence, None).
    - If a tool call is completed, yields (None, tool_call_json_string).
    - Ensures tool syntax is never emitted as spoken text.
    """
    buffer = ""
    in_tool_block = False
    tool_buffer = ""

    async for token in token_stream:
        buffer += token

        # Check if tool block starts (robust detection)
        if not in_tool_block and _COMBINED_TOOL_START_RE.search(buffer):
            # Split at the tool marker
            match = _COMBINED_TOOL_START_RE.search(buffer)
            pre_tool_text = buffer[:match.start()].strip()
            pre_tool_text = sanitize_spoken_text(pre_tool_text)
            if pre_tool_text and len(pre_tool_text.split()) >= 2:
                yield (pre_tool_text, None)
            in_tool_block = True
            tool_buffer = buffer[match.start():]
            buffer = ""
            continue

        # Also catch cases where LLM emits bare JSON tool object without any markers
        if not in_tool_block and '{"tool"' in buffer and '"parameters"' in buffer:
            json_match = _JSON_TOOL_BLOCK_RE.search(buffer)
            if json_match:
                pre_tool_text = buffer[:json_match.start()].strip()
                pre_tool_text = sanitize_spoken_text(pre_tool_text)
                if pre_tool_text and len(pre_tool_text.split()) >= 2:
                    yield (pre_tool_text, None)
                tool_json = json_match.group(0).strip()
                yield ("", tool_json)
                buffer = buffer[json_match.end():]
                buffer = sanitize_spoken_text(buffer)
                continue

        if in_tool_block:
            tool_buffer += token
            # Check for end markers OR a complete JSON block
            if _COMBINED_TOOL_END_RE.search(tool_buffer) or (
                tool_buffer.count("{") >= 2 and tool_buffer.count("}") >= 2 and tool_buffer.count("{") == tool_buffer.count("}")
            ):
                tool_json = _extract_tool_json(tool_buffer)
                if tool_json:
                    yield ("", tool_json)
                in_tool_block = False
                # Keep whatever came after the end marker
                for end_pat in [r":::END_TOOL_CALL:::", r"::END_TOOL_CALL::", r"=END_TOOL_CALL="]:
                    end_match = re.search(end_pat, tool_buffer)
                    if end_match:
                        remainder = tool_buffer[end_match.end():]
                        buffer = sanitize_spoken_text(remainder)
                        tool_buffer = ""
                        break
                else:
                    # No end marker found but JSON complete — take remainder after last }
                    last_brace = tool_buffer.rfind("}")
                    if last_brace >= 0:
                        buffer = sanitize_spoken_text(tool_buffer[last_brace+1:])
                    else:
                        buffer = ""
                    tool_buffer = ""
            continue

        # Check for sentence endings outside tool block
        if any(char in buffer for char in SENTENCE_ENDINGS):
            match = re.search(r"([^.?!।\n]+[.?!।\n]+)(\s+.*)?$", buffer, re.DOTALL)
            if match:
                sentence = sanitize_spoken_text(match.group(1))
                remainder = match.group(2) if match.group(2) else ""
                if sentence and len(sentence.split()) >= 3:
                    yield (sentence, None)
                    buffer = remainder.lstrip()

    # Flush remaining text in buffer
    remaining_clean = sanitize_spoken_text(buffer)
    if remaining_clean and not in_tool_block and len(remaining_clean.split()) >= 2:
        yield (remaining_clean, None)
