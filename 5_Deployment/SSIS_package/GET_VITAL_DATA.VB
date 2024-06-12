#Region "Help:  Introduction to the script task"
'The Script Task allows you to perform virtually any operation that can be accomplished in
'a .Net application within the context of an Integration Services control flow. 

'Expand the other regions which have "Help" prefixes for examples of specific ways to use
'Integration Services features within this script task.
#End Region

#Region "Imports"
Imports System
Imports System.Data
Imports System.Math
Imports Microsoft.SqlServer.Dts.Runtime
Imports System.Data.SqlClient
#End Region

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

             PatientId AS PATIENTNR
            ,[DateTime]
            ,[LABEL]
            ,[Value1]
            ,[Value2]

            FROM METINGEN_PPDVALUE M

            INNER JOIN METINGEN_PPDVC P   ON M.[PatientParameterDataValueContextId] = P.[AutoID]
            INNER JOIN METINGEN_PARAMS PA ON PA.[PARAMID]                           = P.[ParameterCode]

            WHERE 
	             DATEDIFF(DAY, GETDATE() ,[DateTime]) >= -1
            AND [ParameterCode] IN ('CS00000001', 'CS00000286', 'CS00000005', 'CS00000002', 'CS00000003', 'CS00000857')
            AND PatientId IN (" & patientNumbers & ")
            "

            'Execute SQL query and write to LAB table
            Using cmd As New SqlCommand(sqlQuery, sourceDatabase)
                Using reader As SqlDataReader = cmd.ExecuteReader()
                    Using bulkCopy As New SqlBulkCopy(destinationDatabase)

                        bulkCopy.DestinationTableName = "SEH_VITALS"
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