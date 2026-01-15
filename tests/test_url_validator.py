"""Unit tests for URL validator."""
import pytest

from src.scraper.url_validator import validate_url, validate_url_strict, URLValidationError


class TestValidateURL:
    """Tests for validate_url function."""

    def test_valid_https_url(self):
        """Test that valid HTTPS URLs are accepted."""
        is_valid, error = validate_url("https://example.com/blog")
        assert is_valid is True
        assert error == ""

    def test_valid_http_url(self):
        """Test that valid HTTP URLs are accepted."""
        is_valid, error = validate_url("http://example.com/blog")
        assert is_valid is True
        assert error == ""

    def test_url_with_path(self):
        """Test URL with complex path."""
        is_valid, error = validate_url("https://blog.example.com/posts/2024/01/article")
        assert is_valid is True
        assert error == ""

    def test_url_with_query_params(self):
        """Test URL with query parameters."""
        is_valid, error = validate_url("https://example.com/search?q=test&page=1")
        assert is_valid is True
        assert error == ""

    def test_url_with_port(self):
        """Test URL with explicit port."""
        is_valid, error = validate_url("https://example.com:8443/api")
        assert is_valid is True
        assert error == ""

    def test_url_with_subdomain(self):
        """Test URL with subdomain."""
        is_valid, error = validate_url("https://api.blog.example.com/posts")
        assert is_valid is True
        assert error == ""

    def test_reject_file_scheme(self):
        """Test that file:// URLs are rejected (SSRF prevention)."""
        is_valid, error = validate_url("file:///etc/passwd")
        assert is_valid is False
        assert "file" in error.lower()

    def test_reject_javascript_scheme(self):
        """Test that javascript: URLs are rejected (XSS prevention)."""
        is_valid, error = validate_url("javascript:alert('xss')")
        assert is_valid is False
        assert "javascript" in error.lower()

    def test_reject_data_scheme(self):
        """Test that data: URLs are rejected."""
        is_valid, error = validate_url("data:text/html,<h1>Test</h1>")
        assert is_valid is False
        assert "data" in error.lower()

    def test_reject_vbscript_scheme(self):
        """Test that vbscript: URLs are rejected."""
        is_valid, error = validate_url("vbscript:msgbox('test')")
        assert is_valid is False
        assert "vbscript" in error.lower()

    def test_reject_localhost_explicit(self):
        """Test that localhost URLs are rejected (SSRF prevention)."""
        is_valid, error = validate_url("http://localhost:8000/admin")
        assert is_valid is False
        assert "localhost" in error.lower()

    def test_reject_localhost_uppercase(self):
        """Test that LOCALHOST (case-insensitive) is rejected."""
        is_valid, error = validate_url("http://LOCALHOST:8000/admin")
        assert is_valid is False
        assert "localhost" in error.lower()

    def test_reject_127_0_0_1(self):
        """Test that 127.0.0.1 is rejected (SSRF prevention)."""
        is_valid, error = validate_url("http://127.0.0.1:8000/admin")
        assert is_valid is False
        assert "127" in error or "localhost" in error.lower()

    def test_reject_0_0_0_0(self):
        """Test that 0.0.0.0 is rejected."""
        is_valid, error = validate_url("http://0.0.0.0:8000/admin")
        assert is_valid is False
        assert "0.0.0.0" in error or "internal" in error.lower()

    def test_reject_ipv6_localhost(self):
        """Test that ::1 (IPv6 localhost) is rejected."""
        is_valid, error = validate_url("http://[::1]:8000/admin")
        assert is_valid is False
        assert "::" in error or "localhost" in error.lower()

    def test_reject_private_ip_10(self):
        """Test that 10.0.0.0/8 private IPs are rejected."""
        is_valid, error = validate_url("http://10.0.0.1/admin")
        assert is_valid is False
        assert "private" in error.lower() or "10" in error

    def test_reject_private_ip_192(self):
        """Test that 192.168.0.0/16 private IPs are rejected."""
        is_valid, error = validate_url("http://192.168.1.1/admin")
        assert is_valid is False
        assert "private" in error.lower() or "192.168" in error

    def test_reject_private_ip_172(self):
        """Test that 172.16.0.0/12 private IPs are rejected."""
        is_valid, error = validate_url("http://172.16.0.1/admin")
        assert is_valid is False
        assert "private" in error.lower() or "172" in error

    def test_reject_link_local_ip(self):
        """Test that 169.254.0.0/16 link-local IPs are rejected."""
        is_valid, error = validate_url("http://169.254.1.1/admin")
        assert is_valid is False
        assert "link-local" in error.lower() or "169.254" in error

    def test_reject_ftp_scheme(self):
        """Test that ftp:// URLs are rejected."""
        is_valid, error = validate_url("ftp://ftp.example.com/file.txt")
        assert is_valid is False
        assert "ftp" in error.lower() or "scheme" in error.lower()

    def test_reject_url_encoded_localhost(self):
        """Test that URL-encoded localhost patterns are rejected."""
        # %6c%6f%63%61%6c%68%6f%73%74 = localhost
        is_valid, error = validate_url("http://%6c%6f%63%61%6c%68%6f%73%74:8000/")
        assert is_valid is False
        assert "localhost" in error.lower() or "blocked" in error.lower()

    def test_reject_empty_string(self):
        """Test that empty string is rejected."""
        is_valid, error = validate_url("")
        assert is_valid is False
        assert "empty" in error.lower()

    def test_reject_none(self):
        """Test that None is rejected."""
        is_valid, error = validate_url(None)
        assert is_valid is False
        assert "string" in error.lower()

    def test_reject_too_short(self):
        """Test that very short URLs are rejected."""
        is_valid, error = validate_url("http://a")
        assert is_valid is False
        assert "short" in error.lower()

    def test_reject_too_long(self):
        """Test that very long URLs are rejected."""
        long_url = "https://example.com/" + "a" * 3000
        is_valid, error = validate_url(long_url)
        assert is_valid is False
        assert "length" in error.lower() or "2048" in error

    def test_reject_no_hostname(self):
        """Test that URLs without hostname are rejected."""
        is_valid, error = validate_url("https:///path")
        assert is_valid is False
        assert "hostname" in error.lower() or "netloc" in error.lower()

    def test_reject_invalid_format(self):
        """Test that malformed URLs are rejected."""
        is_valid, error = validate_url("not a url at all")
        assert is_valid is False
        assert "scheme" in error.lower() or "format" in error.lower()

    def test_url_with_fragment(self):
        """Test URL with fragment is accepted."""
        is_valid, error = validate_url("https://example.com/page#section")
        assert is_valid is True
        assert error == ""

    def test_url_with_credentials_accepted(self):
        """Test URL with credentials (not recommended but valid format)."""
        is_valid, error = validate_url("https://user:pass@example.com/api")
        assert is_valid is True
        assert error == ""


class TestValidateURLStrict:
    """Tests for validate_url_strict function."""

    def test_valid_url_returns_url(self):
        """Test that valid URL is returned."""
        url = "https://example.com/blog"
        result = validate_url_strict(url)
        assert result == url

    def test_invalid_url_raises_exception(self):
        """Test that invalid URL raises URLValidationError."""
        with pytest.raises(URLValidationError) as exc_info:
            validate_url_strict("file:///etc/passwd")
        assert "file" in str(exc_info.value).lower()

    def test_localhost_raises_exception(self):
        """Test that localhost URL raises URLValidationError."""
        with pytest.raises(URLValidationError) as exc_info:
            validate_url_strict("http://localhost/admin")
        assert "localhost" in str(exc_info.value).lower()

    def test_private_ip_raises_exception(self):
        """Test that private IP raises URLValidationError."""
        with pytest.raises(URLValidationError) as exc_info:
            validate_url_strict("http://192.168.1.1/admin")
        assert "private" in str(exc_info.value).lower() or "192.168" in str(exc_info.value)
