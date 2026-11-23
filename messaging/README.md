# messaging — メッセージングを徹底するPythonライブラリ

`if` / `while` / `for` 文を使わず、オブジェクトへメッセージを送って制御するためのライブラリです。
先生のJavaライブラリ(`Condition` / `Interval` / `ValueHolder`)をPythonに移植しました。

## 使い方

```python
from messaging import Condition, Interval, ValueHolder, ConditionSignal

# 分岐
Condition(lambda: 1 < 2).if_then_else(lambda: print("真"), lambda: print("偽"))

# 繰り返し(while)
n = ValueHolder(0)
Condition(lambda: n.get() < 3).while_true(
    lambda: print(n.get_and_set_do(lambda x: x + 1)))

# 繰り返し(for)と break
def body(v, interval):
    Condition(lambda: v > 2).if_true(interval._break_)
    print(v)
Interval(0, lambda v: v < 100, lambda v: v + 1).for_each(body)

# return(外まで抜ける)
try:
    Condition(lambda: True).while_true(lambda c: c._return_())
except ConditionSignal as s:
    s.is_return_true(lambda: print("return を受け取りました"))
```

コールバックは「引数なし」でも「引数あり(自分自身が渡される)」でもかまいません。
引数の個数を見て自動で振り分けます(Javaのオーバーロードの代わり)。

* `Condition` のコールバック: `()` または `(cond)`
* `Interval.for_each` のコールバック: `()` / `(値)` / `(値, interval)`

## Java版との対応

| Java | Python | 備考 |
|---|---|---|
| `Condition` | `Condition` | `ifTrue` → `if_true` など |
| `ConditionException` | `ConditionSignal` | 共通の基底クラス `Signal` を継承 |
| `Interval` | `Interval` | `stop` → `keep_going` |
| `IntervalException` | `IntervalSignal` | 共通の基底クラス `Signal` を継承 |
| `ValueHolder` | `ValueHolder` | `getAndSetDo` → `get_and_set_do` など |

## Java版からの変更点

1. **then/elseの取り違えを修正。** Java版(デコンパイル結果)の `ifThenElse(Runnable, Runnable)` と
   `isBreakThenElse` などは、then側でも else側のコールバックを呼んでいました。
2. **break/returnの判定を、発信元オブジェクトの同一性(`is`)に変更。**
   Java版はクラス名を含む文字列で判定していたため、ネストしたループで内側と外側を区別できませんでした。
3. **`ConditionException` と `IntervalException` の重複を `Signal` に統合。**
4. **`Interval` の `stop` を `keep_going` に改名。** 「真の間は続ける」条件なので、名前を実態に合わせました。
5. **ライブラリ内部にも `if` / `while` / `for` 文を使っていません。**
   分岐は辞書ディスパッチ、繰り返しは `itertools` + `deque` で実現しています。
   `test_messaging.py` の `NoControlStatementsTest` が、ASTを調べて自動で確認します。

## 注意

* `ValueHolder` の `set` / `set_do` / `get_and_set_do` は、Java版と同じく **更新前の値** を返します。
* ラムダ式は式しか書けないので、複数行の処理は `def` で書きます(制御はメッセージで行います)。
* コールバックの `lambda x=x: ...` のようなデフォルト引数は、上書きされません。

## ファイル構成

```
messaging/
  __init__.py      公開API
  _dispatch.py     内部の分岐・繰り返しの土台(辞書ディスパッチ、引数の個数による振り分け)
  signals.py       Signal(break/returnを運ぶ例外の基底クラス)
  value_holder.py  ValueHolder
  condition.py     Condition, ConditionSignal
  interval.py      Interval, IntervalSignal
  example.py       Java版 Example の移植(test1〜test5)
  test_messaging.py テスト
```

## 実行

```
python -m messaging.example
python -m unittest messaging.test_messaging -v
```

Python 3.8以上が必要です( `itertools.accumulate` の `initial` を使用)。
