import time
from collections import OrderedDict


class LRUCache:
    def __init__(self, max_size=2 * 1024 * 1024 * 1024, ttl=7200):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.ttl = ttl
        self.current_size = 0

    def __getitem__(self, key):
        if key not in self.cache:
            return None

        entry = self.cache.pop(key)
        if time.time() - entry['timestamp'] > self.ttl:
            self.current_size -= entry['size']
            return None

        self.cache[key] = entry  # 将最近访问的项移到末尾
        return entry['value']

    def __setitem__(self, key, value):
        if key in self.cache:
            self.cache.pop(key)

        size = self._estimate_size(value)

        # 如果超出缓存大小，删除旧项
        while self.current_size + size > self.max_size and len(self.cache) > 0:
            self.cache.popitem(last=False)  # 删除最近最少使用的项

        self.cache[key] = {
            'value': value,
            'timestamp': time.time(),
            'size': size
        }
        self.current_size += size

    def __contains__(self, key):
        return key in self.cache

    def _estimate_size(self, value):
        """估算对象占用内存大小（字节）"""
        if isinstance(value, (str, bytes)):
            return len(value)
        elif isinstance(value, (int, float)):
            return 8  # 简单类型假设占8字节
        elif isinstance(value, (list, dict)):
            return sum(self._estimate_size(v) for v in value.values()) if isinstance(value, dict) else sum(
                self._estimate_size(v) for v in value)
        else:
            return 64  # 其他类型的保守估计

    def clear(self):
        self.cache.clear()
        self.current_size = 0
