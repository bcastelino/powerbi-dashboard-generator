## User Question
```text
What is the average number of daily active customers for each month? or What is the count of average active customers slice by month?
```

## Genie Query
```sql
SELECT
  /* Level 2 (Outer): Calculate the average of those daily counts per month. */
  DATE_TRUNC('MONTH', daily_date) as month_date,
  date_format(daily_date, 'MMMM yyyy') AS `Month`,
  AVG(daily_count) AS `Avg Active Users (Monthly)`
FROM
  (
    SELECT
      /* Level 1 (Inner): Count distinct users per day. */
      order_date AS daily_date,
      MEASURE(`Active Customers`) AS daily_count
    FROM
      wl_internal.olist_ecommerce.fact_sales_metric_view
    GROUP BY
      1
  )
GROUP BY
  1,
  2
ORDER BY
  1
```

## Resulting `visual.json` (or key configuration elements)
```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.5.0/schema.json",
  "name": "f1a2b3c4d5e6f7a8b9c0",
  "position": {
    "x": 20,
    "y": 20,
    "z": 0,
    "height": 680,
    "width": 1240,
    "tabOrder": 0
  },
  "visual": {
    "visualType": "barChart",
    "query": {
      "queryState": {
        "Category": {
          "projections": [
            {
              "field": {
                "Column": {
                  "Expression": {
                    "SourceRef": {
                      "Entity": "dim_date"
                    }
                  },
                  "Property": "year"
                }
              },
              "queryRef": "dim_date.year",
              "nativeQueryRef": "year",
              "active": true
            }
          ]
        },
        "Series": {
          "projections": [
            {
              "field": {
                "Column": {
                  "Expression": {
                    "SourceRef": {
                      "Entity": "dim_date"
                    }
                  },
                  "Property": "month_pad"
                }
              },
              "queryRef": "dim_date.month_pad",
              "nativeQueryRef": "month_pad"
            }
          ]
        },
        "Y": {
          "projections": [
            {
              "field": {
                "Measure": {
                  "Expression": {
                    "SourceRef": {
                      "Entity": "fact_sales"
                    }
                  },
                  "Property": "Avg Active Users (Monthly)"
                }
              },
              "queryRef": "fact_sales.Avg Active Users (Monthly)",
              "nativeQueryRef": "Avg Active Users (Monthly)"
            }
          ]
        }
      },
      "sortDefinition": {
        "sort": [
          {
            "field": {
              "Column": {
                "Expression": {
                  "SourceRef": {
                    "Entity": "dim_date"
                  }
                },
                "Property": "year"
              }
            },
            "direction": "Ascending"
          }
        ]
      }
    },
    "objects": {
      "categoryAxis": [
        {
          "properties": {
            "axisType": {
              "expr": {
                "Literal": {
                  "Value": "'Categorical'"
                }
              }
            },
            "concatenateLabels": {
              "expr": {
                "Literal": {
                  "Value": "false"
                }
              }
            }
          }
        }
      ],
      "error": [
        {
          "properties": {
            "enabled": {
              "expr": {
                "Literal": {
                  "Value": "false"
                }
              }
            }
          },
          "selector": {
            "metadata": "fact_sales.Avg Active Users (Monthly)"
          }
        }
      ],
      "labels": [
        {
          "properties": {
            "show": {
              "expr": {
                "Literal": {
                  "Value": "true"
                }
              }
            }
          }
        }
      ],
      "totals": [
        {
          "properties": {
            "show": {
              "expr": {
                "Literal": {
                  "Value": "true"
                }
              }
            }
          }
        }
      ],
      "ribbonBands": [
        {
          "properties": {
            "show": {
              "expr": {
                "Literal": {
                  "Value": "true"
                }
              }
            }
          }
        }
      ],
      "valueAxis": [
        {
          "properties": {
            "gridlineStyle": {
              "expr": {
                "Literal": {
                  "Value": "'dotted'"
                }
              }
            }
          }
        }
      ],
      "zoom": [
        {
          "properties": {
            "show": {
              "expr": {
                "Literal": {
                  "Value": "false"
                }
              }
            }
          }
        }
      ],
      "legend": [
        {
          "properties": {
            "position": {
              "expr": {
                "Literal": {
                  "Value": "'Right'"
                }
              }
            }
          }
        }
      ]
    },
    "drillFilterOtherVisuals": true
  }
}
```