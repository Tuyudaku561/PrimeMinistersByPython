"""内部用の補助関数群。

このライブラリの方針は「制御構文(``if`` / ``while`` / ``for`` 文)を使わず、
オブジェクトへのメッセージ送信だけで制御する」ことである。
そのため、分岐と繰り返しの土台になる処理をこのモジュールに集める。

* 分岐は、辞書ディスパッチ ``{True: then, False: else_}[flag]`` で行う。
* 繰り返しは、イテレータ(``itertools``)を作って ``deque`` で消費することで行う。
* Java版のオーバーロード( ``Runnable`` と ``Consumer`` )は、
  :func:`call` が引数の個数を調べて振り分けることで代替する。

このモジュールの内容は公開APIではない。
"""

from collections import deque
from inspect import Parameter, signature

_POSITIONAL_KINDS = (Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD)


def choose(flag, then, else_):
    """真偽値に応じて ``then`` か ``else_`` のどちらかを選んで返す。

    ``if`` 文の代わりに辞書ディスパッチを使う。選ぶだけで、呼び出しはしない。

    Args:
        flag: 真偽値として評価できる値。
        then: ``flag`` が真のときに選ばれる値。
        else_: ``flag`` が偽のときに選ばれる値。

    Returns:
        ``then`` または ``else_`` 。
    """
    return {True: then, False: else_}[bool(flag)]


def accepted_count(func, limit):
    """``func`` に渡せる位置引数の個数を ``limit`` 以下で返す。

    * ``*args`` を受け取る関数は、 ``limit`` 個すべてを受け取れる。
    * それ以外は、「デフォルト値のない位置引数」の個数まで受け取る。
      (``lambda x=x: ...`` のようなデフォルト引数は、
      クロージャ用の工夫とみなして上書きしない。)
    * ``signature`` で調べられない呼び出し可能オブジェクトは、 ``limit`` 個受け取れるとみなす。

    Args:
        func: 呼び出し可能オブジェクト。
        limit: 渡したい引数の最大個数。

    Returns:
        実際に渡す引数の個数。
    """
    try:
        params = list(signature(func).parameters.values())
    except (TypeError, ValueError):
        return limit
    has_var = any(p.kind is Parameter.VAR_POSITIONAL for p in params)
    required = sum(
        1 for p in params
        if p.kind in _POSITIONAL_KINDS and p.default is Parameter.empty
    )
    return {True: limit, False: min(required, limit)}[has_var]


def call(func, *args):
    """``func`` が受け取れる個数だけ、先頭から引数を渡して呼び出す。

    Java版の ``Runnable`` (引数なし)と ``Consumer`` (引数あり)の
    オーバーロードを、Pythonで再現するための関数。

    Args:
        func: 呼び出す関数。引数なしでも、 ``args`` の先頭から数個を受け取る形でもよい。
        *args: 渡す候補の引数(優先順位の高い順)。

    Returns:
        ``func`` の戻り値。
    """
    return func(*args[:accepted_count(func, len(args))])


def branch(flag, then, else_, *args):
    """``flag`` に応じて ``then`` / ``else_`` の一方だけを :func:`call` で呼び出す。

    Args:
        flag: 真偽値として評価できる値。
        then: ``flag`` が真のときに呼ぶ関数。
        else_: ``flag`` が偽のときに呼ぶ関数。
        *args: :func:`call` に渡す候補の引数。

    Returns:
        呼び出した関数の戻り値。
    """
    return call(choose(flag, then, else_), *args)


def noop(*_):
    """何もしない関数。 ``ifTrue`` の「else側」などに使う。"""
    return None


def raise_(exc):
    """例外を送出する。ラムダ式(式しか書けない)の中から ``raise`` するための関数。

    Args:
        exc: 送出する例外オブジェクト。
    """
    raise exc


def consume(iterable):
    """イテラブルを最後まで読み進める( ``for`` 文の代わり)。

    Args:
        iterable: 読み進めるイテラブル。途中で例外が起きれば、そのまま伝わる。
    """
    deque(iterable, maxlen=0)
