SELECT
    -- AANKOMST GEGEVENS
    [SEH_SEHREG].[SEHID],
    [SEH_SEHREG].[PATIENTNR],
    [AANKSDATUM],
    [AANKSTIJD],
    [GESLACHT],
    DATEDIFF(year, GEBDAT, AANKSDATUM) AS AGE,
    SUBSTRING(POSTCODE, 1, 4) AS POSTCODE,

    -- REGISTRATIE GEGEVENS
	[REGTIJD],
    [KLACHT],
    [REGSTATUS],
    [VVCODE],

    -- TRIAGE GEGEVENS
    [TRIADATUM],
    [TRIAGETIJD],
    [TRIANIVCOD],
    [SPECIALISM],

    -- EIND GEGEVENS
    [EINDTIJD],
    [BESTEMMING],

    -- Previous number of visits in the year before 
     (
        SELECT COUNT(*) 
        FROM [SEH_SEHREG] prev_visits 
        WHERE prev_visits.PATIENTNR = [SEH_SEHREG].PATIENTNR
            AND prev_visits.AANKSDATUM > DATEADD(year, -1, [SEH_SEHREG].AANKSDATUM) 
            AND prev_visits.AANKSDATUM < [SEH_SEHREG].AANKSDATUM
    ) AS PreviousVisits,

    -- Percentage of admissions for previous visits 
    (
        SELECT 
            CASE
                WHEN COUNT(*) > 0 
                THEN COUNT(CASE WHEN prev_visits.BESTEMMING IN ('OPN', 'OVER') THEN 1 END) * 100.0 / COUNT(*) 
                ELSE 0
            END
        FROM [SEH_SEHREG] prev_visits 
        WHERE prev_visits.PATIENTNR = [SEH_SEHREG].PATIENTNR
            AND prev_visits.AANKSDATUM > DATEADD(year, -1, [SEH_SEHREG].AANKSDATUM) 
            AND prev_visits.AANKSDATUM < [SEH_SEHREG].AANKSDATUM
    ) AS PrevAdmissionPercentage


FROM [SEH_SEHREG]
INNER JOIN PATIENT_PATIENT ON [SEH_SEHREG].PATIENTNR = PATIENT_PATIENT.PATIENTNR

WHERE [AANKSDATUM] > '20150101' 
    AND [VERVALL] = 0;
