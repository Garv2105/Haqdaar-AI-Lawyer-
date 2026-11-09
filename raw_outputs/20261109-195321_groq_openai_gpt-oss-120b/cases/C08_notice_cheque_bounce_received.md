# C08_notice_cheque_bounce_received

**What this tests:** User pastes a cheque bounce notice they received - must explain deadline and flag lawyer

## Turn 1

**User** (mode sent: auto):

> I got this notice by post yesterday, what does it mean?
> 
> LEGAL NOTICE UNDER SECTION 138 OF THE NEGOTIABLE INSTRUMENTS ACT, 1881
> To, Mr. Arjun Mehta
> Under instructions from my client Shri Vikas Traders, I hereby serve you notice that your cheque no. 004512 dated 02.10.2026 for Rs 75,000 drawn on State Bank of India was returned unpaid with the remark 'Funds Insufficient' on 10.10.2026. You are hereby called upon to pay the said amount within 15 days of receipt of this notice, failing which my client shall initiate criminal proceedings against you, in which case you shall be liable for costs.
> Advocate S. K. Jain

**Haqdaar** (topic: notice, mode: explain_notice, language: en, needs lawyer: True, 4181 ms):

I’m not a lawyer, but I can help you understand what the notice says.

**Who sent it and why** 
The notice comes from Advocate S. K. Jain, who says he is acting for his client — Shri Vikas Traders. 
They claim that the cheque you gave them (no. 004512 dated 02‑10‑2026 for Rs 75,000) was bounced by the bank on 10‑10‑2026 because there were not enough funds.

**What they are asking for** 
You are asked to pay the full Rs 75,000 **within 15 days of receiving this notice**. The notice says the deadline is “within 15 days of receipt of this notice.” 

**Law they rely on** 
They are invoking **Section 138 of the Negotiable Instruments Act, 1881** – the law that makes a bounced cheque a criminal offence if the drawer does not pay after a demand notice. [1]

**What can happen if you ignore it** 
If you do not pay within the 15‑day window, the creditor can start a criminal case. Under Section 138, the offence can lead to up to **2 years’ imprisonment**, a fine of up to **twice the cheque amount**, or both. [1]

**What you can do now – short list** 

1. **Pay the amount** within the 15‑day period to avoid criminal proceedings. 
2. **Negotiate** with Shri Vikas Traders (or their lawyer) for a settlement or a payment plan. 
3. **Send a written reply** (by registered post, email, or WhatsApp) if you dispute the claim, keeping a copy as proof. Practical tip: treat the notice as a demand, not a court order, and do not ignore it. [2] 
4. **Get a lawyer quickly** – because the notice threatens criminal action, a lawyer can advise you on the best steps and represent you if needed. 

**If you need free help** call the NALSA legal‑aid helpline at **15100**. 

Make sure you keep all documents (the notice, the cheque copy, bank statements, any prior communication) organized; they will be useful later.

**Sources:**

- [1] Negotiable Instruments Act, 1881, Section 138 - Cheque bounce notice and the 15-day window
- [2] Practical guidance - How to treat a legal notice you received

**Source check:** first attempt violations = 0; attempts = 1; stripped by code after retry = 0; violations in what the user saw = 0


## Automatic checks

- topic: PASS
- reply_language: PASS
- lawyer_flag: PASS
- cites_expected_source: PASS
- final_output_passes_source_check: PASS
