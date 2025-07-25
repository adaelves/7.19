"""
Advanced Features Demo - Performance Optimization and Stability
演示高级功能：性能优化和稳定性
"""
import asyncio
import time
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from app.services.advanced_features_service import advanced_features_service
from app.core.utils.memory_manager import memory_manager
from app.core.utils.performance_optimizer import PerformanceTask, TaskPriority
from app.core.utils.exception_recovery import exception_recovery_manager


async def demo_memory_management():
    """演示内存管理功能"""
    print("\n=== 内存管理演示 ===")
    
    # 创建对象池
    def create_download_context():
        return {
            'url': '',
            'headers': {},
            'progress': 0,
            'status': 'pending'
        }
    
    pool = memory_manager.create_object_pool('download_contexts', create_download_context, max_size=10)
    
    # 使用对象池
    contexts = []
    for i in range(5):
        ctx = pool.acquire()
        ctx['url'] = f'https://example.com/video{i}.mp4'
        contexts.append(ctx)
    
    print(f"创建了 {len(contexts)} 个下载上下文")
    
    # 释放对象回池中
    for ctx in contexts:
        pool.release(ctx)
    
    # 获取统计信息
    stats = pool.get_stats()
    print(f"对象池统计: {stats}")
    
    # 测试LRU缓存
    cache = memory_manager.lru_cache
    cache.put('video_metadata_1', {'title': '测试视频1', 'duration': 120})
    cache.put('video_metadata_2', {'title': '测试视频2', 'duration': 180})
    
    metadata = cache.get('video_metadata_1')
    print(f"从缓存获取元数据: {metadata}")
    
    cache_stats = cache.get_stats()
    print(f"缓存统计: {cache_stats}")
    
    # 内存优化
    optimization_result = memory_manager.optimize_memory()
    print(f"内存优化结果: {optimization_result}")


async def demo_connection_pool():
    """演示连接池管理"""
    print("\n=== 连接池管理演示 ===")
    
    from app.core.utils.connection_pool import global_connection_manager
    
    manager = global_connection_manager.get_manager()
    if manager:
        # 模拟获取会话
        session1 = manager.get_session('https://youtube.com')
        session2 = manager.get_session('https://bilibili.com')
        session3 = manager.get_session('https://youtube.com')  # 应该复用
        
        print(f"YouTube会话: {id(session1)}")
        print(f"Bilibili会话: {id(session2)}")
        print(f"YouTube会话(复用): {id(session3)}")
        print(f"会话复用成功: {session1 is session3}")
        
        # 获取连接统计
        stats = manager.get_connection_stats()
        print("连接池统计:")
        for host, host_stats in stats.items():
            print(f"  {host}: {host_stats}")


async def demo_performance_optimizer():
    """演示性能优化器"""
    print("\n=== 性能优化器演示 ===")
    
    from app.core.utils.performance_optimizer import performance_optimizer
    
    # 创建一些测试任务
    def download_task(url, filename):
        """模拟下载任务"""
        time.sleep(0.1)  # 模拟下载时间
        return f"Downloaded {filename} from {url}"
    
    def extract_metadata(url):
        """模拟元数据提取"""
        time.sleep(0.05)
        return f"Metadata for {url}"
    
    # 提交任务
    tasks = []
    for i in range(10):
        # 下载任务
        download_task_obj = PerformanceTask(
            id=f'download_{i}',
            func=download_task,
            args=(f'https://example.com/video{i}.mp4', f'video{i}.mp4'),
            priority=TaskPriority.HIGH if i < 3 else TaskPriority.NORMAL
        )
        performance_optimizer.submit_task(download_task_obj)
        
        # 元数据提取任务
        metadata_task = PerformanceTask(
            id=f'metadata_{i}',
            func=extract_metadata,
            args=(f'https://example.com/video{i}.mp4',),
            priority=TaskPriority.LOW
        )
        performance_optimizer.submit_task(metadata_task)
    
    # 等待一段时间让任务处理
    await asyncio.sleep(2)
    
    # 获取统计信息
    stats = performance_optimizer.get_comprehensive_stats()
    print("性能优化器统计:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


async def demo_exception_recovery():
    """演示异常恢复机制"""
    print("\n=== 异常恢复机制演示 ===")
    
    # 模拟可能失败的网络请求
    call_count = 0
    
    async def unreliable_network_request(url):
        nonlocal call_count
        call_count += 1
        
        if call_count <= 2:
            raise ConnectionError(f"网络连接失败 (尝试 {call_count})")
        
        return f"成功获取 {url} 的数据"
    
    try:
        result = await exception_recovery_manager.execute_with_recovery(
            unreliable_network_request, 
            "https://example.com/api/video_info"
        )
        print(f"恢复成功: {result}")
    except Exception as e:
        print(f"最终失败: {e}")
    
    # 获取异常统计
    stats = exception_recovery_manager.get_exception_stats()
    print("异常恢复统计:")
    print(f"  总异常数: {stats['overall_stats']['total_exceptions']}")
    print(f"  恢复成功数: {stats['overall_stats']['recovered_exceptions']}")
    print(f"  恢复失败数: {stats['overall_stats']['unrecovered_exceptions']}")


async def demo_performance_monitoring():
    """演示性能监控"""
    print("\n=== 性能监控演示 ===")
    
    from app.core.utils.performance_monitor import performance_monitor
    
    # 添加自定义指标
    performance_monitor.add_custom_metric('download_speed', 1024.5, 'KB/s', {'category': 'download'})
    performance_monitor.add_custom_metric('active_downloads', 5, 'count', {'category': 'download'})
    performance_monitor.add_custom_metric('queue_size', 15, 'count', {'category': 'queue'})
    
    # 模拟一些活动
    for i in range(5):
        performance_monitor.add_custom_metric('cpu_usage', 45.0 + i * 2, 'percent', {'category': 'system'})
        await asyncio.sleep(0.1)
    
    # 获取指标摘要
    summary = performance_monitor.get_metrics_summary(last_minutes=1)
    print("性能指标摘要:")
    for category, metrics in summary.items():
        print(f"  {category}:")
        for metric_name, stats in metrics.items():
            print(f"    {metric_name}: 最新={stats['latest']}, 平均={stats['avg']:.2f}, 最大={stats['max']}")
    
    # 获取完整性能报告
    report = performance_monitor.get_performance_report()
    print(f"\n系统运行时间: {report['uptime']:.2f} 秒")
    print(f"监控状态: {'活跃' if report['monitoring_active'] else '非活跃'}")


async def demo_integrated_features():
    """演示集成的高级功能"""
    print("\n=== 集成高级功能演示 ===")
    
    # 初始化高级功能服务
    await advanced_features_service.initialize()
    
    # 模拟一个复杂的下载流程
    async def complex_download_workflow(video_url):
        """复杂的下载工作流程"""
        try:
            # 添加性能指标
            advanced_features_service.add_performance_metric(
                'workflow_start', 1, 'count', {'workflow': 'download'}
            )
            
            # 模拟可能失败的操作
            async def extract_info():
                import random
                if random.random() < 0.3:  # 30% 失败率
                    raise ValueError("信息提取失败")
                return {'title': '测试视频', 'duration': 300}
            
            # 使用异常恢复执行
            info = await advanced_features_service.execute_with_recovery(extract_info)
            print(f"提取信息成功: {info}")
            
            # 模拟下载过程
            for progress in [25, 50, 75, 100]:
                advanced_features_service.add_performance_metric(
                    'download_progress', progress, 'percent', {'video': video_url}
                )
                await asyncio.sleep(0.1)
            
            advanced_features_service.add_performance_metric(
                'workflow_complete', 1, 'count', {'workflow': 'download'}
            )
            
            return f"下载完成: {video_url}"
            
        except Exception as e:
            advanced_features_service.add_performance_metric(
                'workflow_error', 1, 'count', {'workflow': 'download'}
            )
            raise
    
    # 执行多个并发下载
    tasks = []
    for i in range(3):
        task = complex_download_workflow(f"https://example.com/video{i}.mp4")
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"下载 {i} 失败: {result}")
        else:
            print(f"下载 {i} 成功: {result}")
    
    # 获取综合状态
    status = advanced_features_service.get_comprehensive_status()
    print("\n高级功能综合状态:")
    print(f"  服务状态: {status['service_status']}")
    
    if 'memory_manager' in status:
        memory_stats = status['memory_manager']['memory_usage']
        print(f"  内存使用: {memory_stats['percent']:.1f}% ({memory_stats['rss'] / 1024 / 1024:.1f} MB)")
    
    if 'performance_optimizer' in status:
        perf_stats = status['performance_optimizer']['optimizer_stats']
        print(f"  任务处理: 提交={perf_stats['tasks_submitted']}, 完成={perf_stats['tasks_completed']}")


async def main():
    """主演示函数"""
    print("高级功能演示开始")
    print("=" * 50)
    
    try:
        # 初始化服务
        await advanced_features_service.initialize()
        
        # 运行各个演示
        await demo_memory_management()
        await demo_connection_pool()
        await demo_performance_optimizer()
        await demo_exception_recovery()
        await demo_performance_monitoring()
        await demo_integrated_features()
        
        print("\n" + "=" * 50)
        print("所有演示完成!")
        
        # 等待一段时间让后台任务完成
        print("等待后台任务完成...")
        await asyncio.sleep(2)
        
    except Exception as e:
        logger.error(f"演示过程中出现错误: {e}")
    finally:
        # 清理资源
        await advanced_features_service.shutdown()
        print("资源清理完成")


if __name__ == "__main__":
    asyncio.run(main())