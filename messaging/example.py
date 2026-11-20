"""使用例。Java版の ``Example.java`` ( ``test1`` ～ ``test5`` )を移植したもの。

実行方法(プロジェクトの親ディレクトリで)::

    python -m messaging.example

このファイルも、利用者側のコードとして ``if`` / ``while`` / ``for`` 文を使っていない。
(複数行の処理は ``def`` で書くが、制御はすべてメッセージで行う。)
"""

from .condition import Condition, ConditionSignal
from .interval import Interval, IntervalSignal
from .value_holder import ValueHolder


def section(func):
    """関数の実行前に、関数名の見出しを表示するデコレータ。

    Java版の ``new Throwable().getStackTrace()[0].getMethodName()`` に相当する。
    """
    def wrapper():
        print(f"\n--- {func.__name__} ---")
        func()
    wrapper.__name__ = func.__name__
    return wrapper


def ask_yes_no(message):
    """はい/いいえを尋ねる。GUIが使えなければコンソールで尋ねる。

    Java版の ``JOptionPane.showConfirmDialog`` を、 ``tkinter`` に置き換えたもの。

    Args:
        message: 質問文。

    Returns:
        「はい」なら ``True`` 。
    """
    def gui():
        import tkinter
        from tkinter import messagebox
        root = tkinter.Tk()
        root.withdraw()
        try:
            return messagebox.askyesno("質問", message, parent=root)
        finally:
            root.destroy()

    try:
        return gui()
    except Exception:
        return input(f"{message} (y/n): ").strip().lower().startswith("y")


def show_info(message):
    """情報を表示する。GUIが使えなければコンソールに出力する。

    Args:
        message: 表示する文。
    """
    def gui():
        import tkinter
        from tkinter import messagebox
        root = tkinter.Tk()
        root.withdraw()
        try:
            messagebox.showinfo("情報", message, parent=root)
        finally:
            root.destroy()

    try:
        gui()
    except Exception:
        print(message)


@section
def test1():
    """Condition.if_then_else: 引数なし/ありの両方のコールバックを使う。"""
    answered_yes = ask_yes_no("学問をしていますか？")
    cond = Condition(lambda: answered_yes)

    cond.if_then_else(
        lambda: print("これからも学問を続けてください。"),
        lambda: print("学問は学びを問うこと、学びを疑問文(5W1H)にすることから始めてください。"),
    )
    cond.if_then_else(
        lambda: show_info("これからも学問を続けてください。"),
        lambda: show_info("学問は学びを問うこと、学びを疑問文(5W1H)にすることから始めてください。"),
    )


@section
def test2():
    """while_true / while_false / Interval.for_each の基本形。"""
    holder = ValueHolder(0)

    # 0 から 99 まで表示(更新前の値を返す get_and_set_do を使う)
    Condition(lambda: holder.get() < 100).while_true(
        lambda: print(holder.get_and_set_do(lambda n: n + 1), end=" "))
    print()

    # 99 から 0 まで表示(条件が偽である間)
    holder.set(99)

    def count_down():
        print(holder.get(), end=" ")
        holder.set_do(lambda n: n - 1)

    Condition(lambda: holder.get() < 0).while_false(count_down)
    print()

    # 0 から 100 までの偶数を表示
    Interval(0, lambda v: v <= 100, lambda v: v + 1).for_each(
        lambda v: Condition(lambda: v % 2 == 0).if_true(
            lambda: print(v, end=" ")))
    print()


@section
def test3():
    """break: ループの中断。"""
    holder = ValueHolder(0)

    def body(cond):
        Condition(lambda: holder.get() > 100).if_true(cond._break_)
        print(holder.get(), end=" ")
        holder.set_do(lambda n: n + 1)

    Condition(lambda: True).while_true(body)
    print()

    def interval_body(value, interval):
        Condition(lambda: value < 0).if_true(interval._break_)
        print(value, end=" ")

    Interval(100, lambda v: v >= -100, lambda v: v - 1).for_each(interval_body)
    print()


@section
def test4():
    """return: 呼び出し元まで抜ける(Condition版)。"""
    try:
        holder = ValueHolder(0)

        def body(cond):
            Condition(lambda: holder.get() > 100).if_true(cond._return_)
            print(holder.get(), end=" ")
            holder.set_do(lambda n: n + 1)

        Condition(lambda: True).while_true(body)
    except ConditionSignal as signal:
        signal.is_return_true(lambda: print())


@section
def test5():
    """return: 呼び出し元まで抜ける(Interval版)。"""
    try:
        def body(value, interval):
            Condition(lambda: value < 0).if_true(interval._return_)
            print(value, end=" ")

        Interval(100, lambda v: v >= -100, lambda v: v - 1).for_each(body)
    except IntervalSignal as signal:
        signal.is_return_true(lambda: print())


def main():
    """test1 ～ test5 を順に実行する。"""
    test1()
    test2()
    test3()
    test4()
    test5()
    print()


# ``if __name__ == "__main__":`` も使わず、Condition で書く。
Condition(lambda: __name__ == "__main__").if_true(main)
