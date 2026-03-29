# LLM Monitoring Report

- Generated at: 2026-03-28T17:57:04.948046 UTC
- Collection run id: 2
- Total models in latest run: 50
- Newly detected models: 0

## Sources Used

- huggingface_open_llm_leaderboard
- vellum_llm_leaderboard

## Newly Detected Models

- No new models detected in the latest run.

## Metric Coverage

- intelligence_score: 25/50 models (50.0%)
- input_price_per_1m_tokens: 22/50 models (44.0%)
- output_price_per_1m_tokens: 22/50 models (44.0%)
- tokens_per_second: 16/50 models (32.0%)
- ttft_seconds: 18/50 models (36.0%)
- context_window: 23/50 models (46.0%)
- license_type: 24/50 models (48.0%)

## Top Models By Profile

### coding_dev

Best for software engineering, code generation, and coding workflows.

- No recommendations available.

### reasoning_analysis

Best for reasoning-heavy tasks, analysis, and difficult problem solving.

- No recommendations available.

### enterprise_agents

Balanced profile for agent workflows with cost, speed, and reasoning tradeoffs.

- No recommendations available.

### long_context_rag

Best for retrieval and long documents where context window matters most.

- No recommendations available.

### minimum_cost

Best for keeping inference cost low.

- No recommendations available.

## Major Observations

- The latest run contains 50 model rows across the configured public sources.
- 25 models include benchmark intelligence data, while 22 models include cost-related data.
- 24 models include license metadata that can be used by the commercial-use filter.
- 0 models are flagged as new in the latest run.

## Recommendation Summary

- No enterprise summary recommendations are available.

## Limitations

- Some models do not expose all metrics across all public sources.
- Cross-source model matching uses a simple normalized-name rule.
- Missing metrics are stored as null and skipped during scoring.
- The first run marks all models as new because there is no earlier baseline.
