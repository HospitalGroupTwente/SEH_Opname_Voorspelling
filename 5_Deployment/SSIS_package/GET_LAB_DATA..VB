#Region "Imports"
Imports System
Imports System.Data
Imports System.Math
Imports Microsoft.SqlServer.Dts.Runtime
Imports System.Data.SqlClient
#End Region

<Microsoft.SqlServer.Dts.Tasks.ScriptTask.SSISScriptTaskEntryPointAttribute()>
<System.CLSCompliantAttribute(False)>
Partial Public Class ScriptMain
    Inherits Microsoft.SqlServer.Dts.Tasks.ScriptTask.VSTARTScriptObjectModelBase

    Public Sub Main()
        ' Make database connections
        Dim rawConDest As Object = Dts.Connections("researchdb-t01.SEHREP").AcquireConnection(Dts.Transaction)
        Dim rawConSource As Object = Dts.Connections("sql2019hix-h02.HiX_OVZ").AcquireConnection(Dts.Transaction)
        Dim destinationDatabase As SqlConnection = CType(rawConDest, SqlConnection)
        Dim sourceDatabase As SqlConnection = CType(rawConSource, SqlConnection)

        Dim patientNumbers As String = Dts.Variables("User::patientNumbers").Value.ToString()

        If Not patientNumbers = "" Then

            Dim sqlQuery As String

            sqlQuery = "
            SELECT 

            LAB_L_AANVRG.PATIENTNR,
            LAB_L_AANVRG.AFDATUM,
            LAB_L_AANVRG.AFTIJD,
        
            LAB_HUIDIGE_UITSLAG.TIJD AS UITTIJD,
            LAB_HUIDIGE_UITSLAG.BEPCODE,
            LAB_HUIDIGE_UITSLAG.UITSLAG,
            LAB_HUIDIGE_UITSLAG.AANVRAAGNR,

            LAB_L_B_OMS.[DESC], 
            LAB_L_B_OMS.EENHEID,
            LAB_HUIDIGE_UITSLAG.DATUM AS UITDATUM  -- this as last as I cannot change the order of the column no more

            FROM LAB_HUIDIGE_UITSLAG 

            INNER JOIN  LAB_L_AANVRG ON LAB_HUIDIGE_UITSLAG.AANVRAAGNR	= LAB_L_AANVRG.AANVRAAGNR  
            INNER JOIN  LAB_L_B_OMS  ON LAB_HUIDIGE_UITSLAG.BEPCODE		= LAB_L_B_OMS.BEP

            WHERE
                DATEDIFF(DAY, GETDATE(), AFDATUM) >= -1  -- Alles van een dag geleden tot nu
            AND UITSLAG <> '<memo>' 
            AND UITSLAG <> '==='

            -- Ik heb van de SEH PA dit lijstje gekregen van belangrijke labwaarden
            AND PATIENTNR IN (" & patientNumbers & " )
            AND [BEPCODE] IN ('CS000184', 'ZGT01761', 'ZGT01766', 'CS000187', 'ZGT01318', 'ZGT01321', 'CS000165', 'ZGT01448', 'ZGT01452', 'CS000168', 'ZGT01265', 'ZGT01264', 'CS000208', 'CS000211',
				              'CS000211', 'CS000203', 'CS000205', 'CS000214', '@0002464', 'CS000251', 'CS000267', 'CS002485', 'CS003765', 'CS000009', 'CS000013', 'CS003762', 'CS000002', 'CS000001',
				              'CS000277', 'CS000197', 'CS001401', '@0002710', 'ZGT01324', 'ZGT00324', 'ZGT00473') 

            "

            'Execute SQL query and write to LAB table
            Using cmd As New SqlCommand(sqlQuery, sourceDatabase)
                Using reader As SqlDataReader = cmd.ExecuteReader()
                    Using bulkCopy As New SqlBulkCopy(destinationDatabase)

                        bulkCopy.DestinationTableName = "SEH_LAB"
                        bulkCopy.WriteToServer(reader)

                    End Using
                End Using
            End Using

        End If

        'Release database connections
        Dts.Connections("researchdb-t01.SEHREP").ReleaseConnection(rawConDest)
        Dts.Connections("sql2019hix-h02.HiX_OVZ").ReleaseConnection(rawConSource)

        Dts.TaskResult = ScriptResults.Success
    End Sub

#Region "ScriptResults declaration"
    'This enum provides a convenient shorthand within the scope of this class for setting the
    'result of the script.

    'This code was generated automatically.
    Enum ScriptResults
        Success = Microsoft.SqlServer.Dts.Runtime.DTSExecResult.Success
        Failure = Microsoft.SqlServer.Dts.Runtime.DTSExecResult.Failure
    End Enum

#End Region

End Class