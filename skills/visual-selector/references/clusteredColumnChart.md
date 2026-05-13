## User Question
```text
Only show me the product categories that performed well from June to November in 2017
```

## Genie Query
```sql
SELECT
  COALESCE(`Product Category`, 'Other') AS `Product Category`,
  MEASURE(`Units Sold`) AS `Units Sold`
FROM
  `wl_internal`.`olist_ecommerce`.`fact_sales_metric_view`
WHERE
  `order_date` >= '2017-06-01'
  AND `order_date` <= '2017-11-30'
  AND `Product Category` IS NOT NULL
GROUP BY
  ALL
ORDER BY
  `Units Sold` DESC
```

## Resulting `visual.json` (or key configuration elements)
```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.5.0/schema.json",
  "name": "eb3d79f04e0347a5a05d",
  "position": {
    "x": 20,
    "y": 20,
    "z": 0,
    "height": 680,
    "width": 1240,
    "tabOrder": 0
  },
  "visual": {
    "visualType": "clusteredColumnChart",
    "query": {
      "queryState": {
        "Category": {
          "projections": [
            {
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
              "queryRef": "dim_product.category_name",
              "nativeQueryRef": "category_name",
              "active": true
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
              "queryRef": "fact_sales.'Units Sold'",
              "nativeQueryRef": "Units Sold"
            }
          ]
        }
      },
      "sortDefinition": {
        "sort": [
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
            "direction": "Descending"
          }
        ],
        "isDefaultSort": true
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
                  "Value": "'Product Category'"
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
                  "Value": "true"
                }
              }
            },
            "labelDisplayUnits": {
              "expr": {
                "Literal": {
                  "Value": "0D"
                }
              }
            },
            "labelPrecision": {
              "expr": {
                "Literal": {
                  "Value": "0L"
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
                  "Value": "false"
                }
              }
            }
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
                  "Value": "'Units Sold by Product Category (Jun-Nov 2017)'"
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
      ]
    },
    "drillFilterOtherVisuals": true
  },
  "filterConfig": {
    "filters": [
      {
        "name": "cd38dead20294e01b1c80d5a816bfed0",
        "field": {
          "Column": {
            "Expression": {
              "SourceRef": {
                "Entity": "dim_date"
              }
            },
            "Property": "date"
          }
        },
        "type": "Advanced",
        "filter": {
          "Version": 2,
          "From": [
            {
              "Name": "d",
              "Entity": "dim_date",
              "Type": 0
            }
          ],
          "Where": [
            {
              "Condition": {
                "And": {
                  "Left": {
                    "Comparison": {
                      "ComparisonKind": 2,
                      "Left": {
                        "Column": {
                          "Expression": {
                            "SourceRef": {
                              "Source": "d"
                            }
                          },
                          "Property": "date"
                        }
                      },
                      "Right": {
                        "DateSpan": {
                          "Expression": {
                            "Literal": {
                              "Value": "datetime'2017-06-01T00:00:00'"
                            }
                          },
                          "TimeUnit": 5
                        }
                      }
                    }
                  },
                  "Right": {
                    "Comparison": {
                      "ComparisonKind": 4,
                      "Left": {
                        "Column": {
                          "Expression": {
                            "SourceRef": {
                              "Source": "d"
                            }
                          },
                          "Property": "date"
                        }
                      },
                      "Right": {
                        "DateSpan": {
                          "Expression": {
                            "Literal": {
                              "Value": "datetime'2017-11-30T00:00:00'"
                            }
                          },
                          "TimeUnit": 5
                        }
                      }
                    }
                  }
                }
              }
            }
          ]
        }
      }
    ]
  }
}

```