#!/usr/bin/env python3
"""
下载列表管理功能测试
测试拖拽排序、分组筛选、批量操作、虚拟列表优化、搜索过滤等功能
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from app.ui.components.download_list import (
    DownloadListWidget, TaskFilterWidget, TaskGroupWidget, 
    BatchOperationWidget, VirtualTaskList
)


class TestDownloadListManagement(unittest.TestCase):
    """下载列表管理功能测试"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
            
    def setUp(self):
        """设置测试"""
        self.download_list = DownloadListWidget()
        self.sample_tasks = [
            {
                'url': 'https://www.youtube.com/watch?v=test1',
                'metadata': {
                    'title': 'Test Video 1',
                    'author': 'Test Author 1',
                    'platform': 'YouTube'
                }
            },
            {
                'url': 'https://www.bilibili.com/video/test2',
                'metadata': {
                    'title': 'Test Video 2',
                    'author': 'Test Author 2',
                    'platform': 'B站'
                }
            },
            {
                'url': 'https://www.tiktok.com/test3',
                'metadata': {
                    'title': 'Test Video 3',
                    'author': 'Test Author 3',
                    'platform': '抖音'
                }
            }
        ]
        
    def test_add_task(self):
        """测试添加任务"""
        # 添加任务
        task_id = self.download_list.add_task(
            self.sample_tasks[0]['url'],
            self.sample_tasks[0]['metadata']
        )
        
        # 验证任务已添加
        self.assertIsNotNone(task_id)
        self.assertEqual(self.download_list.get_task_count(), 1)
        self.assertIn(task_id, self.download_list.tasks)
        
        # 验证任务信息
        task_info = self.download_list.tasks[task_id]
        self.assertEqual(task_info['metadata']['url'], self.sample_tasks[0]['url'])
        self.assertEqual(task_info['metadata']['platform'], 'YouTube')
        
    def test_remove_task(self):
        """测试移除任务"""
        # 添加任务
        task_id = self.download_list.add_task(
            self.sample_tasks[0]['url'],
            self.sample_tasks[0]['metadata']
        )
        
        # 移除任务
        self.download_list.remove_task(task_id)
        
        # 验证任务已移除
        self.assertEqual(self.download_list.get_task_count(), 0)
        self.assertNotIn(task_id, self.download_list.tasks)
        
    def test_update_task_status(self):
        """测试更新任务状态"""
        # 添加任务
        task_id = self.download_list.add_task(
            self.sample_tasks[0]['url'],
            self.sample_tasks[0]['metadata']
        )
        
        # 更新状态
        self.download_list.update_task_status(task_id, 'downloading')
        
        # 验证状态已更新
        task_info = self.download_list.tasks[task_id]
        self.assertEqual(task_info['metadata']['status'], 'downloading')
        
    def test_update_task_progress(self):
        """测试更新任务进度"""
        # 添加任务
        task_id = self.download_list.add_task(
            self.sample_tasks[0]['url'],
            self.sample_tasks[0]['metadata']
        )
        
        # 更新进度
        self.download_list.update_task_progress(task_id, 50.0, "2.5 MB/s")
        
        # 验证进度已更新（通过检查卡片的进度值）
        task_card = self.download_list.tasks[task_id]['card']
        self.assertEqual(task_card.progress, 50.0)
        
    def test_search_filter(self):
        """测试搜索筛选功能"""
        # 添加多个任务
        task_ids = []
        for task_data in self.sample_tasks:
            task_id = self.download_list.add_task(task_data['url'], task_data['metadata'])
            task_ids.append(task_id)
            
        # 测试搜索筛选
        filters = {'search': 'Test Video 1', 'status': '全部状态', 'platform': '全部平台'}
        self.download_list.apply_filters(filters)
        
        # 验证筛选结果
        self.assertEqual(len(self.download_list.filtered_tasks), 1)
        
        # 测试平台筛选
        filters = {'search': '', 'status': '全部状态', 'platform': 'YouTube'}
        self.download_list.apply_filters(filters)
        
        # 验证筛选结果
        self.assertEqual(len(self.download_list.filtered_tasks), 1)
        
    def test_status_filter(self):
        """测试状态筛选功能"""
        # 添加任务并设置不同状态
        task_ids = []
        for i, task_data in enumerate(self.sample_tasks):
            task_id = self.download_list.add_task(task_data['url'], task_data['metadata'])
            task_ids.append(task_id)
            
            # 设置不同状态
            if i == 0:
                self.download_list.update_task_status(task_id, 'downloading')
            elif i == 1:
                self.download_list.update_task_status(task_id, 'completed')
            # 第三个保持默认状态 'waiting'
            
        # 测试状态筛选
        filters = {'search': '', 'status': '下载中', 'platform': '全部平台'}
        self.download_list.apply_filters(filters)
        
        # 验证筛选结果
        self.assertEqual(len(self.download_list.filtered_tasks), 1)
        
    def test_grouping_by_status(self):
        """测试按状态分组"""
        # 添加任务并设置不同状态
        task_ids = []
        for i, task_data in enumerate(self.sample_tasks):
            task_id = self.download_list.add_task(task_data['url'], task_data['metadata'])
            task_ids.append(task_id)
            
            # 设置不同状态
            if i == 0:
                self.download_list.update_task_status(task_id, 'downloading')
            elif i == 1:
                self.download_list.update_task_status(task_id, 'completed')
                
        # 应用状态分组
        self.download_list.apply_grouping('status')
        
        # 验证分组结果
        self.assertIn('下载中', self.download_list.grouped_tasks)
        self.assertIn('已完成', self.download_list.grouped_tasks)
        self.assertIn('等待中', self.download_list.grouped_tasks)
        
        self.assertEqual(len(self.download_list.grouped_tasks['下载中']), 1)
        self.assertEqual(len(self.download_list.grouped_tasks['已完成']), 1)
        self.assertEqual(len(self.download_list.grouped_tasks['等待中']), 1)
        
    def test_grouping_by_platform(self):
        """测试按平台分组"""
        # 添加任务
        task_ids = []
        for task_data in self.sample_tasks:
            task_id = self.download_list.add_task(task_data['url'], task_data['metadata'])
            task_ids.append(task_id)
            
        # 应用平台分组
        self.download_list.apply_grouping('platform')
        
        # 验证分组结果
        self.assertIn('YouTube', self.download_list.grouped_tasks)
        self.assertIn('B站', self.download_list.grouped_tasks)
        self.assertIn('抖音', self.download_list.grouped_tasks)
        
        self.assertEqual(len(self.download_list.grouped_tasks['YouTube']), 1)
        self.assertEqual(len(self.download_list.grouped_tasks['B站']), 1)
        self.assertEqual(len(self.download_list.grouped_tasks['抖音']), 1)
        
    def test_batch_operations(self):
        """测试批量操作"""
        # 添加任务
        task_ids = []
        for task_data in self.sample_tasks:
            task_id = self.download_list.add_task(task_data['url'], task_data['metadata'])
            task_ids.append(task_id)
            
        # 模拟选中所有任务
        self.download_list.selected_tasks = set(task_ids)
        
        # 测试批量开始
        self.download_list.batch_start_tasks()
        
        # 验证所有任务都收到了开始信号（通过mock验证）
        # 这里我们只验证选中的任务数量
        self.assertEqual(len(self.download_list.selected_tasks), 3)
        
    def test_clear_completed_tasks(self):
        """测试清除已完成任务"""
        # 添加任务并设置状态
        task_ids = []
        for i, task_data in enumerate(self.sample_tasks):
            task_id = self.download_list.add_task(task_data['url'], task_data['metadata'])
            task_ids.append(task_id)
            
            # 设置前两个为已完成
            if i < 2:
                self.download_list.update_task_status(task_id, 'completed')
                
        # 清除已完成任务
        self.download_list.clear_completed_tasks()
        
        # 验证只剩下一个任务
        self.assertEqual(self.download_list.get_task_count(), 1)
        
    def test_platform_extraction(self):
        """测试平台提取功能"""
        test_cases = [
            ('https://www.youtube.com/watch?v=test', 'YouTube'),
            ('https://youtu.be/test', 'YouTube'),
            ('https://www.bilibili.com/video/test', 'B站'),
            ('https://www.douyin.com/video/test', '抖音'),
            ('https://www.tiktok.com/test', '抖音'),
            ('https://www.instagram.com/p/test', 'Instagram'),
            ('https://example.com/video', '其他')
        ]
        
        for url, expected_platform in test_cases:
            platform = self.download_list.extract_platform_from_url(url)
            self.assertEqual(platform, expected_platform, f"URL: {url}")
            
    def test_virtual_list_performance(self):
        """测试虚拟列表性能"""
        # 添加大量任务
        import time
        start_time = time.time()
        
        task_ids = []
        for i in range(100):  # 添加100个任务
            task_id = self.download_list.add_task(
                f"https://example.com/video/{i}",
                {
                    'title': f'Test Video {i}',
                    'author': f'Test Author {i}',
                    'platform': 'YouTube' if i % 2 == 0 else 'B站'
                }
            )
            task_ids.append(task_id)
            
        end_time = time.time()
        
        # 验证性能（应该在合理时间内完成）
        self.assertLess(end_time - start_time, 5.0, "添加100个任务耗时过长")
        self.assertEqual(self.download_list.get_task_count(), 100)
        
    def test_filter_widget(self):
        """测试筛选控件"""
        filter_widget = TaskFilterWidget()
        
        # 测试获取筛选条件
        filters = filter_widget.get_filters()
        self.assertIn('search', filters)
        self.assertIn('status', filters)
        self.assertIn('platform', filters)
        
        # 测试设置搜索文本
        filter_widget.search_input.setText("test search")
        filters = filter_widget.get_filters()
        self.assertEqual(filters['search'], "test search")
        
    def test_group_widget(self):
        """测试分组控件"""
        group_widget = TaskGroupWidget()
        
        # 测试默认分组（无分组）
        self.assertTrue(group_widget.group_buttons.button(0).isChecked())
        
        # 测试切换分组
        group_widget.group_buttons.button(1).setChecked(True)
        self.assertTrue(group_widget.group_buttons.button(1).isChecked())
        
    def test_batch_widget(self):
        """测试批量操作控件"""
        batch_widget = BatchOperationWidget()
        
        # 测试更新选中数量
        batch_widget.update_selection_count(5, 10)
        self.assertEqual(batch_widget.selected_count, 5)
        self.assertIn("已选中 5 个任务", batch_widget.selection_label.text())
        
        # 测试按钮状态
        self.assertTrue(batch_widget.delete_selected_btn.isEnabled())
        
        batch_widget.update_selection_count(0, 10)
        self.assertFalse(batch_widget.delete_selected_btn.isEnabled())


class TestVirtualTaskList(unittest.TestCase):
    """虚拟任务列表测试"""
    
    @classmethod
    def setUpClass(cls):
        """设置测试类"""
        if not QApplication.instance():
            cls.app = QApplication([])
        else:
            cls.app = QApplication.instance()
            
    def setUp(self):
        """设置测试"""
        self.task_list = VirtualTaskList()
        
    def test_drag_drop_setup(self):
        """测试拖拽设置"""
        from PySide6.QtWidgets import QAbstractItemView
        self.assertTrue(self.task_list.dragEnabled())
        self.assertTrue(self.task_list.acceptDrops())
        self.assertEqual(
            self.task_list.dragDropMode(), 
            QAbstractItemView.InternalMove
        )
        
    def test_virtual_list_setup(self):
        """测试虚拟列表设置"""
        self.assertTrue(self.task_list.uniformItemSizes())
        self.assertEqual(self.task_list.item_height, 88)


def run_tests():
    """运行测试"""
    # 创建测试套件
    suite = unittest.TestSuite()
    
    # 添加测试用例
    suite.addTest(unittest.makeSuite(TestDownloadListManagement))
    suite.addTest(unittest.makeSuite(TestVirtualTaskList))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)