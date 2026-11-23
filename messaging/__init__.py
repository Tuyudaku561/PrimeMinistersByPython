"""メッセージングを徹底するためのライブラリ。

``if`` / ``while`` / ``for`` といった制御構文を使わず、
オブジェクトにメッセージ(メソッド呼び出し)を送ることで制御する。

Java版との対応:

=================== =========================== ==========================
Java                Python                      備考
=================== =========================== ==========================
Condition           :class:`Condition`          ifTrue → if_true など
ConditionException  :class:`ConditionSignal`    共通基底 :class:`Signal`
Interval            :class:`Interval`           stop → keep_going
IntervalException   :class:`IntervalSignal`     共通基底 :class:`Signal`
ValueHolder         :class:`ValueHolder`        getAndSetDo → get_and_set_do
=================== =========================== ==========================
"""

from .condition import Condition, ConditionSignal
from .interval import Interval, IntervalSignal
from .signals import Signal
from .value_holder import ValueHolder

__all__ = [
    "Condition",
    "ConditionSignal",
    "Interval",
    "IntervalSignal",
    "Signal",
    "ValueHolder",
]
