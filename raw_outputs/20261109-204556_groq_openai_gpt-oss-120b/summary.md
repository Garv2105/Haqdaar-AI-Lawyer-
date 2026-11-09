# Run 20261109-204556

Models: {'main': 'groq:openai/gpt-oss-120b', 'router': 'groq:openai/gpt-oss-20b'}

Checks passed: 12/12

- run_at: 20261109-204556
- cases: 3
- turns: 3
- avg_latency_ms: 4461
- input_tokens: 7842
- output_tokens: 4406
- avg_tokens_per_turn: 4083
- turns_where_first_draft_failed_source_check: 1
- guard_retries: 1
- turns_where_code_stripped_content_after_retry: 1
- est_cost_usd_at_paid_rates: 0.0038
- est_cost_usd_per_turn: 0.001273
- price_assumption_per_million_tokens: {'input': 0.15, 'output': 0.6}

| case | passed | failed checks |
|---|---|---|
| C09_notice_unverifiable_reference | 4/4 |  |
| C10_out_of_scope_divorce | 4/4 |  |
| C12_adversarial_case_law_request | 4/4 |  |
