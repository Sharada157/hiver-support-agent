## Decision: Brand Selection — SpotifyCares

**Method:** Sampled 40 replies per candidate brand (SpotifyCares, AppleSupport, 
AmazonHelp), applied a keyword heuristic (flags reply as "generic redirect" if it 
mentions DM/direct message AND is under 25 words), then manually verified results 
by reading the flagged samples. Later re-ran a refined 3-way classification 
(Substantive Help / Generic DM Redirect / Conversational Closing) on a 60-tweet 
sample per brand for a clearer breakdown.

**Round 1 — keyword heuristic (n=40 per brand):**
| Brand | Substantive | Generic Redirect |
|---|---|---|
| SpotifyCares | 28 | 12 |
| AppleSupport | 27 | 13 |
| AmazonHelp | 40 | 0 |

AmazonHelp's 40/0 split was immediately suspicious — it implied zero DM redirects, 
which contradicted the general pattern of order-specific brands pushing account 
details to private messages. This prompted a deeper manual check rather than 
accepting the number at face value.

**Round 2 — refined 3-category classification (n=60 per brand):**
| Brand | Substantive Help | Generic DM Redirect | Conversational Closing |
|---|---|---|---|
| SpotifyCares | 41 | 18 | 1 |
| AppleSupport | 37 | 23 | 0 |
| AmazonHelp | 58 | 1 | 1 |

**Why AmazonHelp's high "substantive" count was rejected as misleading:**
Manual inspection of Amazon's flagged "substantive" replies showed most were 
mid-thread clarifying questions (e.g., "What was advised when you contacted them?", 
"What was the delivery estimate given at Checkout?") — not resolutions. The 
heuristic miscounted these as substantive simply because they didn't mention "DM" 
and weren't short. Amazon's sample also contained non-English replies (French 
observed), adding a language-consistency risk not present in the other two brands.

**Final decision: SpotifyCares**
- Highest *genuinely* substantive, resolution-specific content on manual review 
  (e.g., explicit reasons for content removal, specific troubleshooting steps), 
  not just questions or reassurance
- Recurring resolution patterns clearly visible across different customers 
  (e.g., restart/update advice for playback bugs, licensing explanations for 
  missing content) — directly supports the grounded-reply requirement
- Generic-DM-redirect rate (18/60) is real and honestly counted, not an artifact 
  of heuristic blind spots like AmazonHelp's
- Data consistently in English, unlike AmazonHelp's mixed-language replies
- [Fill in: total SpotifyCares message volume from your Phase 1 output — 
  `brand_replies` and `customer_tweets` counts]
- [Fill in: intent tally from your Step 4 manual tagging — confirm ≥6 intents 
  had reasonable representation in your sample]
