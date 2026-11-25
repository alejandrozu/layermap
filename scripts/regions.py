# Regional unions (level 1) and country-level unit merges (level 2)

REGIONS = [
    ("LAM", "Latin America"),
    ("NAM", "Northern America"),
    ("EUR", "Europe (European Political Community)"),
    ("CEA", "Central Eurasia"),
    ("EAS", "East Asia"),
    ("SEA", "Southeast Asia"),
    ("OCE", "Oceania"),
    ("SAS", "South Asia"),
    ("MNA", "Middle East & North Africa"),
    ("ESA", "East & Southern Africa"),
    ("WAF", "West Africa"),
    ("ATA", "Antarctica"),
]

# Country level = 193 UN members + 2 observers (Palestine, Vatican); every dependency or
# disputed/indeterminate unit is folded into the UN member it belongs to.
MERGE = {
    "TWN": "CHN", "HKG": "CHN", "MAC": "CHN",
    "GRL": "DNK", "FRO": "DNK",
    "AIA": "GBR", "BMU": "GBR", "VGB": "GBR", "CYM": "GBR", "FLK": "GBR", "GIB": "GBR", "GGY": "GBR", "JEY": "GBR",
    "IMN": "GBR", "MSR": "GBR", "PCN": "GBR", "SHN": "GBR", "SGS": "GBR", "TCA": "GBR", "IOT": "GBR", "ESB": "GBR", "WSB": "GBR",
    "NCL": "FRA", "PYF": "FRA", "WLF": "FRA", "SPM": "FRA", "BLM": "FRA", "MAF": "FRA", "ATF": "FRA", "CLP": "FRA",
    "ABW": "NLD", "CUW": "NLD", "SXM": "NLD",
    "PRI": "USA", "GUM": "USA", "VIR": "USA", "ASM": "USA", "MNP": "USA", "UMI": "USA",
    "NFK": "AUS", "IOA": "AUS", "HMD": "AUS", "ATC": "AUS", "CSI": "AUS",
    "COK": "NZL", "NIU": "NZL",
    "ALD": "FIN", "CNM": "CYP", "CYN": "CYP", "USG": "CUB",
    "SOL": "SOM", "KAB": "KAZ", "KAS": "IND",
    "KOS": "SRB", "SAH": "MAR", "BRT": "SDN", "BRI": "BRA",
}
DROP = {"PGA", "SCR"}   # tiny disputed reefs (Spratlys, Scarborough): not assigned to anyone
SPLIT = {"SPI": ("ARG", "CHL")}  # undemarcated ice field: split by nearest country

R = {
    "LAM": "MEX GTM BLZ SLV HND NIC CRI PAN CUB JAM HTI DOM PRI BHS TCA CYM VGB VIR AIA MSR KNA ATG DMA LCA VCT BRB GRD TTO ABW CUW SXM MAF BLM COL VEN GUY SUR ECU PER BOL BRA PRY URY ARG CHL FLK BJN SER BRI SPI CLP",
    "NAM": "USA CAN",
    "EUR": "ALB AND ARM AUT AZE BEL BIH BGR HRV CYP CZE DNK EST FIN FRA GEO DEU GRC HUN ISL IRL ITA KOS LVA LIE LTU LUX MLT MDA MCO MNE NLD MKD NOR POL PRT ROU SMR SRB SVK SVN ESP SWE CHE TUR UKR GBR VAT FRO GRL GGY JEY IMN GIB BMU SPM",
    "CEA": "RUS BLR KAZ KGZ TJK TKM UZB",
    "EAS": "CHN JPN KOR PRK MNG",
    "SEA": "BRN KHM IDN LAO MYS MMR PHL SGP THA TLS VNM PGA SCR",
    "OCE": "AUS NZL PNG FJI SLB VUT NCL PYF WSM TON KIR TUV NRU MHL FSM PLW GUM MNP ASM COK NIU PCN NFK WLF UMI IOA ATC CSI TKL",
    "SAS": "IND PAK BGD NPL BTN LKA MDV AFG IOT",
    "MNA": "DZA BHR COM EGY IRQ JOR KWT LBN LBY MRT MAR OMN PSX QAT SAU SDN SYR TUN ARE YEM ISR IRN SAH BRT",
    "ESA": "KEN TZA UGA RWA BDI SDS ETH SOM DJI ERI COD ZAF NAM BWA ZWE ZMB MOZ MWI MDG LSO SWZ MUS SYC SHN AGO",
    "WAF": "BEN CPV CIV GMB GHA GIN GNB LBR NGA SEN SLE TGO MLI BFA NER CMR CAF TCD COG GNQ GAB STP",
    "ATA": "ATA ATF HMD SGS BVT",
}
REGION_OF = {c: r for r, s in R.items() for c in s.split()}

NAMES = {
    "USA": "United States", "SRB": "Serbia", "SWZ": "Eswatini", "TLS": "Timor-Leste",
    "BHS": "Bahamas", "TZA": "Tanzania", "CIV": "Côte d'Ivoire", "COD": "DR Congo",
    "COG": "Congo", "PSX": "Palestine", "SAH": "Western Sahara", "CZE": "Czechia",
    "MKD": "North Macedonia", "BIH": "Bosnia and Herzegovina", "CAF": "Central African Republic",
    "SDS": "South Sudan", "PRK": "North Korea", "KOR": "South Korea", "LAO": "Laos",
    "FSM": "Micronesia", "ATF": "French Southern Lands", "SGS": "South Georgia & S. Sandwich Is.",
    "HMD": "Heard & McDonald Is.", "IOA": "Christmas & Cocos Is.", "IOT": "British Indian Ocean Terr.",
    "UMI": "US Minor Outlying Is.", "VIR": "US Virgin Islands", "VGB": "British Virgin Islands",
    "SPI": "Southern Patagonian Ice Field", "BRI": "Brazilian Island", "BRT": "Bir Tawil",
    "PGA": "Spratly Islands", "SCR": "Scarborough Reef", "CHN": "China",
}
