## User Question
```text
Show me the top 5 customer states by revenue with their month-over-month growth rate, average order value trend, and customer retention. Include only states where average delivery time is under 10 days and compare Q1 vs Q4 performance
```

## Genie Query
```sql
WITH state_metrics AS (
  SELECT
    `Customer State`,
    DATE_TRUNC('MONTH', `order_date`) AS `month`,
    `Quarter`,
    MEASURE(`Total Revenue (GMV)`) AS `revenue`,
    MEASURE(`Average Order Value (AOV)`) AS `avg_order_value`,
    MEASURE(`Active Customers`) AS `active_customers`,
    MEASURE(`Avg Delivery Time`) AS `avg_delivery_time`
  FROM
    `wl_internal`.`olist_ecommerce`.`fact_sales_metric_view`
  WHERE
    `Customer State` IS NOT NULL
  GROUP BY
    ALL
  HAVING
    `avg_delivery_time` < 10
),
ranked_states AS (
  SELECT
    `Customer State`,
    SUM(`revenue`) AS `total_revenue`,
    ROW_NUMBER() OVER (ORDER BY SUM(`revenue`) DESC) AS `revenue_rank`
  FROM
    state_metrics
  GROUP BY
    `Customer State`
)
SELECT
  sm.`Customer State`,
  sm.`month`,
  sm.`Quarter`,
  sm.`revenue`,
  sm.`avg_order_value`,
  sm.`active_customers`,
  TRY_DIVIDE(
    sm.`revenue` - LAG(sm.`revenue`) OVER (PARTITION BY sm.`Customer State` ORDER BY sm.`month`),
    LAG(sm.`revenue`) OVER (PARTITION BY sm.`Customer State` ORDER BY sm.`month`)
  )
    * 100 AS `month_over_month_growth`
FROM
  state_metrics sm
WHERE
  sm.`Customer State` IN (
    SELECT
      `Customer State`
    FROM
      ranked_states
    WHERE
      `revenue_rank` <= 5
  )
ORDER BY
  sm.`Customer State`,
  sm.`month`
```

## Resulting `visual.json` (or key configuration elements)
```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.5.0/schema.json",
  "name": "c8a4e2f1b5d9473a9e6b",
  "position": {
    "x": 20,
    "y": 20,
    "z": 0,
    "height": 680,
    "width": 1240,
    "tabOrder": 0
  },
  "visual": {
    "visualType": "lineClusteredColumnComboChart",
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
              "active": true,
              "format": "G"
            },
            {
              "field": {
                "Column": {
                  "Expression": {
                    "SourceRef": {
                      "Entity": "dim_date"
                    }
                  },
                  "Property": "quarter_name"
                }
              },
              "queryRef": "dim_date.quarter_name",
              "nativeQueryRef": "quarter_name",
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
                      "Entity": "dim_customer"
                    }
                  },
                  "Property": "state"
                }
              },
              "queryRef": "dim_customer.state",
              "nativeQueryRef": "state"
            }
          ]
        },
        "Tooltips": {
          "projections": [
            {
              "field": {
                "Measure": {
                  "Expression": {
                    "SourceRef": {
                      "Entity": "fact_sales"
                    }
                  },
                  "Property": "Average Order Value (AOV)"
                }
              },
              "queryRef": "fact_sales.Average Order Value (AOV)",
              "nativeQueryRef": "Average Order Value (AOV)"
            },
            {
              "field": {
                "Measure": {
                  "Expression": {
                    "SourceRef": {
                      "Entity": "fact_sales"
                    }
                  },
                  "Property": "Active Customers"
                }
              },
              "queryRef": "fact_sales.Active Customers",
              "nativeQueryRef": "Active Customers"
            },
            {
              "field": {
                "Measure": {
                  "Expression": {
                    "SourceRef": {
                      "Entity": "fact_sales"
                    }
                  },
                  "Property": "Avg Delivery Time"
                }
              },
              "queryRef": "fact_sales.Avg Delivery Time",
              "nativeQueryRef": "Avg Delivery Time"
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
                  "Property": "Total Revenue (GMV)"
                }
              },
              "queryRef": "fact_sales.Total Revenue (GMV)",
              "nativeQueryRef": "Total Revenue (GMV)"
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
            "show": {
              "expr": {
                "Literal": {
                  "Value": "true"
                }
              }
            },
            "titleText": {
              "expr": {
                "Literal": {
                  "Value": "'Month'"
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
      "valueAxis": [
        {
          "properties": {
            "show": {
              "expr": {
                "Literal": {
                  "Value": "true"
                }
              }
            },
            "gridlineShow": {
              "expr": {
                "Literal": {
                  "Value": "true"
                }
              }
            },
            "titleText": {
              "expr": {
                "Literal": {
                  "Value": "'Total Revenue (GMV)'"
                }
              }
            },
            "invertAxis": {
              "expr": {
                "Literal": {
                  "Value": "false"
                }
              }
            },
            "logAxisScale": {
              "expr": {
                "Literal": {
                  "Value": "false"
                }
              }
            },
            "alignZeros": {
              "expr": {
                "Literal": {
                  "Value": "false"
                }
              }
            }
          }
        }
      ],
      "lineStyles": [
        {
          "properties": {
            "areaShow": {
              "expr": {
                "Literal": {
                  "Value": "false"
                }
              }
            },
            "showMarker": {
              "expr": {
                "Literal": {
                  "Value": "true"
                }
              }
            },
            "strokeWidth": {
              "expr": {
                "Literal": {
                  "Value": "3D"
                }
              }
            }
          }
        }
      ],
      "markers": [
        {
          "properties": {
            "borderShow": {
              "expr": {
                "Literal": {
                  "Value": "true"
                }
              }
            }
          }
        }
      ],
      "labels": [
        {
          "properties": {
            "show": {
              "expr": {
                "Literal": {
                  "Value": "false"
                }
              }
            },
            "labelDisplayUnits": {
              "expr": {
                "Literal": {
                  "Value": "0D"
                }
              }
            }
          }
        }
      ],
      "legend": [
        {
          "properties": {
            "show": {
              "expr": {
                "Literal": {
                  "Value": "true"
                }
              }
            },
            "position": {
              "expr": {
                "Literal": {
                  "Value": "'Right'"
                }
              }
            },
            "titleText": {
              "expr": {
                "Literal": {
                  "Value": "'Customer State'"
                }
              }
            },
            "legendMarkerRendering": {
              "expr": {
                "Literal": {
                  "Value": "'markerOnly'"
                }
              }
            }
          }
        }
      ],
      "seriesLabels": [
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
      "referenceLine": [
        {
          "properties": {
            "show": {
              "expr": {
                "Literal": {
                  "Value": "true"
                }
              }
            },
            "displayName": {
              "expr": {
                "Literal": {
                  "Value": "'Min line 1'"
                }
              }
            },
            "value": {
              "expr": {
                "Aggregation": {
                  "Expression": {
                    "SelectRef": {
                      "ExpressionName": "fact_sales.Total Revenue (GMV)"
                    }
                  },
                  "Function": 3
                }
              }
            },
            "dataLabelShow": {
              "expr": {
                "Literal": {
                  "Value": "true"
                }
              }
            },
            "shadeShow": {
              "expr": {
                "Literal": {
                  "Value": "false"
                }
              }
            },
            "autoScale": {
              "expr": {
                "Literal": {
                  "Value": "false"
                }
              }
            }
          },
          "selector": {
            "metadata": "fact_sales.Total Revenue (GMV)",
            "id": "1"
          }
        },
        {
          "properties": {
            "show": {
              "expr": {
                "Literal": {
                  "Value": "true"
                }
              }
            },
            "displayName": {
              "expr": {
                "Literal": {
                  "Value": "'Max line 1'"
                }
              }
            },
            "value": {
              "expr": {
                "Aggregation": {
                  "Expression": {
                    "SelectRef": {
                      "ExpressionName": "fact_sales.Total Revenue (GMV)"
                    }
                  },
                  "Function": 4
                }
              }
            },
            "dataLabelShow": {
              "expr": {
                "Literal": {
                  "Value": "true"
                }
              }
            },
            "shadeShow": {
              "expr": {
                "Literal": {
                  "Value": "false"
                }
              }
            }
          },
          "selector": {
            "metadata": "fact_sales.Total Revenue (GMV)",
            "id": "2"
          }
        },
        {
          "properties": {
            "show": {
              "expr": {
                "Literal": {
                  "Value": "true"
                }
              }
            },
            "displayName": {
              "expr": {
                "Literal": {
                  "Value": "'Average line 1'"
                }
              }
            },
            "value": {
              "expr": {
                "Aggregation": {
                  "Expression": {
                    "SelectRef": {
                      "ExpressionName": "fact_sales.Total Revenue (GMV)"
                    }
                  },
                  "Function": 1
                }
              }
            },
            "dataLabelShow": {
              "expr": {
                "Literal": {
                  "Value": "true"
                }
              }
            }
          },
          "selector": {
            "metadata": "fact_sales.Total Revenue (GMV)",
            "id": "3"
          }
        },
        {
          "properties": {
            "show": {
              "expr": {
                "Literal": {
                  "Value": "true"
                }
              }
            },
            "displayName": {
              "expr": {
                "Literal": {
                  "Value": "'Median line 1'"
                }
              }
            },
            "value": {
              "expr": {
                "Aggregation": {
                  "Expression": {
                    "SelectRef": {
                      "ExpressionName": "fact_sales.Total Revenue (GMV)"
                    }
                  },
                  "Function": 6
                }
              }
            },
            "dataLabelShow": {
              "expr": {
                "Literal": {
                  "Value": "true"
                }
              }
            }
          },
          "selector": {
            "metadata": "fact_sales.Total Revenue (GMV)",
            "id": "4"
          }
        },
        {
          "properties": {
            "show": {
              "expr": {
                "Literal": {
                  "Value": "true"
                }
              }
            },
            "displayName": {
              "expr": {
                "Literal": {
                  "Value": "'Percentile line 1'"
                }
              }
            },
            "value": {
              "expr": {
                "Percentile": {
                  "Expression": {
                    "SelectRef": {
                      "ExpressionName": "fact_sales.Total Revenue (GMV)"
                    }
                  },
                  "K": 0.9
                }
              }
            },
            "dataLabelShow": {
              "expr": {
                "Literal": {
                  "Value": "true"
                }
              }
            }
          },
          "selector": {
            "metadata": "fact_sales.Total Revenue (GMV)",
            "id": "5"
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
            "metadata": "fact_sales.Total Revenue (GMV)"
          }
        }
      ]
    },
    "visualContainerObjects": {
      "title": [
        {
          "properties": {
            "show": {
              "expr": {
                "Literal": {
                  "Value": "true"
                }
              }
            },
            "text": {
              "expr": {
                "Literal": {
                  "Value": "'Top 5 Customer States - Revenue Trends Over Time'"
                }
              }
            }
          }
        }
      ],
      "background": [
        {
          "properties": {
            "show": {
              "expr": {
                "Literal": {
                  "Value": "true"
                }
              }
            },
            "transparency": {
              "expr": {
                "Literal": {
                  "Value": "0D"
                }
              }
            }
          }
        }
      ],
      "border": [
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
      "dropShadow": [
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
      "lockAspect": [
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
      ]
    },
    "drillFilterOtherVisuals": true
  },
  "filterConfig": {
    "filters": [
      {
        "name": "e5f6a7b8c9d0e1f2a3b4",
        "field": {
          "Measure": {
            "Expression": {
              "SourceRef": {
                "Entity": "fact_sales"
              }
            },
            "Property": "Avg Delivery Time"
          }
        },
        "type": "Advanced",
        "filter": {
          "Version": 2,
          "From": [
            {
              "Name": "f",
              "Entity": "fact_sales",
              "Type": 0
            }
          ],
          "Where": [
            {
              "Condition": {
                "Comparison": {
                  "ComparisonKind": 4,
                  "Left": {
                    "Measure": {
                      "Expression": {
                        "SourceRef": {
                          "Source": "f"
                        }
                      },
                      "Property": "Avg Delivery Time"
                    }
                  },
                  "Right": {
                    "Literal": {
                      "Value": "10L"
                    }
                  }
                }
              }
            }
          ]
        }
      },
      {
        "name": "f6a7b8c9d0e1f2a3b4c5",
        "field": {
          "Column": {
            "Expression": {
              "SourceRef": {
                "Entity": "dim_customer"
              }
            },
            "Property": "state"
          }
        },
        "type": "TopN",
        "filter": {
          "Version": 2,
          "From": [
            {
              "Name": "subquery",
              "Expression": {
                "Subquery": {
                  "Query": {
                    "Version": 2,
                    "From": [
                      {
                        "Name": "d1",
                        "Entity": "dim_customer",
                        "Type": 0
                      },
                      {
                        "Name": "f",
                        "Entity": "fact_sales",
                        "Type": 0
                      }
                    ],
                    "Select": [
                      {
                        "Column": {
                          "Expression": {
                            "SourceRef": {
                              "Source": "d1"
                            }
                          },
                          "Property": "state"
                        },
                        "Name": "field"
                      }
                    ],
                    "OrderBy": [
                      {
                        "Direction": 2,
                        "Expression": {
                          "Measure": {
                            "Expression": {
                              "SourceRef": {
                                "Source": "f"
                              }
                            },
                            "Property": "Total Revenue (GMV)"
                          }
                        }
                      }
                    ],
                    "Top": 5
                  }
                }
              },
              "Type": 2
            },
            {
              "Name": "d1",
              "Entity": "dim_customer",
              "Type": 0
            }
          ],
          "Where": [
            {
              "Condition": {
                "In": {
                  "Expressions": [
                    {
                      "Column": {
                        "Expression": {
                          "SourceRef": {
                            "Source": "d1"
                          }
                        },
                        "Property": "state"
                      }
                    }
                  ],
                  "Table": {
                    "SourceRef": {
                      "Source": "subquery"
                    }
                  }
                }
              }
            }
          ]
        }
      },
      {
        "name": "e591d859054098fbda86",
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
        "type": "Advanced"
      },
      {
        "name": "35aeee528c8cc84bafd2",
        "field": {
          "Column": {
            "Expression": {
              "SourceRef": {
                "Entity": "dim_date"
              }
            },
            "Property": "quarter_name"
          }
        },
        "type": "Categorical"
      },
      {
        "name": "db5d2eea3bc69a11ffb4",
        "field": {
          "Measure": {
            "Expression": {
              "SourceRef": {
                "Entity": "fact_sales"
              }
            },
            "Property": "Total Revenue (GMV)"
          }
        },
        "type": "Advanced"
      },
      {
        "name": "6379cdd4a37170bece82",
        "field": {
          "Measure": {
            "Expression": {
              "SourceRef": {
                "Entity": "fact_sales"
              }
            },
            "Property": "Average Order Value (AOV)"
          }
        },
        "type": "Advanced"
      },
      {
        "name": "797d066594177011980c",
        "field": {
          "Measure": {
            "Expression": {
              "SourceRef": {
                "Entity": "fact_sales"
              }
            },
            "Property": "Active Customers"
          }
        },
        "type": "Advanced"
      }
    ]
  }
}
```