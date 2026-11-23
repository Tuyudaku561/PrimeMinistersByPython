"""``for`` 文の代わりになる :class:`Interval` と、その ``break`` / ``return`` シグナル。"""

from itertools import accumulate, repeat, takewhile

from ._dispatch import branch, call, consume, noop, raise_
from .signals import Signal
from .value_holder import ValueHolder


class IntervalSignal(Signal):
    """:class:`Interval` の ``_break_`` / ``_return_`` が送出するシグナル。

    ``for_each`` は、自分が発信した ``break`` を受け止めて終了する。
    ``return`` と、他のオブジェクトが発信したシグナルは、外へ伝わる。
    """


class Interval:
    """「開始値・継続条件・増分」で表す区間。 ``for_each`` で繰り返す。

    C言語風の ``for (v = start; keep_going(v); v = step(v))`` に対応する。

    ``for_each`` のコールバックは、次のどの形でもよい
    (引数の個数を見て、自動で振り分ける)。

    * 引数なし          : ``lambda: ...``
    * 引数1つ(値)      : ``lambda v: ...``      (Java版の ``Consumer<Value>`` )
    * 引数2つ(値, 区間) : ``lambda v, itv: ...`` (Java版の ``BiConsumer<Value, Interval>`` )

    Note:
        Java版では、継続条件の引数名が ``stop`` だったが、実際には
        「真の間は続ける」条件(例: ``v <= 100`` )として使われている。
        紛らわしいため、Python版では ``keep_going`` と名付けた。

    Example:
        >>> Interval(0, lambda v: v < 3, lambda v: v + 1).for_each(print)
        0
        1
        2
    """

    def __init__(self, start, keep_going, step):
        """区間を作る。

        Args:
            start: 開始値。
            keep_going: 値を受け取り、繰り返しを続けるなら真を返す関数。
                (Java版の ``stop`` に対応する。)
            step: 値を受け取り、次の値を返す関数。
        """
        self._start = ValueHolder(start)
        self._keep_going = keep_going
        self._step = step

    # ---- break / return --------------------------------------------
    def _break_(self):
        """繰り返しを中断する( ``break`` 相当)。

        Raises:
            IntervalSignal: 発信元がこの ``Interval`` の ``break`` シグナル。
        """
        raise IntervalSignal(Signal.BREAK, self)

    def _return_(self):
        """繰り返しを抜けて、呼び出し元まで処理を戻す( ``return`` 相当)。

        Raises:
            IntervalSignal: 発信元がこの ``Interval`` の ``return`` シグナル。
        """
        raise IntervalSignal(Signal.RETURN, self)

    # ---- 繰り返し ---------------------------------------------------
    def for_each(self, body=noop):
        """区間の各値について、 ``body`` を実行する。

        ``for`` 文は使わず、「値の列を ``accumulate`` で作る → ``takewhile`` で
        継続判定 → ``map`` で本体を実行 → ``consume`` で消費」という流れで繰り返す。

        ``body`` の中で ``itv._break_()`` を呼ぶと繰り返しを終了する。
        ``itv._return_()`` を呼ぶと、 :class:`IntervalSignal` が外へ伝わる。

        Args:
            body: 各値に対する処理のコールバック。省略すると何もしない。
        """
        values = takewhile(
            self._keep_going,
            accumulate(repeat(None), lambda v, _: self._step(v),
                       initial=self._start.get()),
        )
        try:
            consume(map(lambda v: call(body, v, self), values))
        except IntervalSignal as signal:
            branch(
                signal.is_break() and signal.is_from(self),
                noop,                       # 自分の break: 繰り返し終了
                lambda: raise_(signal),     # return / 他人のシグナル: 外へ伝える
            )

    def __repr__(self):
        return (f"{type(self).__name__}"
                f"[{self._start.get()!r},{self._keep_going!r},{self._step!r}]")
