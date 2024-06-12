SELECT 

SEH_SEHREG.SEHID,
SEH_SEHREG.AANKSDATUM,
SEH_SEHREG.AANKSTIJD,

LAB_L_AANVRG.PATIENTNR,
LAB_L_AANVRG.AFDATUM,
LAB_L_AANVRG.AFTIJD,

LAB_HUIDIGE_UITSLAG.TIJD,
LAB_HUIDIGE_UITSLAG.BEPCODE,
LAB_HUIDIGE_UITSLAG.UITSLAG,
LAB_HUIDIGE_UITSLAG.AANVRAAGNR,

LAB_L_B_OMS.[DESC], 
LAB_L_B_OMS.EENHEID,
LAB_L_B_OMS.MATAARD,

SEH_SEHREG.BESTEMMING

FROM LAB_HUIDIGE_UITSLAG 

INNER JOIN  LAB_L_AANVRG ON LAB_HUIDIGE_UITSLAG.AANVRAAGNR	= LAB_L_AANVRG.AANVRAAGNR  
INNER JOIN  LAB_L_B_OMS  ON LAB_HUIDIGE_UITSLAG.BEPCODE		= LAB_L_B_OMS.BEP
INNER JOIN  SEH_SEHREG   ON SEH_SEHREG.PATIENTNR			= LAB_L_AANVRG.PATIENTNR

WHERE
    UITSLAG <> '-volgt-' 
AND UITSLAG <> '<memo>' 
AND UITSLAG <> '==='

-- Ik heb van de SEH PA dit lijstje gekregen van belangrijke labwaarden
AND ([DESC] LIKE '%ureum%' OR
[DESC] LIKE '%kreatinine%' OR
[DESC] LIKE '%natrium%' OR
[DESC] LIKE '%kalium%' OR
[DESC] LIKE '%asat%' OR
[DESC] LIKE '%alat%' OR
[DESC] LIKE '%alkalische fosfatase%' OR
[DESC] LIKE '%ggt%' OR
[DESC] LIKE 'ld' OR
[DESC] LIKE '%glucose%' OR
[DESC] LIKE '%trombocyten%' OR
[DESC] LIKE '%leucocyt%' OR
[DESC] LIKE '%leukocyt%' OR
[DESC] LIKE '%hematocriet%' OR
[DESC] LIKE '%hemoglobine%' OR
[DESC] LIKE '%cg4+%' OR
[DESC] LIKE '%crp%' OR
[DESC] LIKE '%bilirubine totaal%' OR
[DESC] LIKE '%lactaat%' OR
[DESC] LIKE '%bloedgas veneus%' OR
[DESC] LIKE '%bloedgas arterieel%' OR
[DESC] LIKE '%troponine%' OR
[DESC] LIKE '%NT-proBNP%' OR
[DESC] LIKE '%veneus%' OR 
[DESC] LIKE '%arterieel%'
OR [BEPCODE] IN ('ZGT01541', 'ZGT01530', 'ZGT0800', 'ZGT00791', 'ZGT01548', '00003132'))

 -- er zijn meerdere labresultaten dus alleen die recent bij SEH bezoek zijn afgenomen
AND AANKSDATUM > '20150101' 
AND VERVALL = 0
AND DATEDIFF(day, AANKSDATUM, AFDATUM) <= 1 AND DATEDIFF(day, AANKSDATUM, AFDATUM) >= 0 
ORDER BY SEHID, PATIENTNR, AFDATUM, AFTIJD
