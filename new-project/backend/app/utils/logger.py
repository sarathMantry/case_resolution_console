"""
Logging utility with PII redaction for secure logging.
Redacts sensitive information like emails, phone numbers, SSNs, credit cards, etc.
"""
import logging
import re
import json
from typing import Any, Dict, Optional
from functools import wraps
import time

# Configure logging format
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# PII patterns to redact
PII_PATTERNS = {
    'email': (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),
    'phone': (r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]'),
    'ssn': (r'\b\d{3}-\d{2}-\d{4}\b', '[SSN]'),
    'credit_card': (r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b', '[CARD]'),
    'ip_address': (r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '[IP]'),
}

# Sensitive field names to redact (case-insensitive)
SENSITIVE_FIELDS = {
    'password', 'passwd', 'pwd', 'secret', 'token', 'api_key', 'apikey',
    'authorization', 'auth', 'ssn', 'social_security', 'credit_card',
    'card_number', 'cvv', 'pin', 'account_number', 'routing_number',
    'date_of_birth', 'dob', 'drivers_license', 'passport'
}


def setup_logging(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Set up logger with consistent formatting.
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level (default: INFO)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(level)
        formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


def redact_pii(text: str) -> str:
    """
    Redact PII from text using regex patterns.
    
    Args:
        text: Text potentially containing PII
    
    Returns:
        Text with PII redacted
    """
    if not isinstance(text, str):
        text = str(text)
    
    for pattern_name, (pattern, replacement) in PII_PATTERNS.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    
    return text


def redact_dict(data: Dict[str, Any], deep: bool = True) -> Dict[str, Any]:
    """
    Redact sensitive fields in dictionary.
    
    Args:
        data: Dictionary to redact
        deep: Whether to recursively redact nested dicts/lists
    
    Returns:
        Dictionary with sensitive fields redacted
    """
    if not isinstance(data, dict):
        return data
    
    redacted = {}
    for key, value in data.items():
        key_lower = key.lower()
        
        # Check if key is sensitive
        if any(sensitive in key_lower for sensitive in SENSITIVE_FIELDS):
            redacted[key] = '[REDACTED]'
        elif isinstance(value, str):
            # Redact PII in string values
            redacted[key] = redact_pii(value)
        elif deep and isinstance(value, dict):
            # Recursively redact nested dicts
            redacted[key] = redact_dict(value, deep=True)
        elif deep and isinstance(value, list):
            # Redact lists
            redacted[key] = [
                redact_dict(item, deep=True) if isinstance(item, dict)
                else redact_pii(item) if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            redacted[key] = value
    
    return redacted


def safe_log_data(data: Any) -> str:
    """
    Safely convert data to string with PII redaction.
    
    Args:
        data: Data to log (dict, list, str, etc.)
    
    Returns:
        Safe string representation with PII redacted
    """
    if isinstance(data, dict):
        redacted = redact_dict(data)
        return json.dumps(redacted, default=str, indent=2)
    elif isinstance(data, list):
        redacted = [redact_dict(item) if isinstance(item, dict) else item for item in data]
        return json.dumps(redacted, default=str, indent=2)
    elif isinstance(data, str):
        return redact_pii(data)
    else:
        return redact_pii(str(data))


def log_route_call(logger: logging.Logger):
    """
    Decorator to log route function calls with timing and PII redaction.
    
    Usage:
        @log_route_call(logger)
        def my_route(request: Request):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            func_name = func.__name__
            start_time = time.time()
            
            # Log request details (redacted)
            safe_kwargs = redact_dict(kwargs)
            logger.info(f"→ {func_name} called | args={len(args)} kwargs={list(safe_kwargs.keys())}")
            
            try:
                result = await func(*args, **kwargs)
                elapsed = (time.time() - start_time) * 1000
                logger.info(f"← {func_name} completed | {elapsed:.2f}ms")
                return result
            except Exception as e:
                elapsed = (time.time() - start_time) * 1000
                logger.error(f"✗ {func_name} failed | {elapsed:.2f}ms | error={redact_pii(str(e))}")
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            func_name = func.__name__
            start_time = time.time()
            
            # Log request details (redacted)
            safe_kwargs = redact_dict(kwargs)
            logger.info(f"→ {func_name} called | args={len(args)} kwargs={list(safe_kwargs.keys())}")
            
            try:
                result = func(*args, **kwargs)
                elapsed = (time.time() - start_time) * 1000
                logger.info(f"← {func_name} completed | {elapsed:.2f}ms")
                return result
            except Exception as e:
                elapsed = (time.time() - start_time) * 1000
                logger.error(f"✗ {func_name} failed | {elapsed:.2f}ms | error={redact_pii(str(e))}")
                raise
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def log_service_call(logger: logging.Logger, log_result: bool = False):
    """
    Decorator to log service method calls with timing and PII redaction.
    
    Args:
        logger: Logger instance
        log_result: Whether to log the return value (default: False for security)
    
    Usage:
        @log_service_call(logger, log_result=True)
        def my_service_method(self, customer_id: str):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            func_name = func.__name__
            start_time = time.time()
            
            # Log call with redacted parameters
            safe_kwargs = redact_dict(kwargs)
            # Skip 'self' in args
            safe_args = [redact_pii(str(arg)) for arg in args[1:]] if len(args) > 1 else []
            
            logger.debug(f"→ {func_name} | args={safe_args} kwargs={safe_kwargs}")
            
            try:
                result = func(*args, **kwargs)
                elapsed = (time.time() - start_time) * 1000
                
                if log_result and result is not None:
                    safe_result = safe_log_data(result) if isinstance(result, (dict, list)) else redact_pii(str(result))
                    logger.debug(f"← {func_name} | {elapsed:.2f}ms | result={safe_result}")
                else:
                    logger.debug(f"← {func_name} | {elapsed:.2f}ms")
                
                return result
            except Exception as e:
                elapsed = (time.time() - start_time) * 1000
                logger.error(f"✗ {func_name} | {elapsed:.2f}ms | error={redact_pii(str(e))}", exc_info=True)
                raise
        
        return wrapper
    
    return decorator


# Create a default application logger
app_logger = setup_logging("app", level=logging.INFO)


# Example usage and testing
if __name__ == "__main__":
    # Test logging setup
    logger = setup_logging("test", level=logging.DEBUG)
    
    # Test PII redaction
    test_text = "Contact John at john.doe@example.com or call 555-123-4567. SSN: 123-45-6789"
    logger.info(f"Original: {test_text}")
    logger.info(f"Redacted: {redact_pii(test_text)}")
    
    # Test dict redaction
    test_data = {
        "name": "John Doe",
        "email": "john.doe@example.com",
        "phone": "555-123-4567",
        "password": "secret123",
        "address": "123 Main St",
        "ssn": "123-45-6789",
        "metadata": {
            "ip": "192.168.1.1",
            "token": "abc123xyz"
        }
    }
    logger.info(f"Redacted data:\n{safe_log_data(test_data)}")
