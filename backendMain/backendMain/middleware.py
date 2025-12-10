"""
Production Middleware for AeroOps Backend
"""
import time
import logging
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(MiddlewareMixin):
    """Log all requests with timing and status codes"""
    
    def process_request(self, request):
        request.start_time = time.time()
        return None
    
    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            log_data = {
                'method': request.method,
                'path': request.path,
                'status': response.status_code,
                'duration_ms': round(duration * 1000, 2),
                'user': request.user.username if request.user.is_authenticated else 'anonymous',
                'ip': self.get_client_ip(request),
            }
            
            if response.status_code >= 500:
                logger.error(f"Request failed: {log_data}")
            elif response.status_code >= 400:
                logger.warning(f"Client error: {log_data}")
            elif duration > 1.0:  # Slow request (>1s)
                logger.warning(f"Slow request: {log_data}")
            else:
                logger.info(f"Request: {log_data}")
        
        return response
    
    @staticmethod
    def get_client_ip(request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class RateLimitMiddleware(MiddlewareMixin):
    """Rate limiting middleware using cache"""
    
    def process_request(self, request):
        # Skip rate limiting for admin and static files
        if request.path.startswith('/admin/') or request.path.startswith('/static/'):
            return None
        
        # Get rate limit configuration
        from django.conf import settings
        if not getattr(settings, 'RATELIMIT_ENABLE', False):
            return None
        
        # Get identifier (user or IP)
        if request.user.is_authenticated:
            identifier = f"user:{request.user.id}"
            limit_per_minute = 60
            limit_per_hour = 1000
        else:
            identifier = f"ip:{RequestLoggingMiddleware.get_client_ip(request)}"
            limit_per_minute = 30
            limit_per_hour = 500
        
        # Check minute limit
        minute_key = f"ratelimit:minute:{identifier}"
        minute_count = cache.get(minute_key, 0)
        
        if minute_count >= limit_per_minute:
            logger.warning(f"Rate limit exceeded (minute): {identifier}")
            return JsonResponse({
                'error': 'Rate limit exceeded',
                'detail': f'Maximum {limit_per_minute} requests per minute allowed'
            }, status=429)
        
        # Check hour limit
        hour_key = f"ratelimit:hour:{identifier}"
        hour_count = cache.get(hour_key, 0)
        
        if hour_count >= limit_per_hour:
            logger.warning(f"Rate limit exceeded (hour): {identifier}")
            return JsonResponse({
                'error': 'Rate limit exceeded',
                'detail': f'Maximum {limit_per_hour} requests per hour allowed'
            }, status=429)
        
        # Increment counters
        cache.set(minute_key, minute_count + 1, 60)  # 60 seconds
        cache.set(hour_key, hour_count + 1, 3600)  # 1 hour
        
        return None


class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """Monitor and log slow database queries"""
    
    def process_request(self, request):
        request.start_time = time.time()
        return None
    
    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            # Log slow requests
            if duration > 2.0:  # Requests taking more than 2 seconds
                from django.db import connection
                num_queries = len(connection.queries)
                
                logger.warning(
                    f"Slow request detected: {request.method} {request.path} "
                    f"took {duration:.2f}s with {num_queries} database queries"
                )
                
                # Log the slowest queries if DEBUG is on
                from django.conf import settings
                if settings.DEBUG:
                    queries = connection.queries
                    slow_queries = [
                        q for q in queries
                        if float(q.get('time', 0)) > 0.1
                    ]
                    if slow_queries:
                        logger.warning(
                            f"Slow queries: {len(slow_queries)} queries took >0.1s"
                        )
        
        return response


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Add security headers to responses"""
    
    def process_response(self, request, response):
        # Security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Cache control for API responses
        if request.path.startswith('/api/'):
            response['Cache-Control'] = 'no-store, must-revalidate'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        
        return response


class HealthCheckMiddleware(MiddlewareMixin):
    """Quick health check endpoint that bypasses authentication"""
    
    def process_request(self, request):
        if request.path == '/health/':
            from django.http import JsonResponse
            from django.db import connection
            
            try:
                # Quick database check
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                
                return JsonResponse({
                    'status': 'healthy',
                    'timestamp': time.time()
                })
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                return JsonResponse({
                    'status': 'unhealthy',
                    'error': str(e),
                    'timestamp': time.time()
                }, status=503)
        
        return None


class CORSCustomMiddleware(MiddlewareMixin):
    """Custom CORS handling with more control"""
    
    def process_response(self, request, response):
        from django.conf import settings
        
        # Get allowed origins
        allowed_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
        origin = request.META.get('HTTP_ORIGIN', '')
        
        # Check if origin is allowed
        if origin in allowed_origins or getattr(settings, 'CORS_ALLOW_ALL_ORIGINS', False):
            response['Access-Control-Allow-Origin'] = origin
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Authorization, Content-Type, X-Requested-With'
            response['Access-Control-Max-Age'] = '3600'
        
        return response


class ErrorHandlingMiddleware(MiddlewareMixin):
    """Catch and log all unhandled exceptions"""
    
    def process_exception(self, request, exception):
        logger.error(
            f"Unhandled exception in {request.method} {request.path}: {exception}",
            exc_info=True,
            extra={
                'request': request,
                'user': request.user.username if request.user.is_authenticated else 'anonymous'
            }
        )
        
        # Let Django handle the exception normally
        return None
