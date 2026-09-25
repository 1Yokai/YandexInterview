import json, sys, io, traceback, random

class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

def _list_build(arr):
    dummy = ListNode(0)
    cur = dummy
    for v in arr:
        cur.next = ListNode(v)
        cur = cur.next
    return dummy.next

def _list_dump(node):
    res = []
    seen = set()
    while node is not None and id(node) not in seen:
        seen.add(id(node))
        res.append(node.val)
        node = node.next
    return res

def _tree_build(arr):
    if not arr:
        return None
    it = iter(arr)
    root_val = next(it)
    if root_val is None:
        return None
    root = TreeNode(root_val)
    queue = [root]
    while queue:
        node = queue.pop(0)
        try:
            lv = next(it)
        except StopIteration:
            break
        if lv is not None:
            node.left = TreeNode(lv)
            queue.append(node.left)
        try:
            rv = next(it)
        except StopIteration:
            break
        if rv is not None:
            node.right = TreeNode(rv)
            queue.append(node.right)
    return root

def _tree_dump(root):
    if root is None:
        return []
    res = []
    queue = [root]
    while queue:
        node = queue.pop(0)
        if node is None:
            res.append(None)
            continue
        res.append(node.val)
        queue.append(node.left)
        queue.append(node.right)
    while res and res[-1] is None:
        res.pop()
    return res

def _canon_tree_arr(arr):
    return _tree_dump(_tree_build(arr))

def _conv_in(v, kind):
    if kind == "list":
        return _list_build(v)
    if kind == "tree":
        return _tree_build(v)
    if kind == "lists":
        return [_list_build(x) for x in v]
    return v

def _conv_out(v, kind):
    if kind == "list":
        return _list_dump(v)
    if kind == "tree":
        return _tree_dump(v)
    if kind == "lists":
        return [_list_dump(x) for x in v]
    return v

def canon(v):
    if isinstance(v, list):
        return sorted((canon(x) for x in v), key=lambda x: json.dumps(x, sort_keys=True, default=str))
    return v

def _eq(got, exp, ret_type, unordered):
    if ret_type == "tree":
        return _tree_dump(got) == _canon_tree_arr(exp) if got is not None or exp else (got is None and not exp)
    if ret_type == "list":
        got = _list_dump(got)
    if ret_type == "lists":
        got = _conv_out(got, "lists")
    g = got
    try:
        g = json.loads(json.dumps(g))
    except Exception:
        pass
    return (canon(g) == canon(exp)) if unordered else (g == exp)


def _run_solve(ns, spec):
    solve = ns.get("solve")
    if solve is None:
        return None, "Не найдена функция solve(...)"
    arg_types = spec.get("arg_types") or []
    ret_type = spec.get("ret_type") or "raw"
    unordered = bool(spec.get("unordered"))
    results = []
    for i, item in enumerate(spec["tests"], 1):
        args, exp = item[:-1], item[-1]
        r = {"i": i, "args": json.dumps(args, ensure_ascii=False, default=str)[1:-1],
             "expected": json.dumps(exp, ensure_ascii=False, default=str)}
        try:
            call_args = [_conv_in(a, arg_types[j] if j < len(arg_types) else "raw") for j, a in enumerate(args)]
            got = solve(*call_args)
            ok = _eq(got, exp, ret_type, unordered)
            shown = _conv_out(got, ret_type) if ret_type in ("list", "tree") else got
            try:
                shown = json.loads(json.dumps(shown, default=str))
            except Exception:
                pass
            r["ok"] = ok
            r["got"] = json.dumps(shown, ensure_ascii=False, default=str)
        except Exception as e:
            r["ok"] = False
            r["error"] = repr(e)
        results.append(r)
    return results, None


def _run_cycle(ns, spec):
    solve = ns.get("solve")
    if solve is None:
        return None, "Не найдена функция solve(...)"
    results = []
    for i, item in enumerate(spec["tests"], 1):
        values, pos, exp = item
        r = {"i": i, "args": f"values={values!r}, pos={pos!r}", "expected": json.dumps(exp)}
        try:
            head = _list_build(values)
            if pos is not None and pos >= 0 and head is not None:
                nodes = []
                n = head
                while n is not None:
                    nodes.append(n)
                    n = n.next
                nodes[-1].next = nodes[pos]
            got = bool(solve(head))
            r["ok"] = (got == exp)
            r["got"] = json.dumps(got)
        except Exception as e:
            r["ok"] = False
            r["error"] = repr(e)
        results.append(r)
    return results, None


def _run_ops(ns, spec):
    cls = ns.get(spec["class_name"])
    if cls is None:
        return None, f"Не найден класс {spec['class_name']}"
    results = []
    for i, case in enumerate(spec["tests"], 1):
        ops, args, exp = case["ops"], case["args"], case["expected"]
        r = {"i": i, "args": f"{ops}", "expected": json.dumps(exp, ensure_ascii=False)}
        try:
            obj = cls(*args[0])
            out = [None]
            for op, a in zip(ops[1:], args[1:]):
                out.append(getattr(obj, op)(*a))
            ok = True
            shown = []
            for got, want in zip(out, exp):
                shown.append(got)
                if want is None:
                    continue
                g = got
                try:
                    g = json.loads(json.dumps(g))
                except Exception:
                    pass
                if canon(g) != canon(want) if isinstance(want, list) else g != want:
                    ok = False
            r["ok"] = ok
            r["got"] = json.dumps(shown, ensure_ascii=False, default=str)
        except Exception as e:
            r["ok"] = False
            r["error"] = repr(e)
        results.append(r)
    return results, None


def _run_shuffle(ns, spec):
    cls = ns.get("Solution")
    if cls is None:
        return None, "Не найден класс Solution"
    results = []
    for i, case in enumerate(spec["tests"], 1):
        nums = case["nums"]
        r = {"i": i, "args": f"nums={nums!r}", "expected": "reset() == исходный массив; shuffle() — перестановка того же массива"}
        try:
            obj = cls(nums[:])
            ok = True
            for _ in range(5):
                sh = obj.shuffle()
                if sorted(sh) != sorted(nums):
                    ok = False
            back = obj.reset()
            if back != nums:
                ok = False
            r["ok"] = ok
            r["got"] = "перестановки корректны" if ok else "shuffle()/reset() вернули не те элементы"
        except Exception as e:
            r["ok"] = False
            r["error"] = repr(e)
        results.append(r)
    return results, None


def _run_random_pick(ns, spec):
    cls = ns.get("Solution")
    if cls is None:
        return None, "Не найден класс Solution"
    results = []
    for i, case in enumerate(spec["tests"], 1):
        w = case["w"]
        r = {"i": i, "args": f"w={w!r}", "expected": "частоты индексов пропорциональны весам"}
        try:
            obj = cls(w[:])
            n = 4000
            counts = [0] * len(w)
            for _ in range(n):
                idx = obj.pickIndex()
                if idx < 0 or idx >= len(w):
                    r["ok"] = False
                    r["error"] = f"pickIndex() вернул недопустимый индекс {idx}"
                    break
                counts[idx] += 1
            else:
                total = sum(w)
                ok = True
                for c, ww in zip(counts, w):
                    if abs(c / n - ww / total) > 0.08:
                        ok = False
                r["ok"] = ok
                r["got"] = f"частоты: {counts}"
        except Exception as e:
            r["ok"] = False
            r["error"] = repr(e)
        results.append(r)
    return results, None

def _run_serde(ns, spec):
    ser, de = ns.get("serialize"), ns.get("deserialize")
    if ser is None or de is None:
        return None, "Не найдены функции serialize(root) и deserialize(data)"
    results = []
    for i, arr in enumerate(spec["tests"], 1):
        r = {"i": i, "args": f"tree={arr!r}", "expected": "дерево после serialize -> deserialize совпадает с исходным"}
        try:
            root = _tree_build(arr)
            data = ser(root)
            root2 = de(data)
            got = _tree_dump(root2)
            r["ok"] = (got == _canon_tree_arr(arr))
            r["got"] = json.dumps(got)
        except Exception as e:
            r["ok"] = False
            r["error"] = repr(e)
        results.append(r)
    return results, None


class Node:
    def __init__(self, val=0, neighbors=None):
        self.val = val
        self.neighbors = neighbors if neighbors is not None else []


def _graph_build(adj):
    nodes = {i + 1: Node(i + 1) for i in range(len(adj))}
    for i, nbrs in enumerate(adj, 1):
        nodes[i].neighbors = [nodes[j] for j in nbrs]
    return nodes.get(1)


def _graph_dump(node):
    if node is None:
        return {}, set()
    seen = {}
    ids = set()

    def dfs(n):
        if n.val in seen:
            return
        ids.add(id(n))
        seen[n.val] = sorted(nb.val for nb in n.neighbors)
        for nb in n.neighbors:
            dfs(nb)
    dfs(node)
    return seen, ids


def _run_clone_graph(ns, spec):
    solve = ns.get("solve")
    if solve is None:
        return None, "Не найдена функция solve(...)"
    results = []
    for i, adj in enumerate(spec["tests"], 1):
        r = {"i": i, "args": f"adjList={adj!r}", "expected": "клон с той же структурой, но другими объектами узлов"}
        try:
            orig = _graph_build(adj)
            orig_map, orig_ids = _graph_dump(orig)
            clone = solve(orig)
            clone_map, clone_ids = _graph_dump(clone)
            same_structure = (orig_map == clone_map)
            real_copy = not (orig_ids & clone_ids) if adj else True
            r["ok"] = same_structure and real_copy
            r["got"] = "структура совпадает, узлы скопированы" if r["ok"] else ("структура отличается" if not same_structure else "возвращены те же объекты узлов, а не копии")
        except Exception as e:
            r["ok"] = False
            r["error"] = repr(e)
        results.append(r)
    return results, None

_RUNNERS = {
    "solve": _run_solve, "cycle": _run_cycle, "ops": _run_ops,
    "shuffle": _run_shuffle, "random_pick": _run_random_pick,
    "serde": _run_serde, "clone_graph": _run_clone_graph,
}

def run_tests(code, spec_json):
    spec = json.loads(spec_json)
    buf, old = io.StringIO(), sys.stdout
    sys.stdout = buf
    out = {"res": [], "fatal": ""}
    try:
        ns = {"__name__": "solution", "ListNode": ListNode, "TreeNode": TreeNode, "Node": Node}
        exec("from typing import *\nimport heapq, collections, bisect, math, random\nfrom collections import defaultdict, Counter, deque\n", ns)
        exec(compile(code, "solution.py", "exec"), ns)
        runner = _RUNNERS.get(spec.get("kind", "solve"), _run_solve)
        results, fatal = runner(ns, spec)
        if fatal:
            out["fatal"] = fatal
        else:
            out["res"] = results
    except BaseException as e:
        tb = e.__traceback__.tb_next if e.__traceback__ else None
        out["fatal"] = "".join(traceback.format_exception(type(e), e, tb))
    finally:
        sys.stdout = old
    out["out"] = buf.getvalue()[:5000]
    return json.dumps(out, ensure_ascii=False)
