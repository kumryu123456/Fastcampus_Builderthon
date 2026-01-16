"""
PII scrubbing utilities for PathPilot.

Constitution Compliance:
- Principle III: User Data Privacy (NON-NEGOTIABLE)
  - No sensitive data in logs, error messages, or stack traces
  - Scrub SSN, phone, email, addresses from logs

T029-T030: PII scrubbing for resume content and logs
"""

import re
from typing import Any, Dict


# PII Regex Patterns
# Constitution III: These patterns detect and scrub sensitive information
EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
PHONE_PATTERN = re.compile(r'''
    (?:
        (?:\+?1[-.]?)?                    # Optional country code
        (?:\([0-9]{3}\)|[0-9]{3})[-.]?    # Area code
        [0-9]{3}[-.]?                     # Prefix
        [0-9]{4}                          # Line number
    )
''', re.VERBOSE)

# SSN patterns: 123-45-6789, 123456789
SSN_PATTERN = re.compile(r'\b\d{3}-?\d{2}-?\d{4}\b')

# Address patterns (basic street addresses)
ADDRESS_PATTERN = re.compile(r'\d+\s+[\w\s]+(?:street|st|avenue|ave|road|rd|boulevard|blvd|lane|ln|drive|dr|court|ct|circle|cir|way)\.?', re.IGNORECASE)

# Credit card patterns (basic)
CREDIT_CARD_PATTERN = re.compile(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b')

# IP addresses
IP_PATTERN = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b')


def scrub_email(text: str, replacement: str = "[EMAIL]") -> str:
    """
    Replace email addresses with placeholder.

    Args:
        text: Input text
        replacement: Replacement string (default: [EMAIL])

    Returns:
        Text with emails scrubbed

    Example:
        >>> scrub_email("Contact john@example.com")
        'Contact [EMAIL]'
    """
    return EMAIL_PATTERN.sub(replacement, text)


def scrub_phone(text: str, replacement: str = "[PHONE]") -> str:
    """
    Replace phone numbers with placeholder.

    Args:
        text: Input text
        replacement: Replacement string (default: [PHONE])

    Returns:
        Text with phones scrubbed

    Example:
        >>> scrub_phone("Call 555-123-4567")
        'Call [PHONE]'
    """
    return PHONE_PATTERN.sub(replacement, text)


def scrub_ssn(text: str, replacement: str = "[SSN]") -> str:
    """
    Replace Social Security Numbers with placeholder.

    Args:
        text: Input text
        replacement: Replacement string (default: [SSN])

    Returns:
        Text with SSNs scrubbed

    Example:
        >>> scrub_ssn("SSN: 123-45-6789")
        'SSN: [SSN]'
    """
    return SSN_PATTERN.sub(replacement, text)


def scrub_address(text: str, replacement: str = "[ADDRESS]") -> str:
    """
    Replace street addresses with placeholder.

    Args:
        text: Input text
        replacement: Replacement string (default: [ADDRESS])

    Returns:
        Text with addresses scrubbed
    """
    return ADDRESS_PATTERN.sub(replacement, text)


def scrub_credit_card(text: str, replacement: str = "[CARD]") -> str:
    """
    Replace credit card numbers with placeholder.

    Args:
        text: Input text
        replacement: Replacement string (default: [CARD])

    Returns:
        Text with card numbers scrubbed
    """
    return CREDIT_CARD_PATTERN.sub(replacement, text)


def scrub_ip_address(text: str, replacement: str = "[IP]") -> str:
    """
    Replace IP addresses with placeholder.

    Args:
        text: Input text
        replacement: Replacement string (default: [IP])

    Returns:
        Text with IP addresses scrubbed
    """
    return IP_PATTERN.sub(replacement, text)


def scrub_all_pii(text: str) -> str:
    """
    Scrub all PII from text in one pass.

    Constitution III: Comprehensive PII removal for logging safety.

    Args:
        text: Input text that may contain PII

    Returns:
        Text with all PII scrubbed

    Example:
        >>> text = "Email: john@test.com, Phone: 555-1234, SSN: 123-45-6789"
        >>> scrub_all_pii(text)
        'Email: [EMAIL], Phone: [PHONE], SSN: [SSN]'
    """
    if not text:
        return text

    # Apply all scrubbers in sequence
    text = scrub_ssn(text)
    text = scrub_credit_card(text)
    text = scrub_phone(text)
    text = scrub_email(text)
    text = scrub_address(text)
    text = scrub_ip_address(text)

    return text


def scrub_dict_pii(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively scrub PII from dictionary values.

    Args:
        data: Dictionary that may contain PII

    Returns:
        Dictionary with PII scrubbed from string values

    Example:
        >>> data = {"email": "test@example.com", "phone": "555-1234"}
        >>> scrub_dict_pii(data)
        {'email': '[EMAIL]', 'phone': '[PHONE]'}
    """
    if not isinstance(data, dict):
        return data

    scrubbed = {}
    for key, value in data.items():
        if isinstance(value, str):
            scrubbed[key] = scrub_all_pii(value)
        elif isinstance(value, dict):
            scrubbed[key] = scrub_dict_pii(value)
        elif isinstance(value, list):
            scrubbed[key] = [
                scrub_all_pii(item) if isinstance(item, str)
                else scrub_dict_pii(item) if isinstance(item, dict)
                else item
                for item in value
            ]
        else:
            scrubbed[key] = value

    return scrubbed


def safe_filename(filename: str) -> bool:
    """
    Check if filename is safe (no PII in the filename itself).

    Args:
        filename: Filename to check

    Returns:
        True if filename appears safe, False if it may contain PII

    Example:
        >>> safe_filename("resume.pdf")
        True
        >>> safe_filename("john.doe@email.com_resume.pdf")
        False
    """
    # Check for email in filename
    if EMAIL_PATTERN.search(filename):
        return False

    # Check for phone in filename
    if PHONE_PATTERN.search(filename):
        return False

    # Check for SSN in filename
    if SSN_PATTERN.search(filename):
        return False

    return True


# Example usage for testing
if __name__ == "__main__":
    # Test email scrubbing
    text = "Contact john.doe@example.com or jane@test.org"
    print(f"Original: {text}")
    print(f"Scrubbed: {scrub_email(text)}\n")

    # Test phone scrubbing
    text = "Call 555-123-4567 or (555) 987-6543"
    print(f"Original: {text}")
    print(f"Scrubbed: {scrub_phone(text)}\n")

    # Test SSN scrubbing
    text = "SSN: 123-45-6789 or 987654321"
    print(f"Original: {text}")
    print(f"Scrubbed: {scrub_ssn(text)}\n")

    # Test all PII scrubbing
    text = """
    John Doe
    Email: john.doe@example.com
    Phone: 555-123-4567
    SSN: 123-45-6789
    Address: 123 Main Street, Anytown
    """
    print(f"Original:\n{text}")
    print(f"Scrubbed:\n{scrub_all_pii(text)}\n")

    # Test dict scrubbing
    data = {
        "name": "John Doe",
        "contact": {
            "email": "john@example.com",
            "phone": "555-1234",
        },
        "ssn": "123-45-6789",
    }
    print(f"Original dict: {data}")
    print(f"Scrubbed dict: {scrub_dict_pii(data)}")
