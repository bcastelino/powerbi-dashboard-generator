## User Question
```text
What is the trend of sales volume for the top 5 product categories over time?
```

## Genie Query
```sql
WITH top_categories AS (
  SELECT
    COALESCE(`Product Category`, 'Other') AS `Product Category`,
    MEASURE(`Units Sold`) AS `Units Sold`,
    ROW_NUMBER() OVER (ORDER BY MEASURE(`Units Sold`) DESC) AS `volume_rank`
  FROM
    `wl_internal`.`olist_ecommerce`.`fact_sales_metric_view`
  WHERE
    `Product Category` IS NOT NULL
  GROUP BY
    ALL
)
SELECT
  DATE_TRUNC('MONTH', f.`order_date`) AS `month`,
  COALESCE(f.`Product Category`, 'Other') AS `Product Category`,
  MEASURE(f.`Units Sold`) AS `Units Sold`
FROM
  `wl_internal`.`olist_ecommerce`.`fact_sales_metric_view` f
WHERE
  f.`Product Category` IN (
    SELECT
      `Product Category`
    FROM
      top_categories
    WHERE
      `volume_rank` <= 5
  )
  AND f.`order_date` IS NOT NULL
  AND f.`Product Category` IS NOT NULL
GROUP BY
  ALL
ORDER BY
  `month`,
  `Product Category`
```

## Resulting `visual.json` (or key configuration elements)
```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.5.0/schema.json",
  "name": "affa4fa17dbd4428a1be",
  "position": {
    "x": 20.58325935107791,
    "y": 0,
    "z": 0,
    "height": 699.83081793664894,
    "width": 1239.11221293489,
    "tabOrder": 0
  },
  "visual": {
    "visualType": "lineChart",
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
                  "Property": "month_pad"
                }
              },
              "queryRef": "dim_date.month_pad",
              "nativeQueryRef": "month_pad",
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
                "Property": "month_pad"
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
                  "Value": "'Time (Year-Month)'"
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
                  "Value": "2D"
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
                  "Value": "'Top Categories Trends - Units Sold Over Time'"
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
        "name": "81d1be20f7bdb89c5935",
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
        "name": "08d4296fc315b4c1e745",
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
        "name": "3a18af9cf002f2dffb9f",
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
                    "Top": 5
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
        }
      },
      {
        "name": "3fb4e3ed16833e034c0c",
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
        "type": "Categorical"
      }
    ]
  }
}
```