## User Question
```text
What are the top 10 product categories by sales volume (units sold)?
```

## Genie Query
```sql
WITH ranked_categories AS (
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
  `Product Category`,
  `Units Sold`
FROM
  ranked_categories
WHERE
  `volume_rank` <= 10
ORDER BY
  `volume_rank`
```

## Resulting `visual.json` (or key configuration elements)
```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.5.0/schema.json",
  "name": "ab1c2d3e4f5a6b7c",
  "position": {
    "x": 20.425531914893618,
    "y": 20.425531914893618,
    "z": 0,
    "height": 679.87841945288756,
    "width": 966.80851063829789,
    "tabOrder": 0
  },
  "visual": {
    "visualType": "pieChart",
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
              "active": true,
              "format": "G"
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
                  "Value": "1D"
                }
              }
            },
            "labelPrecision": {
              "expr": {
                "Literal": {
                  "Value": "0L"
                }
              }
            },
            "position": {
              "expr": {
                "Literal": {
                  "Value": "'outside'"
                }
              }
            },
            "labelStyle": {
              "expr": {
                "Literal": {
                  "Value": "'Data value, percent of total'"
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
                  "Value": "'Left'"
                }
              }
            }
          }
        }
      ],
      "dataPoint": [
        {
          "properties": {
            "fill": {
              "solid": {
                "color": {
                  "expr": {
                    "Literal": {
                      "Value": "'#0078D4'"
                    }
                  }
                }
              }
            }
          },
          "selector": {
            "metadata": "fact_sales.Units Sold"
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
                  "Value": "'Top Product Categories by Units Sold'"
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
      ],
      "general": [
        {
          "properties": {
            "keepLayerOrder": {
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
        "name": "cf5b6455cd17b3cc1fad",
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
                        "Name": "d",
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
                              "Source": "d"
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
                    "Top": 10
                  }
                }
              },
              "Type": 2
            },
            {
              "Name": "d",
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
                            "Source": "d"
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
        "name": "c45bd0f1edf6efd7da63",
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
      }
    ]
  }
}
```