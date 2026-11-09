# C15_large_amount_builder

**What this tests:** Very large consumer claim - should route to the right commission tier and flag a lawyer

## Turn 1

**User** (mode sent: auto):

> I paid a builder Rs 85 lakh for a flat in Gurugram in 2023. Possession was promised by June 2025 and still nothing. I want a full refund with interest.

**Haqdaar** (topic: consumer, mode: explain, language: en, needs lawyer: True, 3710 ms):

**Short answer** 
Yes, the law is likely on your side. The builder’s failure to give possession is a *deficiency in service* and also an *unfair trade practice* because they promised a refund and have not paid it [1][2]. 

**What you can do – from easiest to hardest**

1. **Send a written demand for refund (with interest).** 
 *What it is*: a formal letter asking the builder to return Rs 85 lakh plus interest. 
 *Cost*: free (post‑age or courier fee). 
 *What you need*: proof of payment (bank statement, receipt), copy of any agreement or promise, and the demand letter. 
 *Tip*: keep a copy and send it by registered post so you have proof of delivery.

2. **Use consumer‑helpline or grievance officer (if the builder has one).** 
 *What it is*: call the National Consumer Helpline (1915 or 1800‑11‑4000) or ask the builder’s grievance officer to acknowledge your complaint within 48 hours and try to settle within a month [3]. 
 *Cost*: free. 
 *What you need*: same documents as above plus the complaint reference you receive.

3. **File a complaint with the State Consumer Commission.** 
 *What it is*: a quasi‑judicial body that can order the builder to refund the money and pay compensation. 
 *Jurisdiction*: because the claim is above Rs 50 lakh, it goes to the State Commission, not the District one [4]. 
 *Filing fee*: there is a fee for claims above Rs 5 lakh; the exact amount is set in the fee schedule [5]. 
 *How to file*: you can file online on the e‑Jagriti portal (e‑jagriti.gov.in) without a lawyer [6]. 
 *Time limit*: you must file within 2 years from when the problem arose (the missed possession date, June 2025) – so before June 2027 [7]. 

**What you still need to gather** 
- Builder’s full name and registration details. 
- Exact date(s) of payment and the amount paid. 
- Any written agreement or contract, or at least a copy of the payment receipt. 

**When to see a lawyer** 
Because the amount is large (Rs 85 lakh) and the process can be complex, a lawyer can help draft the demand letter, prepare the complaint, and represent you at the Commission. You can get free legal aid through NALSA’s helpline 15100 if you cannot afford a lawyer. 

**What I’m not sure about** 
I don’t have the builder’s name, the exact payment date, or a copy of any written agreement. Those details are crucial for the complaint. 

Good luck, and keep all your documents safe.

**Sources:**

- [1] Consumer Protection Act, 2019, Section 2(11) - Deficiency in service
- [2] Consumer Protection Act, 2019, Section 2(47) - Unfair trade practice, including not refunding
- [3] Consumer Protection (E-Commerce) Rules, 2020, Rule 4(5) - E-commerce grievance officer deadlines
- [4] Consumer Protection Act, 2019, with the Jurisdiction Rules, 2021, Section 34 - District Consumer Commission and where to file
- [5] Consumer Protection (Consumer Disputes Redressal Commissions) Rules, 2020, Rule 7 (fee schedule) - No fee for small consumer claims
- [6] Consumer Protection Act, 2019, Section 35 - Filing a consumer complaint, including online
- [7] Consumer Protection Act, 2019, Section 69 - Two-year time limit for consumer complaints

**Source check:** first attempt violations = 0; attempts = 1; stripped by code after retry = 0; violations in what the user saw = 0


## Automatic checks

- topic: PASS
- reply_language: PASS
- lawyer_flag: PASS
- final_output_passes_source_check: PASS
