ureum           = 'CS000184'
ureum_poc       = ['ZGT01761', 'ZGT01766']
kreat           = 'CS000187'
kreat_poc       = ['ZGT01318', 'ZGT01321']
natrium         = 'CS000165'
natrium_poc     = ['ZGT01448', 'ZGT01452']
kalium          = 'CS000168'
kalium_poc      = ['ZGT01265', 'ZGT01264']
asat            = 'CS000208'
alat            = 'CS000211'
af              = 'CS000203'
ggt             = 'CS000205'
ldh             = 'CS000214'
glucose         = ['@0002464', 'CS000251']
glucose_poc     = ['CS000267', 'CS002485']
glucose_urine   = 'CS003765'
trombocyt       = 'CS000009'
leukocyt_bloed  = 'CS000013'
leukocyt_urine  = 'CS003762'
hematocriet     = 'CS000002'
hemoglobine     = 'CS000001'
crp             = 'CS000277'
bilirubine      = 'CS000197'
lactaat         = 'CS001401'
lactaat_poc     = ['@0002710', 'ZGT01324']
troponine       = 'ZGT00324'
pro_bnp         = 'ZGT00473'

all_bepcodes = [ureum, *ureum_poc, kreat, *kreat_poc, natrium, *natrium_poc, kalium, *kalium_poc, \
                asat, alat, af, ggt, ldh, *glucose, *glucose_poc, glucose_urine, trombocyt, leukocyt_bloed, 
                leukocyt_urine, hematocriet, hemoglobine, crp, bilirubine, lactaat, *lactaat_poc, troponine, pro_bnp]