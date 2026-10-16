---
status: Accepted
date: 2026-10-16
systems: [ACE, UDS]
tags: [プラン変更, neos_item_cd, バンドコード, 判定ロジック]
---

# ADR-0010: プラン変更は、DBのNeOS品目CDと連携値の差異で判定して上書きする

- 決定者・関係者: 野澤有沙、佐々木航太（UDS）
- 出典: 文字起こし 01:09:53〜01:11:16（Geminiメモ: https://docs.google.com/document/d/1n-Av2kjhakuFZvuhaYh-807svACt8pbR069ukM9-Nd4）

## コンテキスト
- ACE移行後、UNIS品目CDとバンドコードの概念はなくなる。
- NeOS品目CD（neos_item_cd）は存続する。メニューコードは連携されるが、一旦、device_types（デバイス種別マスタ）には入れず、持っておくだけにする。
- ACEのcontract.tsvには、必ずNeOS品目CDが入る。

## 決定
- DBに登録済みのNeOS品目CDと、連携されたNeOS品目CDに差異があれば、プラン変更とみなして上書きする。
- 従来のバンドコード・UNIS品目CDを使った判定は不要になる。

## 理由
- ACEではNeOS品目CDが必ず連携されるため、シンプルな判定で足りる。

## 補足
- UDSのサービスコード（デバイス側の概念）は変わらない。新しい品目が増えた場合は、UDS側でサービスコードを追加する対応が必要になる（ACE側で持たせる案は断られた）。

## 関連
- ADR-0006、ADR-0009
