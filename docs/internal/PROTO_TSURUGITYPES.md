# TsurugiDB 型と Protocol Buffers (proto) 型の対応表

## 基本対応

| TsurugiDB types | Proto Type (Scalar Value Types) |
|-----------------|---------------------------------|
| `INT` | int32, uint32, sint32, fixed32, sfixed32, bool |
| `BIGINT` | int64, uint64, sint64, fixed64, sfixed64 |
| `REAL` | double |
| `FLOAT` | float |
| `DOUBLE [PRECISION]` | double |
| `CHAR [(<fixed-length>)]` | string |
| `CHARACTER [(<fixed-length>)]` | string |
| `VARCHAR [(<varying-length>)]` | string |
| `CHAR VARYING [(<varying-length>)]` | string |
| `CHARACTER VARYING [(<varying-length>)]` | string |
| `BINARY [(<fixed-length>)]` | bytes |
| `VARBINARY [(<varying-length>)]` | bytes |
| `BINARY VARYING [(<varying-length>)]` | bytes |

______________________________________________________________________

## 将来的なサポート予定

以下の型は [Proto3 Scalar Value Types](https://protobuf.dev/programming-guides/proto3/) では直接対応していないため、\
独自の message 定義を用いてサポート予定です。\
これらの定義は [complex_types.proto](https://github.com/project-tsurugi/tsurugi-udf/blob/master/udf-plugin-builder/proto/complex_types.proto) で管理されます。

### DECIMAL

```proto
message Decimal {
    bytes unscaled_value = 1;
    sint32 exponent      = 2;
}
```

### DATE

```proto
message Date {
    sint32 days = 1;
}
```

### TIME / TIMESTAMP

```proto
message LocalDatetime {
    sint64 offset_seconds  = 1;
    uint32 nano_adjustment = 2;
}
```

### TIME WITH TIME ZONE / TIMESTAMP WITH TIME ZONE

```proto
message OffsetDatetime {
    sint64 offset_seconds   = 1;
    uint32 nano_adjustment  = 2;
    sint32 time_zone_offset = 3;
}
```

### BLOB / BINARY LARGE OBJECT

```proto
message BlobReference {
    bytes secret = 1;
}
```

### CLOB / CHAR LARGE OBJECT / CHARACTER LARGE OBJECT

```proto
message ClobReference {
    bytes secret = 1;
}
```

## 注意事項

proto で定義できる引数の入れ子の深さは最大 2 階層まで です。

### 例: 1階層の定義（OK）

```proto
message UserdefinedTwoargs {
    sint64 one = 1;
    sint64 two = 2;
}
```

### 例: 2階層の定義（OK）

```proto
message UserdefinedTwoRow {
    UserdefinedTwoargs one = 1;
    sint64 two = 2;
}
```

### 例: 3階層以上の定義（サポート対象外）

```proto
message UserdefinedThreeRow {
    UserdefinedTwoRow one = 1;
    UserdefinedTwoargs two = 2;
}
```
