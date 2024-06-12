#Region "Imports"
Imports System
Imports System.Data
Imports System.Math
Imports Microsoft.SqlServer.Dts.Runtime
Imports System.Collections.Generic
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
        Dim results As New List(Of String)
        Dim patientNum As String
        Dim patientNumbersString As String = ""

        ' Create a list of strings of patient numbers available in the SEH table
        sqlQuery = "SELECT * FROM SEH_REG"
        Dim sqlcmd1 As New SqlCommand(sqlQuery, destinationDatabase)
        Using reader As SqlDataReader = sqlcmd1.ExecuteReader()
            While reader.Read()
                results.Add(reader("PATIENTNR").ToString())
            End While
        End Using

        ' add patientnumbers in  string like: "'0001', '0002', '003'" So we can use it in a IN statment in SQL later
        For Each patientNum In results
            patientNumbersString += "'" & patientNum & "',"
        Next

        ' Save in a global visual studio variable
        Dts.Variables("User::patientNumbers").Value = patientNumbersString.TrimEnd(","c)

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