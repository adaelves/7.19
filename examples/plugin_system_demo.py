"""
Plugin System Demonstration

This script demonstrates the plugin management system functionality including:
- Loading plugins dynamically
- URL routing to appropriate plugins
- Security validation
- Plugin information retrieval
"""
import asyncio
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

from app.core.plugin import PluginManager


async def main():
    """Main demonstration function"""
    print("=== Plugin System Demonstration ===\n")
    
    # Initialize plugin manager
    print("1. Initializing Plugin Manager...")
    plugin_dirs = [
        str(Path(__file__).parent.parent / 'app' / 'plugins')
    ]
    
    manager = PluginManager(
        plugin_directories=plugin_dirs,
        enable_hot_reload=True
    )
    
    try:
        # Initialize the manager
        success = await manager.initialize()
        if not success:
            print("❌ Failed to initialize plugin manager")
            return
        
        print("✅ Plugin manager initialized successfully\n")
        
        # Show loaded plugins
        print("2. Loaded Plugins:")
        plugins = manager.get_all_plugins()
        for name, plugin in plugins.items():
            print(f"   📦 {name}")
            print(f"      - Name: {plugin.info.name}")
            print(f"      - Version: {plugin.info.version}")
            print(f"      - Domains: {', '.join(plugin.supported_domains)}")
            print(f"      - Status: {plugin.status.value}")
            print(f"      - Usage Count: {plugin.usage_count}")
            print()
        
        # Show supported domains
        print("3. Supported Domains:")
        domains = manager.get_supported_domains()
        for domain in domains:
            print(f"   🌐 {domain}")
        print()
        
        # Show supported platforms
        print("4. Supported Platforms:")
        platforms = manager.get_supported_platforms()
        for platform in platforms:
            print(f"   🎬 {platform}")
        print()
        
        # Test URL routing
        print("5. URL Routing Tests:")
        test_urls = [
            'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            'https://www.youtube.com/playlist?list=PLrAXtmRdnEQy6nuLMt9H1mu_0Qk0XLhqF',
            'https://example.com/video?v=test123',
            'https://unsupported.com/video',
            'https://www.bilibili.com/video/BV1234567890',
            'https://www.tiktok.com/@user/video/1234567890',
        ]
        
        for url in test_urls:
            print(f"   🔗 Testing: {url}")
            
            # Check if supported
            is_supported = manager.is_url_supported(url)
            print(f"      Supported: {'✅' if is_supported else '❌'}")
            
            if is_supported:
                # Get URL info
                url_info = manager.get_url_info(url)
                if url_info:
                    print(f"      Platform: {url_info.platform}")
                    print(f"      Type: {url_info.url_type.value}")
                    if url_info.video_id:
                        print(f"      Video ID: {url_info.video_id}")
                    if url_info.playlist_id:
                        print(f"      Playlist ID: {url_info.playlist_id}")
                
                # Route to plugin
                routing_result = await manager.route_url(url)
                if routing_result.success:
                    print(f"      Plugin: {routing_result.plugin.name}")
                    print(f"      Confidence: {routing_result.confidence:.2f}")
            
            print()
        
        # Test information extraction (only for example.com)
        print("6. Information Extraction Test:")
        example_url = 'https://example.com/video?v=test123'
        
        if manager.is_url_supported(example_url):
            print(f"   🔗 Extracting info from: {example_url}")
            
            try:
                # Extract basic info
                info = await manager.extract_info(example_url)
                if info:
                    print(f"      Title: {info.get('title', 'N/A')}")
                    print(f"      ID: {info.get('id', 'N/A')}")
                    print(f"      Uploader: {info.get('uploader', 'N/A')}")
                    print(f"      Duration: {info.get('duration', 'N/A')} seconds")
                
                # Extract metadata
                metadata = await manager.get_metadata(example_url)
                if metadata:
                    print(f"      Metadata Title: {metadata.title}")
                    print(f"      Metadata Author: {metadata.author}")
                    print(f"      Quality Options: {len(metadata.quality_options)}")
                    for quality in metadata.quality_options:
                        print(f"        - {quality.quality_id}: {quality.resolution}")
                
            except Exception as e:
                print(f"      ❌ Extraction failed: {e}")
        else:
            print(f"   ❌ URL not supported: {example_url}")
        
        print()
        
        # Show statistics
        print("7. Plugin Manager Statistics:")
        stats = manager.get_statistics()
        print(f"   📊 Total Plugins: {stats.total_plugins}")
        print(f"   📊 Active Plugins: {stats.active_plugins}")
        print(f"   📊 Failed Plugins: {stats.failed_plugins}")
        print(f"   📊 Total Domains: {stats.total_domains}")
        print(f"   📊 Cache Hits: {stats.cache_hits}")
        print(f"   📊 Cache Misses: {stats.cache_misses}")
        print(f"   📊 Security Violations: {stats.security_violations}")
        print()
        
        # Show security violations (if any)
        violations = manager.get_security_violations()
        if violations:
            print("8. Security Violations:")
            for plugin_name, plugin_violations in violations.items():
                print(f"   ⚠️  Plugin: {plugin_name}")
                for violation in plugin_violations:
                    print(f"      - {violation.violation_type.value}: {violation.description}")
                    if violation.line_number:
                        print(f"        Line: {violation.line_number}")
                    print(f"        Severity: {violation.severity}")
        else:
            print("8. Security Violations: None ✅")
        
        print()
        
        # Test plugin usage statistics
        print("9. Plugin Usage Statistics:")
        usage_stats = manager.registry.get_plugin_usage_stats()
        for plugin_name, usage_count in usage_stats.items():
            print(f"   📈 {plugin_name}: {usage_count} uses")
        
        print("\n=== Plugin System Demonstration Complete ===")
        
    except Exception as e:
        print(f"❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Shutdown the manager
        await manager.shutdown()


if __name__ == '__main__':
    asyncio.run(main())