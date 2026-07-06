"""Tests for MCP Collection Tools — deduplicate, intersect, union, diff, flatten, chunk, sort, group, rotate, sample."""
import json
import pytest
import os
import sys
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.server import MCPCollectionToolsServer, TOOL_DEFS
from src.collection_engine import CollectionEngine


class TestToolDefinitions:
    def test_all_tools_have_names(self):
        for t in TOOL_DEFS:
            assert "name" in t and len(t["name"]) > 0

    def test_all_tools_have_descriptions(self):
        for t in TOOL_DEFS:
            assert "description" in t and len(t["description"]) > 10

    def test_all_tools_have_input_schema(self):
        for t in TOOL_DEFS:
            assert "inputSchema" in t and t["inputSchema"]["type"] == "object"

    def test_expected_tool_count(self):
        assert len(TOOL_DEFS) == 19

    def test_required_tools_present(self):
        names = {t["name"] for t in TOOL_DEFS}
        expected = {"deduplicate", "intersect", "union", "difference", "symmetric_difference",
                    "flatten", "chunk", "sort_list", "group_by", "count_items", "rotate",
                    "sample", "partition", "zip_lists", "reverse_list", "find_index",
                    "contains", "head", "tail"}
        assert names == expected


class TestManifest:
    def test_manifest(self):
        s = MCPCollectionToolsServer()
        m = s.manifest()
        assert m["server"]["name"] == "mcp-collection-tools"
        assert len(m["tools"]) == 19


class TestDeduplicate:
    def test_basic(self):
        r = CollectionEngine.deduplicate([1, 2, 2, 3, 3, 3])
        assert r["deduplicated_count"] == 3
        assert r["duplicates_removed"] == 3

    def test_preserve_order(self):
        r = CollectionEngine.deduplicate([3, 1, 2, 1, 3])
        assert r["result"] == [3, 1, 2]


class TestIntersect:
    def test_basic(self):
        r = CollectionEngine.intersect([1, 2, 3], [2, 3, 4])
        assert set(r["result"]) == {2, 3}
        assert r["common_count"] == 2

    def test_no_common(self):
        r = CollectionEngine.intersect([1, 2], [3, 4])
        assert r["common_count"] == 0


class TestUnion:
    def test_dedup(self):
        r = CollectionEngine.union([1, 2], [2, 3])
        assert len(r["result"]) == 3

    def test_no_dedup(self):
        r = CollectionEngine.union([1, 2], [2, 3], deduplicate=False)
        assert len(r["result"]) == 4


class TestDifference:
    def test_basic(self):
        r = CollectionEngine.difference([1, 2, 3, 4], [2, 4])
        assert r["result"] == [1, 3]


class TestSymmetricDifference:
    def test_basic(self):
        r = CollectionEngine.symmetric_difference([1, 2, 3], [2, 3, 4])
        assert set(r["result"]) == {1, 4}


class TestFlatten:
    def test_full(self):
        r = CollectionEngine.flatten([1, [2, [3, [4]]]])
        assert r["result"] == [1, 2, 3, 4]

    def test_depth_1(self):
        r = CollectionEngine.flatten([1, [2, [3]]], depth=1)
        assert r["result"] == [1, 2, [3]]


class TestChunk:
    def test_basic(self):
        r = CollectionEngine.chunk([1, 2, 3, 4, 5], 2)
        assert r["chunk_count"] == 3
        assert r["result"] == [[1, 2], [3, 4], [5]]

    def test_invalid_size(self):
        r = CollectionEngine.chunk([1, 2], 0)
        assert r["success"] is False


class TestSort:
    def test_basic(self):
        r = CollectionEngine.sort_list([3, 1, 2])
        assert r["result"] == [1, 2, 3]

    def test_reverse(self):
        r = CollectionEngine.sort_list([1, 2, 3], reverse=True)
        assert r["result"] == [3, 2, 1]

    def test_by_key(self):
        r = CollectionEngine.sort_list([{"age": 30}, {"age": 20}], key="age")
        assert r["result"][0]["age"] == 20


class TestGroupBy:
    def test_basic(self):
        r = CollectionEngine.group_by([{"type": "a", "v": 1}, {"type": "b", "v": 2}, {"type": "a", "v": 3}], "type")
        assert r["group_count"] == 2
        assert len(r["groups"]["a"]) == 2


class TestCountItems:
    def test_basic(self):
        r = CollectionEngine.count_items(["a", "b", "a", "c", "a"])
        assert r["counts"]["a"] == 3
        assert r["unique"] == 3


class TestRotate:
    def test_right(self):
        r = CollectionEngine.rotate([1, 2, 3, 4], 1)
        assert r["result"] == [4, 1, 2, 3]

    def test_left(self):
        r = CollectionEngine.rotate([1, 2, 3, 4], -1)
        assert r["result"] == [2, 3, 4, 1]


class TestSample:
    def test_basic(self):
        r = CollectionEngine.sample([1, 2, 3, 4, 5], 3)
        assert len(r["result"]) == 3
        assert all(x in [1, 2, 3, 4, 5] for x in r["result"])

    def test_too_many(self):
        r = CollectionEngine.sample([1, 2], 5)
        assert r["success"] is False


class TestPartition:
    def test_truthy(self):
        r = CollectionEngine.partition([1, 0, "hello", "", None, True], "truthy")
        assert r["matching_count"] == 3

    def test_even(self):
        r = CollectionEngine.partition([1, 2, 3, 4, 5, 6], "even")
        assert r["matching_count"] == 3

    def test_unknown(self):
        r = CollectionEngine.partition([1, 2], "unknown")
        assert r["success"] is False


class TestZipLists:
    def test_basic(self):
        r = CollectionEngine.zip_lists([[1, 2], ["a", "b"]])
        assert r["result"] == [[1, "a"], [2, "b"]]


class TestReverseList:
    def test_basic(self):
        r = CollectionEngine.reverse_list([1, 2, 3])
        assert r["result"] == [3, 2, 1]


class TestFindIndex:
    def test_found(self):
        r = CollectionEngine.find_index(["a", "b", "c"], "b")
        assert r["found"] is True
        assert r["index"] == 1

    def test_not_found(self):
        r = CollectionEngine.find_index(["a", "b"], "z")
        assert r["found"] is False


class TestContains:
    def test_true(self):
        r = CollectionEngine.contains([1, 2, 3], 2)
        assert r["contains"] is True

    def test_false(self):
        r = CollectionEngine.contains([1, 2, 3], 5)
        assert r["contains"] is False


class TestHeadTail:
    def test_head(self):
        r = CollectionEngine.head([1, 2, 3, 4, 5], 3)
        assert r["result"] == [1, 2, 3]

    def test_tail(self):
        r = CollectionEngine.tail([1, 2, 3, 4, 5], 3)
        assert r["result"] == [3, 4, 5]

    def test_head_more_than_list(self):
        r = CollectionEngine.head([1, 2], 5)
        assert r["count"] == 2


class TestServerDispatch:
    def test_unknown_tool(self):
        s = MCPCollectionToolsServer()
        assert "error" in json.loads(s.handle_tool_call("nope", {}))

    def test_missing_param(self):
        s = MCPCollectionToolsServer()
        assert "error" in json.loads(s.handle_tool_call("deduplicate", {}))

    def test_deduplicate_dispatch(self):
        s = MCPCollectionToolsServer()
        r = json.loads(s.handle_tool_call("deduplicate", {"items": [1, 1, 2]}))
        assert r["deduplicated_count"] == 2

    def test_flatten_dispatch(self):
        s = MCPCollectionToolsServer()
        r = json.loads(s.handle_tool_call("flatten", {"items": [1, [2, [3]]]}))
        assert r["result"] == [1, 2, 3]

    def test_chunk_dispatch(self):
        s = MCPCollectionToolsServer()
        r = json.loads(s.handle_tool_call("chunk", {"items": [1, 2, 3, 4], "size": 2}))
        assert r["chunk_count"] == 2


class TestSTDIOMode:
    def test_manifest_flag(self, capsys):
        from src.server import main
        with patch("sys.argv", ["server", "--manifest"]):
            main()
        parsed = json.loads(capsys.readouterr().out.strip())
        assert parsed["server"]["name"] == "mcp-collection-tools"
