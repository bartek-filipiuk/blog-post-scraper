"""URL validation module for SSRF prevention.

This module provides security-focused URL validation to prevent
Server-Side Request Forgery (SSRF) attacks by rejecting dangerous
URL schemes and localhost targeting.
"""
from urllib.parse import urlparse
from typing import Tuple

from src.config import settings, get_logger

logger = get_logger(__name__)


class URLValidationError(Exception):
    """Raised when URL validation fails."""
    pass


def validate_url(url: str) -> Tuple[bool, str]:
    """Validate URL for security and format.

    Performs comprehensive validation to prevent SSRF attacks:
    - Only allows http:// and https:// schemes
    - Blocks localhost, 127.0.0.1, 0.0.0.0, ::1
    - Blocks file://, javascript:, data:// schemes
    - Validates URL format

    Args:
        url: URL string to validate

    Returns:
        Tuple[bool, str]: (is_valid, error_message)
        - (True, "") if valid
        - (False, "error message") if invalid

    Examples:
        >>> validate_url("https://example.com/blog")
        (True, "")

        >>> validate_url("file:///etc/passwd")
        (False, "Invalid URL scheme: file. Only http and https are allowed")

        >>> validate_url("http://localhost/admin")
        (False, "Cannot target localhost or internal IPs")
    """
    # Basic validation
    if not url or not isinstance(url, str):
        return False, "URL must be a non-empty string"

    url = url.strip()

    if len(url) < 10:
        return False, "URL is too short to be valid"

    if len(url) > 2048:
        return False, "URL exceeds maximum length of 2048 characters"

    # Parse URL
    try:
        parsed = urlparse(url)
    except Exception as e:
        logger.warning("URL parsing failed", url=url, error=str(e))
        return False, f"Invalid URL format: {str(e)}"

    # Check scheme
    if parsed.scheme not in settings.allowed_schemes:
        logger.warning(
            "Blocked URL with invalid scheme",
            url=url,
            scheme=parsed.scheme,
            allowed=settings.allowed_schemes
        )
        return False, f"Invalid URL scheme: {parsed.scheme}. Only {' and '.join(settings.allowed_schemes)} are allowed"

    # Check for empty netloc (host)
    if not parsed.netloc:
        return False, "URL must have a valid hostname"

    # Extract hostname (remove port if present)
    hostname = parsed.hostname if parsed.hostname else parsed.netloc.split(':')[0]
    hostname_lower = hostname.lower()

    # Check against blocked hosts
    for blocked in settings.blocked_hosts:
        if blocked.lower() in hostname_lower:
            logger.warning(
                "Blocked URL targeting localhost/internal IP",
                url=url,
                hostname=hostname,
                blocked_pattern=blocked
            )
            return False, f"Cannot target localhost or internal IPs (matched: {blocked})"

    # Additional security checks for common SSRF patterns
    ssrf_patterns = [
        'localhost',
        '127.',  # Catches 127.0.0.1, 127.1, etc.
        '0.0.0.0',
        '::1',
        '0:0:0:0:0:0:0:1',  # IPv6 localhost
        '[::]',
        'file://',
        'javascript:',
        'data:',
        'vbscript:',
        'about:',
    ]

    url_lower = url.lower()
    for pattern in ssrf_patterns:
        if pattern in url_lower:
            logger.warning(
                "Blocked URL with SSRF pattern",
                url=url,
                pattern=pattern
            )
            return False, f"URL contains blocked pattern: {pattern}"

    # Check for URL encoding tricks (e.g., %6c%6f%63%61%6c%68%6f%73%74 = localhost)
    try:
        from urllib.parse import unquote
        decoded_url = unquote(url_lower)
        if decoded_url != url_lower:
            # URL was encoded, check decoded version
            for pattern in ssrf_patterns:
                if pattern in decoded_url:
                    logger.warning(
                        "Blocked URL with encoded SSRF pattern",
                        url=url,
                        decoded=decoded_url,
                        pattern=pattern
                    )
                    return False, f"URL contains encoded blocked pattern: {pattern}"
    except Exception:
        pass  # If decoding fails, continue with other checks

    # Check for IP address patterns (private ranges)
    if hostname.replace('.', '').isdigit():  # Looks like IPv4
        parts = hostname.split('.')
        if len(parts) == 4:
            try:
                octets = [int(p) for p in parts]
                # Check for private IP ranges
                if octets[0] == 10:  # 10.0.0.0/8
                    return False, "Cannot target private IP range (10.0.0.0/8)"
                if octets[0] == 172 and 16 <= octets[1] <= 31:  # 172.16.0.0/12
                    return False, "Cannot target private IP range (172.16.0.0/12)"
                if octets[0] == 192 and octets[1] == 168:  # 192.168.0.0/16
                    return False, "Cannot target private IP range (192.168.0.0/16)"
                if octets[0] == 169 and octets[1] == 254:  # 169.254.0.0/16 (link-local)
                    return False, "Cannot target link-local IP range (169.254.0.0/16)"
                if octets[0] == 127:  # 127.0.0.0/8
                    return False, "Cannot target localhost IP range (127.0.0.0/8)"
            except (ValueError, IndexError):
                pass

    logger.info("URL validation passed", url=url, hostname=hostname)
    return True, ""


def validate_url_strict(url: str) -> str:
    """Validate URL and raise exception if invalid.

    Args:
        url: URL string to validate

    Returns:
        str: The validated URL

    Raises:
        URLValidationError: If URL is invalid

    Example:
        >>> validate_url_strict("https://example.com")
        'https://example.com'

        >>> validate_url_strict("file:///etc/passwd")
        URLValidationError: Invalid URL scheme: file
    """
    is_valid, error_message = validate_url(url)
    if not is_valid:
        raise URLValidationError(error_message)
    return url
