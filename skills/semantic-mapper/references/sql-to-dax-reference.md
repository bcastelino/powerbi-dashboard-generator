# Semantic Mapper Quick Reference

## SQL-to-DAX Cheat Sheet

### Aggregations
| SQL | DAX |
|---|---|
| `SUM(col)` | `SUM(table[col])` |
| `COUNT(DISTINCT col)` | `DISTINCTCOUNT(table[col])` |
| `COUNT(*)` | `COUNTROWS(table)` |
| `AVG(col)` | `AVERAGE(table[col])` |
| `MIN(col)` | `MIN(table[col])` |
| `MAX(col)` | `MAX(table[col])` |

### Division & Null Handling
| SQL | DAX |
|---|---|
| `a / NULLIF(b, 0)` | `DIVIDE(a, b)` |
| `COALESCE(a, b)` | `IF(ISBLANK(a), b, a)` |
| `NULLIF(a, b)` | `IF(a = b, BLANK(), a)` |

### Conditionals
| SQL | DAX |
|---|---|
| `CASE WHEN x THEN a ELSE b END` | `IF(x, a, b)` |
| Complex multi-CASE | `VAR ... RETURN` pattern |

### Cross-Table References
| SQL | DAX |
|---|---|
| `dim_table.column` | `RELATED('dim_table'[column])` |
| Subquery with IN | `CALCULATE(..., RELATEDTABLE(table))` |

### Time Intelligence
| YAML Window | DAX |
|---|---|
| `trailing N day` | `DATESINPERIOD(date_col, MAX(date_col), -N, DAY)` |
| `trailing N month` | `DATESINPERIOD(date_col, MAX(date_col), -N, MONTH)` |

## Currency Code Mapping
| Code | Symbol | Culture |
|---|---|---|
| `USD` | `$` | `en-US` |
| `BRL` | `R$` | `pt-BR` |
| `GBP` | `£` | `en-GB` |
| `EUR` | `€` | `de-DE` |
| `JPY` | `¥` | `ja-JP` |
