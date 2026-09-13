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

## Intent Taxonomy Design
Drafted 7 categories (6 real + Other) based on prior knowledge of SpotifyCares support patterns, then validated against 80 randomly sampled real customer tweets.

- "Other" accounted for 21.2% of the sample (17 out of 80 tweets). This sits comfortably within the acceptable range (<25%), proving the 6 core functional categories successfully covered nearly 80% of real-world user situations without massive data leakage.
- Found ambiguity between Playback/Technical Bug and Service Outage on tweets like *"It seems that i can't play any song from some artists. Lot's of people are talking about this bug."* (Tweet 5) — resolved by adding a specific social-proof rule: if a playback error is explicitly noted by the user as widespread or affecting multiple peers simultaneously, it scales into a Service Outage (Category 6); otherwise, isolated errors default to a Playback Bug (Category 1).
- Deliberately did NOT create separate categories for third-party platform integrations (like Hulu bundles, Facebook authentication links, or SheerID configurations) because they easily mapped to Account Access or Billing/Subscription depending on the roadblock symptom. Creating individual categories for them would over-fragment the taxonomy without adding value to the core "good agent" troubleshooting framework.
- Final taxonomy: 
  1. Playback/Technical Bug
  2. Account Access
  3. Billing/Subscription
  4. Content Availability
  5. Feature Request/Complaint
  6. Service Outage
  7. Other



# Draft Escalation Rules

Escalate to human if ANY of the following:
1. Intent = Billing/Subscription AND message mentions a specific dollar amount 
   or the word "refund"
2. Intent = Account Access AND message implies compromise ("hacked", "someone 
   else logged in")
3. Message contains anger/threat markers (profanity, "cancelling", "lawyer")
4. Classifier confidence below [threshold — TBD once classifier is built]
5. This is a repeat contact on the same thread (customer replied again after 
   an earlier auto-reply)

Otherwise, auto-handle.

## Phase 4 — Data Preparation Results

**Language filtering:**
Language distribution across cleaned customer tweets:
- English (en): 15,983
- Unknown: 239
- Polish: 136
- Tagalog: 97
- French: 90
- Somali: 84
- Indonesian: 67
- Norwegian: 57
- Afrikaans: 53
- Dutch: 50
(plus a long tail of other languages)

Filtered to English-only, retaining 15,983 rows. Non-English tweets (~a few 
hundred across many languages) excluded since taxonomy, prompts, and evaluation 
are all designed for English; multilingual support explicitly out of scope for 
this project.

**Deduplication:**
- Removed 6,468 exact duplicate rows
- Removed 7 additional near-duplicate rows (normalized-template matching)

**Triple construction (customer_message, brand_reply pairs):**
- Total customer messages seen: 4,947
- Kept (had a matching brand reply): 4,081
- Dropped (no brand reply found): 866 (17.5%)

This 17.5% drop rate is a meaningful limitation: our knowledge base and later 
golden set only reflect issues SpotifyCares actually responded to in-thread. 
Issues that went unanswered publicly, or were resolved entirely via DM with no 
visible public reply, are systematically excluded from what the system can learn 
from. This is a real source of bias worth flagging in the report's "what's 
misleading about my headline number" section.

**Knowledge base for grounding:**
- Final knowledge base size: 4,081 (customer_message, brand_reply) pairs
- Embedding model: sentence-transformers `all-MiniLM-L6-v2`
- Embedding dimensionality: 384 (confirmed via output shape: 4081 x 384)
- Chose local embeddings over TF-IDF for semantic (not just keyword) similarity 
  matching, and over hosted embedding APIs to keep this step free, fast (local 
  GPU), and fully reproducible offline for reviewers without requiring an 
  additional API key

**Note on Hugging Face rate limits:**
Ran without an HF_TOKEN set, triggering a warning about unauthenticated request 
limits. Did not block the run, but worth setting an HF_TOKEN env variable if 
this step needs to be re-run frequently to avoid potential rate limiting.