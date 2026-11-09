# C07_salary_hindi_daily_wage_draft

**What this tests:** Hindi, daily-wage worker, draft a complaint to the labour authority

## Turn 1

**User** (mode sent: draft):

> मैं एक फैक्ट्री में दिहाड़ी पर काम करता था, 600 रुपये रोज़। ठेकेदार ने पिछले 20 दिन का पैसा नहीं दिया। मैं गाज़ियाबाद में हूँ। मुझे शिकायत लिखनी है।

**Haqdaar** (topic: salary, mode: draft, language: hi, needs lawyer: False, 5877 ms):

यहाँ एक लिखित माँग‑पत्र (डिमांड लेटर) का नमूना है। 
आपको अपने ठेकेदार का पूरा नाम, पता और अपने काम की सटीक तिथियाँ भरनी होंगी। 
इसे स्पीड पोस्ट (ट्रैकिंग के साथ) या ई‑मेल से भेजें और भेजने की रसीद सुरक्षित रखें। 


(See the draft below.)
 

कृपया इस पत्र को भेजने से पहले किसी वकील से जाँच कर लें, खासकर अगर राशि बड़ी हो या दूसरी पार्टी के पास वकील हो।

**Draft:**

```
Date: [FILL: पत्र की तिथि]

From: 
Name: [FILL: आपका पूरा नाम] 
Address: [FILL: आपका पूरा पता] 
Phone: [FILL: आपका फ़ोन नंबर] 

To: 
Name: [FILL: ठेकेदार का पूरा नाम] 
Address: [FILL: ठेकेदार का पूरा पता] 

Subject: Demand for Payment of Unpaid Daily Wages 

1. I was employed as a daily‑wage worker at your factory located in Ghaziabad. 
2. My daily wage rate is Rs 600 (six hundred rupees) as agreed. 
3. For the period of the last 20 working days, i.e., from [FILL: प्रारम्भ तिथि] to [FILL: समाप्ति तिथि], you have not paid me the wages due, amounting to Rs 12,000 (twelve thousand rupees). 

Legal Basis: 
- Under the Code on Wages, 2019, Section 17, wages must be paid before the end of the 7th day of the following month. Failure to do so is a violation (Section 17, Code on Wages, 2019). 
- A claim for unpaid wages can be filed before the labour authority within three years of the cause of action, and the authority should decide within three months (Section 45, Code on Wages, 2019). 

Demand: 
Please pay the outstanding amount of Rs 12,000 within fifteen (15) days from the date of this letter, i.e., by [FILL: डेडलाइन तिथि]. 

Consequences of Non‑Payment: 
If the amount is not received within the stipulated period, I will file a wage claim before the appropriate labour authority as provided under the Code on Wages, 2019, Section 45. 

Yours sincerely, 

[Signature] 
[FILL: आपका पूरा नाम]
```

**Sources:**

- [1] Code on Wages, 2019, Section 17 - Deadline for paying wages
- [2] Code on Wages, 2019, Section 45 - Wage claim before the labour authority

**Source check:** first attempt violations = 0; attempts = 1; stripped by code after retry = 0; violations in what the user saw = 0


## Automatic checks

- topic: PASS
- reply_language: PASS
- draft_produced: PASS
- final_output_passes_source_check: PASS
