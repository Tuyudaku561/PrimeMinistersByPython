"""``messaging`` パッケージのテスト。

実行方法(プロジェクトの親ディレクトリで)::

    python -m unittest messaging.test_messaging -v
"""

import ast
import pathlib
import unittest

from .condition import Condition, ConditionSignal
from .interval import Interval, IntervalSignal
from .value_holder import ValueHolder


class ValueHolderTest(unittest.TestCase):
    def test_set_returns_old_value(self):
        h = ValueHolder(1)
        self.assertEqual(h.set(2), 1)
        self.assertEqual(h.get(), 2)

    def test_set_do_and_get_and_set_do_return_old_value(self):
        h = ValueHolder(10)
        self.assertEqual(h.set_do(lambda n: n + 1), 10)
        self.assertEqual(h.get_and_set_do(lambda n: n * 2), 11)
        self.assertEqual(h.get(), 22)


class ConditionBranchTest(unittest.TestCase):
    def test_then_and_else_are_not_mixed_up(self):
        """Java版にあった「どちらでもelse側が走る」不具合の回帰テスト。"""
        log = []
        Condition(lambda: True).if_then_else(lambda: log.append("then"), lambda: log.append("else"))
        Condition(lambda: False).if_then_else(lambda: log.append("then"), lambda: log.append("else"))
        self.assertEqual(log, ["then", "else"])

    def test_if_true_and_if_false(self):
        log = []
        Condition(lambda: True).if_true(lambda: log.append("t1"))
        Condition(lambda: False).if_true(lambda: log.append("t2"))
        Condition(lambda: True).if_false(lambda: log.append("f1"))
        Condition(lambda: False).if_false(lambda: log.append("f2"))
        self.assertEqual(log, ["t1", "f2"])

    def test_callback_arity_is_dispatched(self):
        got = []
        cond = Condition(lambda: True)
        cond.if_true(lambda: got.append("no-arg"))
        cond.if_true(lambda c: got.append(c))
        self.assertEqual(got[0], "no-arg")
        self.assertIs(got[1], cond)

    def test_default_argument_is_not_overwritten(self):
        got = []
        Condition(lambda: True).if_true(lambda x=5: got.append(x))
        self.assertEqual(got, [5])


class ConditionLoopTest(unittest.TestCase):
    def test_while_true(self):
        h, log = ValueHolder(0), []
        Condition(lambda: h.get() < 3).while_true(
            lambda: log.append(h.get_and_set_do(lambda n: n + 1)))
        self.assertEqual(log, [0, 1, 2])

    def test_while_false(self):
        h, log = ValueHolder(3), []
        Condition(lambda: h.get() <= 0).while_false(
            lambda: log.append(h.get_and_set_do(lambda n: n - 1)))
        self.assertEqual(log, [3, 2, 1])

    def test_break_stops_loop_and_is_swallowed(self):
        h, log = ValueHolder(0), []

        def body(cond):
            Condition(lambda: h.get() >= 3).if_true(cond._break_)
            log.append(h.get_and_set_do(lambda n: n + 1))

        Condition(lambda: True).while_true(body)
        self.assertEqual(log, [0, 1, 2])

    def test_return_propagates(self):
        def body(cond):
            cond._return_()

        with self.assertRaises(ConditionSignal) as ctx:
            Condition(lambda: True).while_true(body)
        self.assertTrue(ctx.exception.is_return())
        self.assertFalse(ctx.exception.is_break())

    def test_signal_message_helpers(self):
        log = []
        try:
            Condition(lambda: True).while_true(lambda c: c._return_())
        except ConditionSignal as signal:
            signal.is_return_true(lambda: log.append("return"))
            signal.is_break_true(lambda: log.append("break"))
            signal.is_break_false(lambda: log.append("not-break"))
        self.assertEqual(log, ["return", "not-break"])

    def test_nested_inner_break_only_stops_inner(self):
        log = []
        outer_count = ValueHolder(0)
        outer = Condition(lambda: outer_count.get() < 2)

        def outer_body():
            outer_count.set_do(lambda n: n + 1)
            inner = Condition(lambda: True)

            def inner_body(i):
                log.append("inner")
                i._break_()

            inner.while_true(inner_body)

        outer.while_true(outer_body)
        self.assertEqual(log, ["inner", "inner"])

    def test_nested_outer_break_from_inside_inner(self):
        """Java版ではクラス名比較のため区別できなかった、外側のbreak。"""
        log = []
        outer = Condition(lambda: True)
        inner = Condition(lambda: True)

        def outer_body(o):
            def inner_body(_):
                log.append("inner")
                o._break_()  # 外側をbreak

            inner.while_true(inner_body)
            log.append("never")

        outer.while_true(outer_body)
        self.assertEqual(log, ["inner"])


class IntervalTest(unittest.TestCase):
    def test_for_each_one_arg(self):
        log = []
        Interval(0, lambda v: v < 3, lambda v: v + 1).for_each(log.append)
        self.assertEqual(log, [0, 1, 2])

    def test_for_each_two_args_and_no_arg(self):
        itv = Interval(0, lambda v: v < 2, lambda v: v + 1)
        pairs, count = [], ValueHolder(0)
        itv.for_each(lambda v, i: pairs.append((v, i)))
        itv.for_each(lambda: count.set_do(lambda n: n + 1))
        self.assertEqual([v for v, _ in pairs], [0, 1])
        self.assertTrue(all(i is itv for _, i in pairs))
        self.assertEqual(count.get(), 2)

    def test_for_each_can_run_repeatedly(self):
        itv, log = Interval(1, lambda v: v <= 2, lambda v: v + 1), []
        itv.for_each(log.append)
        itv.for_each(log.append)
        self.assertEqual(log, [1, 2, 1, 2])

    def test_descending(self):
        log = []
        Interval(3, lambda v: v >= 1, lambda v: v - 1).for_each(log.append)
        self.assertEqual(log, [3, 2, 1])

    def test_break(self):
        log = []

        def body(v, itv):
            Condition(lambda: v > 2).if_true(itv._break_)
            log.append(v)

        Interval(0, lambda v: v < 100, lambda v: v + 1).for_each(body)
        self.assertEqual(log, [0, 1, 2])

    def test_return_propagates(self):
        with self.assertRaises(IntervalSignal) as ctx:
            Interval(0, lambda v: True, lambda v: v + 1).for_each(lambda v, i: i._return_())
        self.assertTrue(ctx.exception.is_return())

    def test_nested_outer_break_from_inner_interval(self):
        log = []
        inner = Interval(0, lambda v: v < 3, lambda v: v + 1)

        def outer_body(a, outer):
            def inner_body(b):
                log.append((a, b))
                Condition(lambda: b == 1).if_true(outer._break_)

            inner.for_each(inner_body)

        Interval(0, lambda v: v < 3, lambda v: v + 1).for_each(outer_body)
        self.assertEqual(log, [(0, 0), (0, 1)])

    def test_return_from_interval_inside_condition_loop(self):
        """種類の違うシグナル(IntervalSignal)は、Conditionのループを素通りする。"""
        def body(cond):
            Interval(0, lambda v: True, lambda v: v + 1).for_each(lambda v, i: i._return_())

        with self.assertRaises(IntervalSignal):
            Condition(lambda: True).while_true(body)


class NoControlStatementsTest(unittest.TestCase):
    """ライブラリ本体と使用例に、制御構文(文)が1つもないことを確かめる。"""

    FORBIDDEN = (ast.If, ast.IfExp, ast.While, ast.For, ast.AsyncFor)

    def test_no_if_while_for(self):
        directory = pathlib.Path(__file__).parent
        targets = [p for p in sorted(directory.glob("*.py")) if not p.name.startswith("test_")]
        self.assertTrue(targets)
        found = [
            f"{p.name}:{node.lineno} {type(node).__name__}"
            for p in targets
            for node in ast.walk(ast.parse(p.read_text(encoding="utf-8")))
            if isinstance(node, self.FORBIDDEN)
        ]
        self.assertEqual(found, [])


if __name__ == "__main__":
    unittest.main()
