"""Collection/list operations engine — zero dependencies.

Uses only Python stdlib (json, collections, itertools, random).
Provides list manipulation: deduplicate, intersect, union, diff, flatten, chunk, sort, group, rotate, sample.
"""
import json
import random
import secrets
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple


class CollectionEngine:
    """List/collection operations with zero external dependencies."""

    @staticmethod
    def deduplicate(items: List[Any], preserve_order: bool = True) -> Dict:
        """Remove duplicates from a list."""
        if preserve_order:
            seen = set()
            result = []
            for item in items:
                key = json.dumps(item, sort_keys=True, default=str) if isinstance(item, (dict, list)) else item
                if key not in seen:
                    seen.add(key)
                    result.append(item)
        else:
            result = list(set(items)) if all(isinstance(x, (str, int, float, bool)) for x in items) else items

        return {
            "success": True,
            "original_count": len(items),
            "deduplicated_count": len(result),
            "duplicates_removed": len(items) - len(result),
            "result": result,
        }

    @staticmethod
    def intersect(list1: List[Any], list2: List[Any]) -> Dict:
        """Get intersection of two lists."""
        set1 = set(list1)
        set2 = set(list2)
        common = list(set1 & set2)
        return {
            "success": True,
            "list1_count": len(list1),
            "list2_count": len(list2),
            "common_count": len(common),
            "result": common,
        }

    @staticmethod
    def union(list1: List[Any], list2: List[Any], deduplicate: bool = True) -> Dict:
        """Get union of two lists."""
        if deduplicate:
            result = list(dict.fromkeys(list1 + list2))
        else:
            result = list1 + list2
        return {
            "success": True,
            "list1_count": len(list1),
            "list2_count": len(list2),
            "result_count": len(result),
            "result": result,
        }

    @staticmethod
    def difference(list1: List[Any], list2: List[Any]) -> Dict:
        """Get items in list1 but not in list2."""
        set2 = set(list2)
        result = [item for item in list1 if item not in set2]
        return {
            "success": True,
            "list1_count": len(list1),
            "list2_count": len(list2),
            "difference_count": len(result),
            "result": result,
        }

    @staticmethod
    def symmetric_difference(list1: List[Any], list2: List[Any]) -> Dict:
        """Get items in either list but not in both."""
        set1 = set(list1)
        set2 = set(list2)
        result = list(set1 ^ set2)
        return {
            "success": True,
            "result": result,
            "count": len(result),
        }

    @staticmethod
    def flatten(nested: List[Any], depth: int = -1) -> Dict:
        """Flatten a nested list. depth=-1 means fully flat."""
        def _flatten(items, current_depth):
            result = []
            for item in items:
                if isinstance(item, list) and (depth == -1 or current_depth < depth):
                    result.extend(_flatten(item, current_depth + 1))
                else:
                    result.append(item)
            return result

        result = _flatten(nested, 0)
        return {
            "success": True,
            "original_length": len(nested),
            "flattened_length": len(result),
            "result": result,
        }

    @staticmethod
    def chunk(items: List[Any], size: int) -> Dict:
        """Split a list into chunks of specified size."""
        if size < 1:
            return {"success": False, "error": "Chunk size must be >= 1"}
        chunks = [items[i:i + size] for i in range(0, len(items), size)]
        return {
            "success": True,
            "original_count": len(items),
            "chunk_count": len(chunks),
            "chunk_size": size,
            "result": chunks,
        }

    @staticmethod
    def sort_list(items: List[Any], key: str = None, reverse: bool = False) -> Dict:
        """Sort a list, optionally by a key in dict items."""
        try:
            if key and all(isinstance(x, dict) for x in items):
                result = sorted(items, key=lambda x: x.get(key, 0), reverse=reverse)
            elif key and all(isinstance(x, (list, tuple)) for x in items):
                idx = int(key) if key.isdigit() else 0
                result = sorted(items, key=lambda x: x[idx] if len(x) > idx else 0, reverse=reverse)
            else:
                result = sorted(items, reverse=reverse)
            return {"success": True, "result": result, "count": len(result), "reverse": reverse}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def group_by(items: List[Dict], key: str) -> Dict:
        """Group list of dicts by a key."""
        groups = {}
        for item in items:
            if isinstance(item, dict) and key in item:
                group_key = str(item[key])
                if group_key not in groups:
                    groups[group_key] = []
                groups[group_key].append(item)
        return {
            "success": True,
            "group_count": len(groups),
            "groups": groups,
            "total_items": len(items),
        }

    @staticmethod
    def count_items(items: List[Any]) -> Dict:
        """Count occurrences of each item."""
        counter = Counter(items)
        return {
            "success": True,
            "total": len(items),
            "unique": len(counter),
            "counts": dict(counter.most_common()),
        }

    @staticmethod
    def rotate(items: List[Any], positions: int) -> Dict:
        """Rotate list by n positions (positive=right, negative=left)."""
        if not items:
            return {"success": True, "result": [], "positions": positions}
        n = positions % len(items)
        result = items[-n:] + items[:-n] if n > 0 else items
        return {"success": True, "result": result, "positions": positions, "count": len(result)}

    @staticmethod
    def sample(items: List[Any], n: int) -> Dict:
        """Get n random items from a list (using secrets for crypto-safe random)."""
        if n > len(items):
            return {"success": False, "error": f"Cannot sample {n} from {len(items)} items"}
        indices = list(range(len(items)))
        # Crypto-safe shuffle
        for i in range(len(indices) - 1, 0, -1):
            j = secrets.randbelow(i + 1)
            indices[i], indices[j] = indices[j], indices[i]
        selected = [items[indices[i]] for i in range(n)]
        return {"success": True, "result": selected, "sampled": n, "total": len(items)}

    @staticmethod
    def partition(items: List[Any], predicate_fn: str = "truthy") -> Dict:
        """Partition list into two based on a simple predicate."""
        if predicate_fn == "truthy":
            truthy = [x for x in items if x]
            falsy = [x for x in items if not x]
        elif predicate_fn == "even":
            truthy = [x for x in items if isinstance(x, (int, float)) and x % 2 == 0]
            falsy = [x for x in items if not (isinstance(x, (int, float)) and x % 2 == 0)]
        elif predicate_fn == "nonempty":
            truthy = [x for x in items if isinstance(x, (str, list, dict)) and len(x) > 0]
            falsy = [x for x in items if not (isinstance(x, (str, list, dict)) and len(x) > 0)]
        else:
            return {"success": False, "error": f"Unknown predicate: {predicate_fn}. Use truthy, even, nonempty."}

        return {
            "success": True,
            "matching": truthy,
            "non_matching": falsy,
            "matching_count": len(truthy),
            "non_matching_count": len(falsy),
        }

    @staticmethod
    def zip_lists(lists: List[List[Any]]) -> Dict:
        """Zip multiple lists together."""
        if not lists:
            return {"success": False, "error": "No lists provided"}
        result = list(zip(*lists))
        return {
            "success": True,
            "list_count": len(lists),
            "zipped_count": len(result),
            "result": [list(t) for t in result],
        }

    @staticmethod
    def reverse_list(items: List[Any]) -> Dict:
        """Reverse a list."""
        return {"success": True, "result": items[::-1], "original": items}

    @staticmethod
    def find_index(items: List[Any], value: Any) -> Dict:
        """Find the index of a value in a list."""
        try:
            index = items.index(value)
            return {"success": True, "found": True, "index": index, "value": value}
        except ValueError:
            return {"success": True, "found": False, "index": None, "value": value}

    @staticmethod
    def contains(items: List[Any], value: Any) -> Dict:
        """Check if a list contains a value."""
        return {"success": True, "contains": value in items, "value": value, "list_length": len(items)}

    @staticmethod
    def head(items: List[Any], n: int = 5) -> Dict:
        """Get the first n items."""
        return {"success": True, "result": items[:n], "count": min(n, len(items)), "total": len(items)}

    @staticmethod
    def tail(items: List[Any], n: int = 5) -> Dict:
        """Get the last n items."""
        return {"success": True, "result": items[-n:], "count": min(n, len(items)), "total": len(items)}
