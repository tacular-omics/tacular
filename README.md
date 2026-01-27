# tacular

A helper package for peptacular and paftacular. Includes lookups for modifications, amino acids, and other data types.

## Generate Data

See data_gen/README.md

## Generating JSONs

It's possible to generate JSON objects for all parsed data used within tacular. This isn't used within tacular or its downstream packages, but may be useful in other projects, especially those not Python-based.

```
just gen-jsons
```