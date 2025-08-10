from django.core.management.base import BaseCommand
from django.core.cache import cache
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Check Redis connection and health'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed Redis information',
        )

    def handle(self, *args, **options):
        try:
            # Test cache connection
            test_key = 'health_check_test'
            test_value = 'redis_connection_ok'
            
            self.stdout.write('🔍 Testing Redis connection...')
            
            # Set and get test value
            cache.set(test_key, test_value, 30)
            result = cache.get(test_key)
            
            if result == test_value:
                self.stdout.write(
                    self.style.SUCCESS('✅ Redis connection successful')
                )
                
                # Clean up test key
                cache.delete(test_key)
                
                if options['verbose']:
                    try:
                        # Get detailed Redis info
                        from django_redis import get_redis_connection
                        redis_conn = get_redis_connection("default")
                        info = redis_conn.info()
                        
                        self.stdout.write('\n📊 Redis Server Information:')
                        self.stdout.write(f"  Version: {info.get('redis_version', 'Unknown')}")
                        self.stdout.write(f"  Memory Used: {info.get('used_memory_human', 'Unknown')}")
                        self.stdout.write(f"  Connected Clients: {info.get('connected_clients', 'Unknown')}")
                        self.stdout.write(f"  Total Connections: {info.get('total_connections_received', 'Unknown')}")
                        self.stdout.write(f"  Keyspace Hits: {info.get('keyspace_hits', 'Unknown')}")
                        self.stdout.write(f"  Keyspace Misses: {info.get('keyspace_misses', 'Unknown')}")
                        
                        # Test cache operations
                        self.stdout.write('\n🧪 Testing cache operations:')
                        
                        # Test basic operations
                        cache.set('test_string', 'hello', 60)
                        cache.set('test_number', 42, 60)
                        cache.set('test_list', [1, 2, 3], 60)
                        cache.set('test_dict', {'key': 'value'}, 60)
                        
                        string_result = cache.get('test_string')
                        number_result = cache.get('test_number')
                        list_result = cache.get('test_list')
                        dict_result = cache.get('test_dict')
                        
                        self.stdout.write(f"  String cache: {'✅' if string_result == 'hello' else '❌'}")
                        self.stdout.write(f"  Number cache: {'✅' if number_result == 42 else '❌'}")
                        self.stdout.write(f"  List cache: {'✅' if list_result == [1, 2, 3] else '❌'}")
                        self.stdout.write(f"  Dict cache: {'✅' if dict_result == {'key': 'value'} else '❌'}")
                        
                        # Clean up test data
                        cache.delete_many(['test_string', 'test_number', 'test_list', 'test_dict'])
                        
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(f'⚠️  Could not get detailed Redis info: {e}')
                        )
                
                # Test session backend
                self.stdout.write('\n🔐 Testing session configuration...')
                session_engine = getattr(settings, 'SESSION_ENGINE', 'Unknown')
                self.stdout.write(f"  Session Engine: {session_engine}")
                
                if 'cache' in session_engine:
                    self.stdout.write('  ✅ Using cache-based sessions')
                elif 'db' in session_engine:
                    self.stdout.write('  ✅ Using database-based sessions')
                else:
                    self.stdout.write('  ❓ Unknown session backend')
                
            else:
                self.stdout.write(
                    self.style.ERROR('❌ Redis cache test failed - values do not match')
                )
                self.stdout.write(f"  Expected: {test_value}")
                self.stdout.write(f"  Got: {result}")
                
        except ConnectionError as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Redis connection failed: {e}')
            )
            self.stdout.write('💡 Possible solutions:')
            self.stdout.write('  1. Check if Redis server is running')
            self.stdout.write('  2. Verify REDIS_HOST and REDIS_PORT settings')
            self.stdout.write('  3. Check Redis password (REDIS_PASSWORD)')
            self.stdout.write('  4. Ensure Redis is accessible from this server')
            
        except ImportError as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Redis client not available: {e}')
            )
            self.stdout.write('💡 Install redis and django-redis packages:')
            self.stdout.write('  pip install redis django-redis')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Unexpected error: {e}')
            )
            logger.error(f"Redis health check failed: {e}")
            
        # Show current cache configuration
        self.stdout.write('\n⚙️  Current cache configuration:')
        cache_config = getattr(settings, 'CACHES', {}).get('default', {})
        backend = cache_config.get('BACKEND', 'Unknown')
        location = cache_config.get('LOCATION', 'Unknown')
        
        self.stdout.write(f"  Backend: {backend}")
        self.stdout.write(f"  Location: {location}")
        
        if 'redis' in backend.lower():
            self.stdout.write('  🚀 Using Redis cache backend')
        else:
            self.stdout.write('  📦 Using fallback cache backend')
            self.stdout.write('  ⚠️  Consider installing Redis for better performance')
