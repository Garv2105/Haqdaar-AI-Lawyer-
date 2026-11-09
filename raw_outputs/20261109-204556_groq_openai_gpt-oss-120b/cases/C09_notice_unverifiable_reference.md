# C09_notice_unverifiable_reference

**What this tests:** Notice cites a section that is not in the verified sources - bot must not explain it from memory

## Turn 1

**User** (mode sent: auto):

> My landlord's lawyer sent me a notice saying under Section 106 of the Transfer of Property Act my tenancy is terminated and I must vacate in 15 days or he will file an eviction suit. I have lived here 4 years in Indore. Is this valid?

**Haqdaar** (topic: notice, mode: explain_notice, language: en, needs lawyer: True, 6602 ms):

**Who sent the notice and what it says** 
The notice came from your landlord’s lawyer, acting on the landlord’s behalf. It says that, under “[reference removed: not in verified sources] of the Transfer of Property Act,” your tenancy is terminated and you must leave the flat within **15 days** of the notice. It also warns that the landlord will file an eviction suit if you do not vacate.

**What the notice is asking for** 
- Vacate the premises. 
- Deadline: “within 15 days of this notice” (quote exactly as written).

**Legal basis mentioned** 
The notice relies on “[reference removed: not in verified sources] of the Transfer of Property Act.” I do not have that provision in my source material, so I cannot confirm whether it applies to your case. A lawyer should check the exact wording of that section and how it fits your lease.

**What can happen if you ignore it** 
A lawyer’s notice is only a demand, not a court order. Ignoring it may lead the landlord to start a civil eviction suit, which you would then have to defend in court. [1]

**What you can do now – short list** 

1. **Read the lease** – see if it is a fixed‑term or periodic tenancy and what notice period it requires. 
2. **Pay or vacate** – if you agree to leave, do so before the 15‑day deadline. 
3. **Negotiate** – contact the landlord or his lawyer to ask for more time or a settlement. 
4. **Reply in writing** – if you disagree, send a written response (email, WhatsApp, or a legal notice by Speed Post) stating your position and keep proof of sending. [1] 
5. **Get legal help** – because the notice threatens an eviction suit, speak to a lawyer right away. You can call the free legal‑aid helpline **15100** for assistance. [2]

If you are unsure about the legal reference or your rights, a lawyer can review the lease and the notice and advise the best step.

**Sources:**

- [1] Practical guidance - How to treat a legal notice you received
- [2] Legal Services Authorities Act, 1987, Section 12 - Who gets a free government lawyer

**Source check:** first attempt violations = 1; attempts = 2; stripped by code after retry = 1; violations in what the user saw = 0

- attempt 0: invalid ids [], unverified refs ['Section\u202f106'], case law []
- attempt 1: invalid ids [], unverified refs ['Section\u202f106'], case law []

## Automatic checks

- topic: PASS
- reply_language: PASS
- lawyer_flag: PASS
- final_output_passes_source_check: PASS
