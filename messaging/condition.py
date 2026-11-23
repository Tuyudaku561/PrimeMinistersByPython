"""条件オブジェクト :class:`Condition` と、その ``break`` / ``return`` シグナル。"""

from itertools import repeat, takewhile

from ._dispatch import branch, call, consume, noop, raise_
from .signals import Signal


class ConditionSignal(Signal):
    """:class:`Condition` の ``_break_`` / ``_return_`` が送出するシグナル。

    ``while_true`` / ``while_false`` の中で、自分が発信した ``break`` は
    ループが受け止めて終了する。 ``return`` と、他のオブジェクトが発信した
    シグナルは、そのまま外へ伝わる。

    ``return`` を受け止めたい側は、 ``try`` / ``except`` で捕まえて
    :meth:`~messaging.signals.Signal.is_return_true` などで判定する。
    """


class Condition:
    """条件(真偽値を返す関数)を持ち、メッセージで分岐・繰り返しを行うオブジェクト。

    ``if`` 文や ``while`` 文の代わりに、条件オブジェクトへ
    ``if_true`` や ``while_true`` といったメッセージを送る。

    コールバック(``then`` / ``body`` など)は、次のどちらの形でもよい。
    ライブラリが引数の個数を調べて、自動で振り分ける(Java版のオーバーロードの代わり)。

    * 引数なし: ``lambda: ...``   (Java版の ``Runnable`` )
    * 引数1つ : ``lambda cond: ...`` (Java版の ``Consumer<Condition>`` 。
      ``cond`` には、この ``Condition`` 自身が渡される。)

    Example:
        >>> Condition(lambda: 1 < 2).if_then_else(
        ...     lambda: print("真"), lambda: print("偽"))
        真
    """

    def __init__(self, supplier):
        """条件オブジェクトを作る。

        Args:
            supplier: 引数なしで呼び出すと、真偽値として評価できる値を返す関数。
                呼び出すたびに評価されるので、ループの継続条件にも使える。
        """
        self._condition = supplier

    def evaluate(self):
        """条件を評価して、 ``bool`` で返す。"""
        return bool(self._condition())

    # ---- break / return --------------------------------------------
    def _break_(self):
        """ループを中断する( ``break`` 相当)。

        Raises:
            ConditionSignal: 発信元がこの ``Condition`` の ``break`` シグナル。
        """
        raise ConditionSignal(Signal.BREAK, self)

    def _return_(self):
        """ループを抜けて、呼び出し元まで処理を戻す( ``return`` 相当)。

        ``while_true`` / ``while_false`` は ``return`` を握りつぶさず、外へ伝える。

        Raises:
            ConditionSignal: 発信元がこの ``Condition`` の ``return`` シグナル。
        """
        raise ConditionSignal(Signal.RETURN, self)

    # ---- 分岐 -------------------------------------------------------
    def if_then_else(self, then, else_):
        """条件が真なら ``then`` 、偽なら ``else_`` を実行する。

        Args:
            then: 真のときに実行するコールバック。
            else_: 偽のときに実行するコールバック。
        """
        branch(self.evaluate(), then, else_, self)

    def if_true(self, then):
        """条件が真のときだけ ``then`` を実行する。

        Args:
            then: 真のときに実行するコールバック。
        """
        self.if_then_else(then, noop)

    def if_false(self, else_):
        """条件が偽のときだけ ``else_`` を実行する。

        Args:
            else_: 偽のときに実行するコールバック。
        """
        self.if_then_else(noop, else_)

    # ---- 繰り返し ---------------------------------------------------
    def while_true(self, body):
        """条件が真である間、 ``body`` を繰り返し実行する。

        ``body`` の中で ``cond._break_()`` を呼ぶと、ループを終了する。
        ``cond._return_()`` を呼ぶと、 :class:`ConditionSignal` が外へ伝わる。

        Args:
            body: 繰り返す処理のコールバック。
        """
        self._while(self.evaluate, body)

    def while_false(self, body):
        """条件が偽である間、 ``body`` を繰り返し実行する。

        Args:
            body: 繰り返す処理のコールバック。
        """
        self._while(lambda: not self.evaluate(), body)

    def _while(self, predicate, body):
        """``predicate`` が真である間、 ``body`` を繰り返す(共通の実装)。

        ``while`` 文は使わず、「無限イテレータ → ``takewhile`` で継続判定 →
        ``map`` で本体を実行 → ``consume`` で消費」という流れで繰り返す。
        自分の ``break`` だけを握りつぶし、それ以外のシグナルは再送出する。

        Args:
            predicate: 引数なしで継続可否を返す関数。
            body: 繰り返す処理のコールバック。
        """
        try:
            consume(map(
                lambda _: call(body, self),
                takewhile(lambda _: predicate(), repeat(None)),
            ))
        except ConditionSignal as signal:
            branch(
                signal.is_break() and signal.is_from(self),
                noop,                       # 自分の break: ループ終了
                lambda: raise_(signal),     # return / 他人のシグナル: 外へ伝える
            )

    def __repr__(self):
        return f"{type(self).__name__}[{self._condition!r}]"
