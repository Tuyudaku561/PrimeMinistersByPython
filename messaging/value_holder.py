"""ラムダ式の中から書き換えられる「値の入れ物」。"""

from threading import RLock


class ValueHolder:
    """値を1つ保持する、スレッドセーフな入れ物。

    Pythonの ``lambda`` の中では代入ができず、クロージャ内の変数を
    書き換えるには ``nonlocal`` 文( ``def`` の中でしか使えない)が必要になる。
    そこで、値を入れ物に包み、 ``set`` などのメッセージで書き換える。

    Java版の ``synchronized`` は、再入可能ロック( ``RLock`` )で再現している。

    Note:
        Java版と同じく、 ``set`` ・ ``set_do`` ・ ``get_and_set_do`` は
        すべて **更新前の値** を返す。

    Example:
        >>> counter = ValueHolder(0)
        >>> counter.set_do(lambda n: n + 1)
        0
        >>> counter.get()
        1
    """

    def __init__(self, value=None):
        """入れ物を作る。

        Args:
            value: 初期値。省略すると ``None`` 。
        """
        self._value = value
        self._lock = RLock()

    def get(self):
        """現在の値を返す。"""
        with self._lock:
            return self._value

    def set(self, value):
        """値を置き換える。

        Args:
            value: 新しい値。

        Returns:
            更新前の値。
        """
        with self._lock:
            old = self._value
            self._value = value
            return old

    def set_do(self, func):
        """現在の値に ``func`` を適用した結果を、新しい値として設定する。

        Args:
            func: 現在の値を受け取り、新しい値を返す関数。

        Returns:
            更新前の値。
        """
        with self._lock:
            return self.set(func(self.get()))

    def get_and_set_do(self, func):
        """更新前の値を取り出しつつ、 ``func`` の結果で更新する。

        Java版の ``getAndSetDo`` に対応する。戻り値は :meth:`set_do` と同じ
        (更新前の値)で、「取ってから更新する」意図を名前で表している。

        Args:
            func: 現在の値を受け取り、新しい値を返す関数。

        Returns:
            更新前の値。
        """
        with self._lock:
            old = self.get()
            self.set(func(old))
            return old

    def __repr__(self):
        return f"{type(self).__name__}[{self.get()!r}]"
