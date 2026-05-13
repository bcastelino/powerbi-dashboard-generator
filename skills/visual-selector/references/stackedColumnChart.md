## User Question
```text
What are the top 3 product categories by units sold with weekend vs weekday sales split, their NPS score, freight cost ratio, and seasonal trend (Q1-Q4 breakdown)? Only include categories with more than 100 orders and a positive NPS proxy.
```

## Genie Query
```sql
WITH top_categories AS (
  SELECT
    COALESCE(`Product Category`, 'Other') AS `Product Category`,
    MEASURE(`Units Sold`) AS `Units Sold`,
    MEASURE(`Total Orders`) AS `Total Orders`,
    MEASURE(`Net Promotor Score (NPS Proxy)`) AS `NPS Proxy`
  FROM
    `wl_internal`.`olist_ecommerce`.`fact_sales_metric_view`
  GROUP BY
    ALL
  HAVING
    `Total Orders` > 100
    AND `NPS Proxy` > 0
  ORDER BY
    `Units Sold` DESC
  LIMIT 3
)
SELECT
  DATE_TRUNC('QUARTER', `order_date`) AS `Quarter`,
  COALESCE(`Product Category`, 'Other') AS `Product Category`,
  `Is Weekend`,
  MEASURE(`Units Sold`) AS `Units Sold`,
  MEASURE(`Net Promotor Score (NPS Proxy)`) AS `NPS Proxy`,
  MEASURE(`Freight Cost Ratio`) AS `Freight Cost Ratio`
FROM
  `wl_internal`.`olist_ecommerce`.`fact_sales_metric_view`
WHERE
  COALESCE(`Product Category`, 'Other') IN (
    SELECT
      `Product Category`
    FROM
      top_categories
  )
GROUP BY
  ALL
ORDER BY
  `Product Category`,
  `Quarter`,
  `Is Weekend`
```

## Resulting `visual.json` (or key configuration elements)
```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.5.0/schema.json",
  "name": "c7a2f1e0b5d64a1c9f3e",
  "position": {
    "x": 0,
    "y": 40.353475041796038,
    "z": 0,
    "height": 679.894912825412,
    "width": 1239.95223310246,
    "tabOrder": 0
  },
  "visual": {
    "visualType": "columnChart",
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
                      "Entity": "dim_date"
                    }
                  },
                  "Property": "is_weekend"
                }
              },
              "queryRef": "dim_date.is_weekend",
              "nativeQueryRef": "is_weekend"
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
                  "Property": "Net Promotor Score (NPS Proxy)"
                }
              },
              "queryRef": "fact_sales.Net Promotor Score (NPS Proxy)",
              "nativeQueryRef": "Net Promotor Score (NPS Proxy)"
            },
            {
              "field": {
                "Measure": {
                  "Expression": {
                    "SourceRef": {
                      "Entity": "fact_sales"
                    }
                  },
                  "Property": "Freight Cost Ratio"
                }
              },
              "queryRef": "fact_sales.Freight Cost Ratio",
              "nativeQueryRef": "Freight Cost Ratio"
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
                  "Property": "Units Sold"
                }
              },
              "queryRef": "fact_sales.Units Sold",
              "nativeQueryRef": "Units Sold"
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
            "direction": "Ascending"
          }
        ]
      }
    },
    "drillFilterOtherVisuals": true
  },
  "filterConfig": {
    "filters": [
      {
        "name": "c90f259664e2c8f7ced9",
        "field": {
          "Column": {
            "Expression": {
              "SourceRef": {
                "Entity": "dim_product"
              }
            },
            "Property": "category_name"
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
                        "Entity": "dim_product",
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
                          "Property": "category_name"
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
                            "Property": "Units Sold"
                          }
                        }
                      }
                    ],
                    "Top": 3
                  }
                }
              },
              "Type": 2
            },
            {
              "Name": "d1",
              "Entity": "dim_product",
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
                        "Property": "category_name"
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
        },
        "howCreated": "User"
      },
      {
        "name": "f154e6fa0c2979b9524e",
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
        "type": "Categorical",
        "howCreated": "Drill"
      },
      {
        "name": "b60f6507322dcf3c524a",
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
        "name": "1603c2a1c6222148f4d1",
        "field": {
          "Measure": {
            "Expression": {
              "SourceRef": {
                "Entity": "fact_sales"
              }
            },
            "Property": "Units Sold"
          }
        },
        "type": "Advanced"
      },
      {
        "name": "ececbde97b6bba3ac5b7",
        "field": {
          "Measure": {
            "Expression": {
              "SourceRef": {
                "Entity": "fact_sales"
              }
            },
            "Property": "Net Promotor Score (NPS Proxy)"
          }
        },
        "type": "Advanced"
      },
      {
        "name": "26a190fc0f5554c6c87c",
        "field": {
          "Measure": {
            "Expression": {
              "SourceRef": {
                "Entity": "fact_sales"
              }
            },
            "Property": "Freight Cost Ratio"
          }
        },
        "type": "Advanced"
      },
      {
        "name": "a06b07ae8d4385d87ccf",
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
        "name": "71fcc5e257d0e4e1a274",
        "field": {
          "Column": {
            "Expression": {
              "SourceRef": {
                "Entity": "dim_date"
              }
            },
            "Property": "is_weekend"
          }
        },
        "type": "Categorical"
      }
    ]
  }
}
```