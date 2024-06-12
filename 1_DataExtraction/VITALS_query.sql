SELECT 

 [SEHID]
,[PATIENTNR]
,[AANKSDATUM]
,[DateTime]
,[LABEL]
,[Value1]
,[Value2]
,[Value3]
,[EENHEID]

FROM METINGEN_PPDVALUE M

INNER JOIN METINGEN_PPDVC P   ON M.[PatientParameterDataValueContextId] = P.[AutoID]
INNER JOIN SEH_SEHREG         ON SEH_SEHREG.[PATIENTNR]                 = P.[PatientId]
INNER JOIN METINGEN_PARAMS PA ON PA.[PARAMID]                           = P.[ParameterCode]

WHERE 
    [AANKSDATUM] > '20150101'
AND [VERVALL] = 0
AND [ParameterCode] IN (
						'CS00000001', -- HR
						'CS00000286', -- POLS
						'CS00000005', -- TEMP
						'CS00000002', -- NIBP
						'CS00000003', -- RESP
						'CS00000857'  -- MEWS
									)

AND DATEDIFF(day, AANKSDATUM, [DateTime]) >= 0 
AND DATEDIFF(day, AANKSDATUM, [DateTime]) <= 1

