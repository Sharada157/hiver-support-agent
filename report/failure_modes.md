# Phase 9 Failure Modes

The Phase 8-named files were not present in this checkout. This analysis
uses their completed equivalents: `outputs/runs/full_agent_predictions_with_confidence.csv`,
`outputs/runs/full_agent_full_log.json`, and `outputs/runs/judge_scores.csv`.
The judge file contains scores for all 200 examples, so no judge rows were
discarded during selection.

## The catch-all Other category is context-dependent

**Frequency:** 29/89 selected rows (33%).

**Real example:**
- ID: `golden_042`
- Customer: "I’ve got a ton of saved offline content so I’m not eager to do that unless it’s really likely to fix things..."
- Gold answer: "Thanks for the heads up! We'll take note of this. We're always testing things in order to improve. More info at /JE"
- System output: "Thanks for letting us know! In most cases a fresh reinstall clears up offline‑download glitches, and it’s the quickest way to get everything back working. If you’re comfortable giving it a try, just follow the steps here: Keep us in the loop /JM.  

If you’d rather hold off, could you share the device model and the iOS/Android + Spotify app version you’re on? That’ll help us see if there’s another fix that won’t require a reinstall."

**Mechanism hypothesis:** The message is a short conversational or underspecified fragment; gold=Other and prediction=Other, showing that the model resolves ambiguous context into a functional category or misses the catch-all.

**Fixability:** Partly fixable this week with contrastive Other examples and an explicit context-uncertainty rule; irreducible ambiguity remains when a tweet is only a fragment.

## Taxonomy boundaries collapse neighboring intents

**Frequency:** 38/89 selected rows (43%).

**Real example:**
- ID: `golden_133`
- Customer: "Meybe Problem with facebook??? Sometimes showing a Facebook Error has occiored.please try later. Ewen if Restart phone"
- Gold answer: "We understand. Is the same issue happening via WiFi, or is it only when you're on 3G/4G? Does restarting your connection help at all? /NY"
- System output: "Hey there! Sorry you’re seeing that Facebook error. Could you DM us your Spotify username or the email you use for the account? That’ll let us peek behind the scenes and see what’s up. Also, let us know if it happens on Wi‑Fi, mobile data, or both, and if a quick phone restart changes anything. Thanks! /AP"

**Mechanism hypothesis:** The response is useful, but the dominant issue was labeled Playback/Technical Bug while the classifier chose Account Access; overlapping product, content, access, and playback cues make the taxonomy boundary unstable.

**Fixability:** Fixable this week with contrastive boundary examples and a primary-issue instruction; some labels will remain inherently overlapping because the taxonomy forces one category.

## Reply drafting adds unsupported or unnecessary specifics

**Frequency:** 14/89 selected rows (16%).

**Real example:**
- ID: `golden_030`
- Customer: "Has the lyrics for completely gone now? I really rated that feature... 🤔"
- Gold answer: "Hey there! What's happening exactly? Could you let us know the device/OS you're using? We'll see what we can suggest /DF"
- System output: "Hey there! We hear you – the lyrics for that track have indeed disappeared for a lot of users. Could you let us know which device and OS you’re on? That’ll help us dig into what’s going on. In the meantime, you can keep an eye on any updates and add your vote for the lyrics feature on our community page. Thanks for the heads‑up! /DF"

**Mechanism hypothesis:** The intent was correct, but the generated reply scored 3.5/5 because it added details or assumptions beyond the short customer message and reference reply.

**Fixability:** Fixable this week with stricter source-only drafting and a post-generation fact check; residual model over-helpfulness is a limitation to monitor.

## Retrieval matches surface wording more than root cause

**Frequency:** 6/89 selected rows (7%).

**Real example:**
- ID: `golden_036`
- Customer: "Will that be soon? Also can't find Disco Santa Claus by The Rain Dolls, despite that being on UK iTunes"
- Gold answer: "We don't have any info on this yet. Same thing with Disco Santa Claus. Fingers crossed we'll be able to have it soon /GK"
- System output: "Hi there,

We don’t have any new information on that track yet. The Rain Dolls’ “Disco Santa Claus” isn’t available on Spotify right now, but we’re still working on adding it and hope to have it up soon.

Let us know if there’s anything else we can help with! /GK"

**Mechanism hypothesis:** The intent was correct, but the retrieved precedent or thread context steered the reply toward a nearby workflow rather than the exact customer state.

**Fixability:** Fixable this week by reranking retrieved examples with intent and thread context; semantic retrieval will still occasionally confuse nearby problems.

## Escalation rules miss implicit financial urgency

**Frequency:** 2/89 selected rows (2%).

**Real example:**
- ID: `golden_140`
- Customer: "Hi , you should start a family deal so my husband and I can have a spotify and not pay 10$ each. Because that's 20$ a month. From our single bank account. A little frustrating. Even if you could make it one charge that'd be great"
- Gold answer: "Hi Shyla, help's arrived! We have a Premium for Family plan that's 14.99 USD which you and your husband can join. You can find out more about Premium for Family over here: Let us know if you need anything 🙂 /JQ"
- System output: "Hey there! We’ve got a solution that should make things easier for you and your husband. Our **Premium for Family** plan lets up to six people share one subscription for just **$14.99 USD per month**, so you’ll only see a single charge on your account. 

You can learn more and switch over here: https://www.spotify.com/family  

If you need any help setting it up or have other questions, just let us know—we’re happy to assist! 🙂 /JQ"

**Mechanism hypothesis:** The gold label escalates this financially consequential message, but the keyword rules returned no escalation trigger despite the subscription or pricing concern.

**Fixability:** Fixable this week by adding financial-frustration and price-comparison signals; subtle urgency and sarcasm remain harder than explicit keywords.

## Systematic Bias Checks

The post-Phase-7 weakness is confirmed but improved from the earlier
20.7% Other accuracy: Other is now 31.0% (9/29), while Content
Availability is the lowest functional category at 43.8% (14/32).
The full agent's overall accuracy is 67.5%.

Message-length slices were short=67.3% accuracy / 4.79 judge score
(n=101), medium=68.8% / 4.87 (n=96), and long=33.3% / 5.00 (n=3).
The long slice is too small for a stable conclusion; short messages are
notably harder than medium messages for intent classification.

Emoji slices were no emoji=65.8% / 4.84 (n=184) and emoji present=87.5%
/ 4.81 (n=16). Emoji did not introduce measurable reply-quality noise
in this sample, though the emoji group is small and happened to contain
easier intent examples.

## Language, Dialect, and Sarcasm

Manual review flagged 8 selected rows with slang, non-standard grammar,
sarcasm, or ambiguous tone, including `golden_103` ("like wtf"),
`golden_121` ("What the fuck are you guys doing????"), and
`golden_200` ("fam"). These are English tweets with non-standard or
social-media usage, not non-English examples excluded by the Phase 4
English-only filter. They overlap the taxonomy-boundary and urgency
modes, especially when sarcasm or frustration obscures the literal issue.

## Relationship to Earlier Findings

Phase 9 confirms the Phase 7 Other-category concern, but the few-shot
prompt improved measured Other accuracy to 31.0%; it did not solve the
catch-all boundary. The analysis also refines the concern by identifying
Content Availability as the weakest functional category. The judge-human
correlation remains a limitation from Phase 5: judge scores are useful
for ranking reply quality, but should not be treated as a definitive
ground-truth quality metric.
