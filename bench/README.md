# HRCP Benchmarks

Performance benchmarks for HRCP operations.

## Running Benchmarks

```bash
# Using uv (recommended)
uv run python bench/benchmark.py

# Using pip/venv
python bench/benchmark.py
```

## Output

The benchmark script outputs a table showing:

| Column | Description |
|--------|-------------|
| **ops/sec** | Operations per second (higher is better) |
| **μs/op** | Microseconds per operation (lower is better) |
| **std dev** | Standard deviation across runs |

## Benchmark Categories

- **creation**: Tree and resource creation
- **lookup**: Path lookups and tree walking
- **attribute**: Getting and setting attributes
- **propagation**: DOWN, UP, MERGE_DOWN, NONE modes
- **provenance**: Provenance tracking overhead
- **wildcard**: Pattern matching queries
- **serialization**: to_dict/from_dict operations

## Example Output

```
================================================================================
HRCP Performance Benchmarks
================================================================================

Benchmark                                          ops/sec      μs/op    std dev
--------------------------------------------------------------------------------
creation: single resource                        1,113,078       0.90       0.02
creation: 100 children                              13,660      73.21       0.65

lookup: get from 1000 siblings                   4,799,808       0.21       0.00
lookup: walk 1111 nodes                              5,854     170.81       0.90

attribute: set                                   8,027,615       0.12       0.01
attribute: get (exists)                         23,284,242       0.04       0.00

propagation: DOWN depth-50                         313,041       3.19       0.04
propagation: MERGE_DOWN depth-50                   131,662       7.60       0.08
propagation: UP 1000 children                        4,760     210.10       1.39

wildcard: /root/** (all 1111)                          916    1091.69       3.24

serialization: to_dict 1111 nodes                    3,352     298.32       1.24
--------------------------------------------------------------------------------
```

## Notes

- Benchmarks disable garbage collection during timing for consistency
- Each benchmark runs multiple iterations with warmup
- Results may vary based on hardware and system load
- Use for relative comparisons, not absolute guarantees
