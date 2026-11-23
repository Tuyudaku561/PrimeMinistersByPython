"""``break`` と ``return`` を運ぶ例外(シグナル)の基底クラス。

Java版では、 ``ConditionException`` と ``IntervalException`` がほぼ同じ内容で
重複していたので、Python版では共通の :class:`Signal` にまとめた。

また、Java版は「メッセージ文字列(クラス名+メソッド名)の比較」で
break/returnを判定していたため、ループがネストすると
内側と外側を区別できなかった。Python版は、シグナルに
「発信元オブジェクト(``source``)」を持たせ、 ``is`` で同一性を比べる。
"""

from ._dispatch import branch, noop


class Signal(Exception):
    """``break`` / ``return`` を表す例外の基底クラス。

    ループ本体から ``_break_()`` / ``_return_()`` が呼ばれると送出される。

    Attributes:
        kind (str): ``Signal.BREAK`` か ``Signal.RETURN`` 。
        source: このシグナルを発信したオブジェクト( ``Condition`` や ``Interval`` )。
    """

    BREAK = "break"
    RETURN = "return"

    def __init__(self, kind, source):
        """シグナルを作る。

        Args:
            kind: ``Signal.BREAK`` または ``Signal.RETURN`` 。
            source: 発信元オブジェクト。
        """
        super().__init__(f"{type(source).__name__}.{kind}()")
        self.kind = kind
        self.source = source

    # ---- 判定 -------------------------------------------------------
    def is_break(self):
        """``break`` のシグナルなら ``True`` 。"""
        return self.kind == Signal.BREAK

    def is_return(self):
        """``return`` のシグナルなら ``True`` 。"""
        return self.kind == Signal.RETURN

    def is_from(self, source):
        """発信元が ``source`` 自身なら ``True`` ( ``is`` による同一性判定)。

        Args:
            source: 比べる相手のオブジェクト。
        """
        return self.source is source

    # ---- break へのメッセージ --------------------------------------
    def is_break_then_else(self, then, else_):
        """``break`` なら ``then`` 、そうでなければ ``else_`` を呼ぶ。

        Args:
            then: ``break`` のときに呼ぶ関数。引数なし、または発信元を受け取る1引数。
            else_: ``break`` でないときに呼ぶ関数。形は ``then`` と同じ。
        """
        branch(self.is_break(), then, else_, self.source)

    def is_break_true(self, then):
        """``break`` のときだけ ``then`` を呼ぶ。"""
        self.is_break_then_else(then, noop)

    def is_break_false(self, else_):
        """``break`` でないときだけ ``else_`` を呼ぶ。"""
        self.is_break_then_else(noop, else_)

    # ---- return へのメッセージ -------------------------------------
    def is_return_then_else(self, then, else_):
        """``return`` なら ``then`` 、そうでなければ ``else_`` を呼ぶ。

        Args:
            then: ``return`` のときに呼ぶ関数。引数なし、または発信元を受け取る1引数。
            else_: ``return`` でないときに呼ぶ関数。形は ``then`` と同じ。
        """
        branch(self.is_return(), then, else_, self.source)

    def is_return_true(self, then):
        """``return`` のときだけ ``then`` を呼ぶ。"""
        self.is_return_then_else(then, noop)

    def is_return_false(self, else_):
        """``return`` でないときだけ ``else_`` を呼ぶ。"""
        self.is_return_then_else(noop, else_)

    def __str__(self):
        return f"{type(self).__name__}[{self.args[0]}]"
