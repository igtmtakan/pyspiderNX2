# PySpider パフォーマンス最適化ガイド

このドキュメントでは、PySpider のパフォーマンスを最適化するための機能と使用方法について説明します。

## 目次

1. [概要](#概要)
2. [メモリ使用量の最適化](#メモリ使用量の最適化)
3. [コネクションプールの最適化](#コネクションプールの最適化)
4. [最適化されたフェッチャー](#最適化されたフェッチャー)
5. [使用例](#使用例)
6. [ベストプラクティス](#ベストプラクティス)
7. [トラブルシューティング](#トラブルシューティング)

## 概要

PySpider のパフォーマンスを最適化するために、以下の機能が実装されています：

1. **メモリ使用量の最適化**：メモリ使用量を監視し、必要に応じてガベージコレクションを実行します。
2. **コネクションプールの最適化**：ワークロードに基づいてコネクションプールのサイズを動的に調整します。
3. **最適化されたフェッチャー**：上記の最適化機能を組み込んだ非同期フェッチャーを提供します。

これらの機能を使用することで、PySpider のパフォーマンスと安定性を向上させることができます。

## メモリ使用量の最適化

`MemoryOptimizer` クラスは、メモリ使用量を監視し、必要に応じてガベージコレクションを実行します。

### 主な機能

- メモリ使用率の監視
- 設定可能なしきい値に基づくガベージコレクションの実行
- メモリ使用量のメトリクス収集

### 使用方法

```python
from pyspider.libs.memory_optimizer import memory_optimizer

# 自動最適化を開始
memory_optimizer.start()

# 手動でメモリ使用量をチェック
memory_usage = memory_optimizer.check_memory()
print(f"Memory usage: {memory_usage['percent']:.2f}%")

# 手動でメモリを最適化
optimization_result = memory_optimizer.optimize_memory()
print(f"Memory saved: {optimization_result['saved']['rss'] / (1024 * 1024):.2f} MB")

# 自動最適化を停止
memory_optimizer.stop()
```

### 設定オプション

- `max_memory_percent`：最適化を実行するメモリ使用率のしきい値（デフォルト：80%）
- `gc_interval`：ガベージコレクション間の最小間隔（秒）（デフォルト：60秒）
- `check_interval`：メモリチェック間の間隔（秒）（デフォルト：30秒）
- `auto_optimize`：自動最適化を有効にするかどうか（デフォルト：True）

## コネクションプールの最適化

`ConnectionPoolOptimizer` クラスは、ワークロードに基づいてコネクションプールのサイズを動的に調整します。

### 主な機能

- ワークロードに基づくプールサイズの動的調整
- 設定可能な最小・最大プールサイズ
- プールサイズのメトリクス収集

### 使用方法

```python
from pyspider.fetcher.connection_pool_optimizer import connection_pool_optimizer

# 自動最適化を開始
connection_pool_optimizer.start()

# アクティブな接続数を設定
connection_pool_optimizer.set_active_connections(10)

# キューサイズを設定
connection_pool_optimizer.set_queue_size(20)

# 手動でプールサイズを最適化
optimization_result = connection_pool_optimizer.optimize_pool_size()
print(f"Pool size {optimization_result['action']} from {optimization_result['before']} to {optimization_result['after']}")

# プール統計を取得
pool_stats = connection_pool_optimizer.get_pool_stats()
print(f"Pool utilization: {pool_stats['utilization'] * 100:.2f}%")

# 自動最適化を停止
connection_pool_optimizer.stop()
```

### 設定オプション

- `min_pool_size`：最小プールサイズ（デフォルト：10）
- `max_pool_size`：最大プールサイズ（デフォルト：200）
- `initial_pool_size`：初期プールサイズ（デフォルト：50）
- `check_interval`：プールサイズチェック間の間隔（秒）（デフォルト：30秒）
- `scale_factor`：キューサイズに基づくスケールアップ係数（デフォルト：1.5）
- `scale_down_threshold`：スケールダウンのしきい値（デフォルト：0.3）
- `auto_optimize`：自動最適化を有効にするかどうか（デフォルト：True）

## 最適化されたフェッチャー

`OptimizedAsyncFetcher` クラスは、メモリ使用量の最適化とコネクションプールの最適化を組み込んだ非同期フェッチャーです。

### 主な機能

- 非同期 HTTP リクエスト
- メモリ使用量の最適化
- コネクションプールの最適化
- 詳細なエラーハンドリング
- メトリクス収集

### 使用方法

```python
import asyncio
from pyspider.fetcher.optimized_async_fetcher import OptimizedAsyncFetcher

async def main():
    # フェッチャーを作成
    fetcher = OptimizedAsyncFetcher(
        poolsize=50,
        timeout=60,
        user_agent='PySpider/1.0',
        auto_optimize=True
    )
    
    try:
        # フェッチャーを初期化
        await fetcher.init()
        
        # タスクを作成
        task = {
            'taskid': 'example',
            'project': 'example',
            'url': 'https://example.com',
            'fetch': {
                'method': 'GET',
                'headers': {
                    'User-Agent': 'PySpider/1.0'
                }
            }
        }
        
        # タスクをフェッチ
        result = await fetcher.async_fetch(task)
        
        print(f"Status code: {result['status_code']}")
        print(f"Content length: {len(result['content'])}")
        print(f"Time: {result['time']:.2f}s")
        
        # フェッチャーの統計を取得
        stats = fetcher.get_stats()
        print(f"Active connections: {stats['active_connections']}")
        print(f"Queue size: {stats['queue_size']}")
        print(f"Pool size: {stats['pool_size']}")
    finally:
        # フェッチャーを閉じる
        await fetcher.close()

asyncio.run(main())
```

### 設定オプション

- `poolsize`：コネクションプールのサイズ（デフォルト：50）
- `timeout`：デフォルトのタイムアウト（秒）（デフォルト：60秒）
- `user_agent`：ユーザーエージェント
- `proxy`：プロキシ
- `memory_check_interval`：メモリチェック間の間隔（秒）（デフォルト：60秒）
- `pool_check_interval`：プールサイズチェック間の間隔（秒）（デフォルト：30秒）
- `auto_optimize`：自動最適化を有効にするかどうか（デフォルト：True）

## 使用例

`examples/optimized_fetcher_example.py` は、最適化されたフェッチャーの使用例を提供します。

```bash
python examples/optimized_fetcher_example.py --poolsize 50 --timeout 60
```

このスクリプトは、以下の機能を示しています：

1. 単一 URL のフェッチ
2. 複数 URL の並行フェッチ
3. パフォーマンスベンチマーク

## ベストプラクティス

### メモリ使用量の最適化

1. **適切なしきい値の設定**：`max_memory_percent` を環境に合わせて調整します。メモリが限られている環境では低い値（例：70%）を、メモリが豊富な環境では高い値（例：90%）を設定します。
2. **適切な間隔の設定**：`gc_interval` と `check_interval` を調整して、過度なガベージコレクションを避けます。
3. **メモリリークの監視**：メモリ使用量が継続的に増加する場合は、メモリリークの可能性があります。

### コネクションプールの最適化

1. **適切なプールサイズの設定**：`min_pool_size` と `max_pool_size` を環境に合わせて調整します。
2. **スケール係数の調整**：`scale_factor` を調整して、プールサイズの変動を制御します。
3. **プール使用率の監視**：プール使用率が継続的に高い場合は、`max_pool_size` を増やすことを検討します。

### 最適化されたフェッチャー

1. **適切なタイムアウトの設定**：`timeout` を対象サイトに合わせて調整します。
2. **エラーハンドリングの実装**：エラーを適切に処理し、必要に応じてリトライします。
3. **メトリクスの監視**：フェッチャーのメトリクスを監視して、パフォーマンスの問題を特定します。

## トラブルシューティング

### メモリ使用量の問題

1. **メモリ使用量が高い**：
   - `max_memory_percent` を下げる
   - `gc_interval` を短くする
   - メモリリークの可能性を調査する

2. **ガベージコレクションが頻繁に実行される**：
   - `gc_interval` を長くする
   - `max_memory_percent` を上げる

### コネクションプールの問題

1. **接続エラーが多い**：
   - `min_pool_size` を上げる
   - `scale_factor` を上げる
   - ネットワーク接続を確認する

2. **プールサイズが頻繁に変動する**：
   - `scale_factor` を下げる
   - `check_interval` を長くする

### フェッチャーの問題

1. **タイムアウトエラーが多い**：
   - `timeout` を長くする
   - 対象サイトの応答時間を確認する

2. **メモリ使用量が高い**：
   - 同時リクエスト数を減らす
   - `poolsize` を下げる
