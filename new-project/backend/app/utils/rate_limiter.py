"""Token bucket rate limiter using Redis - 5 requests/second per client."""
import redis
import time
import json
from typing import Optional, Tuple
from fastapi import Request, HTTPException
from starlette.responses import JSONResponse
import os

# Initialize Redis connection
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# Token bucket configuration
RATE_LIMIT = 5  # requests per second
BUCKET_CAPACITY = 5  # maximum burst size
REFILL_RATE = 5  # tokens per second

try:
    redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        decode_responses=False,  # We'll handle encoding ourselves
        socket_connect_timeout=5
    )
    # Test connection
    redis_client.ping()
    print(f"✅ Redis connected at {REDIS_HOST}:{REDIS_PORT}")
    print(f"🪣 Token bucket: {RATE_LIMIT} req/s, capacity: {BUCKET_CAPACITY}")
except Exception as e:
    print(f"⚠️  Redis connection failed: {e}. Rate limiting will be disabled.")
    redis_client = None


def get_redis_client() -> Optional[redis.Redis]:
    """Get Redis client instance."""
    return redis_client


class TokenBucketRateLimiter:
    """Token bucket rate limiter with Redis backend."""
    
    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        capacity: int = BUCKET_CAPACITY,
        refill_rate: float = REFILL_RATE
    ):
        """
        Initialize token bucket rate limiter.
        
        Args:
            redis_client: Redis client instance
            capacity: Maximum number of tokens in bucket
            refill_rate: Tokens added per second
        """
        self.redis = redis_client or get_redis_client()
        self.capacity = capacity
        self.refill_rate = refill_rate
    
    def _get_client_key(self, client_id: str) -> str:
        """Generate Redis key for client."""
        return f"rate_limit:token_bucket:{client_id}"
    
    def check_rate_limit(self, client_id: str) -> Tuple[bool, dict]:
        """
        Check if request is allowed using token bucket algorithm.
        
        Args:
            client_id: Unique client identifier (usually IP address)
        
        Returns:
            Tuple of (is_allowed, info_dict)
            info_dict contains: allowed, remaining, retry_after, limit
        """
        if not self.redis:
            # If Redis unavailable, allow all requests
            return True, {
                "allowed": True,
                "remaining": self.capacity,
                "retry_after": 0,
                "limit": self.refill_rate
            }
        
        try:
            key = self._get_client_key(client_id)
            current_time = time.time()
            
            # Use Lua script for atomic token bucket operations
            lua_script = """
            local key = KEYS[1]
            local capacity = tonumber(ARGV[1])
            local refill_rate = tonumber(ARGV[2])
            local current_time = tonumber(ARGV[3])
            local requested_tokens = tonumber(ARGV[4])
            
            -- Get current bucket state
            local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
            local tokens = tonumber(bucket[1])
            local last_refill = tonumber(bucket[2])
            
            -- Initialize if bucket doesn't exist
            if tokens == nil then
                tokens = capacity
                last_refill = current_time
            end
            
            -- Calculate tokens to add based on time elapsed
            local time_elapsed = current_time - last_refill
            local tokens_to_add = time_elapsed * refill_rate
            tokens = math.min(capacity, tokens + tokens_to_add)
            
            -- Check if request can be fulfilled
            local allowed = 0
            local retry_after = 0
            
            if tokens >= requested_tokens then
                tokens = tokens - requested_tokens
                allowed = 1
            else
                -- Calculate time needed to refill enough tokens
                retry_after = math.ceil((requested_tokens - tokens) / refill_rate)
            end
            
            -- Update bucket state
            redis.call('HMSET', key, 'tokens', tokens, 'last_refill', current_time)
            redis.call('EXPIRE', key, 60)  -- Expire after 60 seconds of inactivity
            
            return {allowed, math.floor(tokens), retry_after}
            """
            
            # Execute Lua script
            result = self.redis.eval(
                lua_script,
                1,  # number of keys
                key,  # KEYS[1]
                self.capacity,  # ARGV[1]
                self.refill_rate,  # ARGV[2]
                current_time,  # ARGV[3]
                1  # ARGV[4] - requested tokens (always 1 per request)
            )
            
            allowed = bool(result[0])
            remaining = int(result[1])
            retry_after = int(result[2])
            
            info = {
                "allowed": allowed,
                "remaining": remaining,
                "retry_after": retry_after,
                "limit": self.refill_rate
            }
            
            return allowed, info
            
        except Exception as e:
            print(f"❌ Rate limiter error: {e}")
            # On error, allow request (fail-open)
            return True, {
                "allowed": True,
                "remaining": self.capacity,
                "retry_after": 0,
                "limit": self.refill_rate
            }
    
    def reset_limit(self, client_id: str) -> bool:
        """Reset rate limit for a specific client."""
        if not self.redis:
            return False
        
        try:
            key = self._get_client_key(client_id)
            self.redis.delete(key)
            return True
        except Exception as e:
            print(f"❌ Error resetting rate limit: {e}")
            return False


# Global rate limiter instance
rate_limiter = TokenBucketRateLimiter(redis_client)


async def rate_limit_middleware(request: Request, call_next):
    """
    FastAPI middleware to enforce rate limiting with token bucket.
    
    Returns 429 with Retry-After header if rate limit exceeded.
    """
    # Get client identifier (IP address)
    client_id = request.client.host if request.client else "unknown"
    
    # Check rate limit
    is_allowed, info = rate_limiter.check_rate_limit(client_id)
    
    if not is_allowed:
        # Rate limit exceeded - return 429 JSONResponse with Retry-After header
        return JSONResponse(
            status_code=429,
            content={
                "detail": {
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {RATE_LIMIT} requests per second allowed",
                    "limit": info["limit"],
                    "remaining": info["remaining"],
                    "retry_after": info["retry_after"]
                }
            },
            headers={
                "Retry-After": str(info["retry_after"]),
                "X-RateLimit-Limit": str(int(info["limit"])),
                "X-RateLimit-Remaining": str(info["remaining"])
            }
        )
    
    # Add rate limit headers to response
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(int(info["limit"]))
    response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
    
    return response
