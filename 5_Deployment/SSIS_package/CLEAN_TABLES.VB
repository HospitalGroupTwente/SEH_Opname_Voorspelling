
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
        ' Make database connection
        Dim rawCon As Object = Dts.Connections("researchdb-t01.SEHREP").AcquireConnection(Dts.Transaction)
        Dim destinationDatabase As SqlConnection = CType(rawCon, SqlConnection)

        Dim sqlQuery As String

        sqlQuery = "DELETE FROM SEH_REG"
        Dim sqlcmd1 As New SqlCommand(sqlQuery, destinationDatabase)
        sqlcmd1.ExecuteNonQuery()

        sqlQuery = "DELETE FROM SEH_LAB"
        Dim sqlcmd3 As New SqlCommand(sqlQuery, destinationDatabase)
        sqlcmd3.ExecuteNonQuery()

        sqlQuery = "DELETE FROM SEH_VITALS"
        Dim sqlcmd4 As New SqlCommand(sqlQuery, destinationDatabase)
        sqlcmd4.ExecuteNonQuery()


        'Release database connection
        Dts.Connections("researchdb-t01.SEHREP").ReleaseConnection(rawCon)

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