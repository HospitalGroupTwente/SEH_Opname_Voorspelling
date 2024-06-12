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
        System.Diagnostics.Debug.WriteLine("test SEH")
        Dim rawConDest As Object = Dts.Connections("researchdb-t01.SEHREP").AcquireConnection(Dts.Transaction)
        Dim rawConSource As Object = Dts.Connections("sql2019hix-h02.HiX_OVZ").AcquireConnection(Dts.Transaction)
        Dim destinationDatabase As SqlConnection = CType(rawConDest, SqlConnection)
        Dim sourceDatabase As SqlConnection = CType(rawConSource, SqlConnection)

        Dim sqlQuery As String

        sqlQuery = "
        WITH MED_VER_ALL AS (
        SELECT
            PATCODE,
            MUTDAT,
            MUTTIJD,
		    VERIFIED,
            ROW_NUMBER() OVER (PARTITION BY PATCODE ORDER BY MUTDAT DESC, MUTTIJD DESC, DATUM DESC) AS RowRank
        FROM
            MEDICAT_RECEPT
	    WHERE 
		    DATEDIFF(DAY, MUTDAT, GETDATE()) <= 1
		    AND VerificationTypeCode IN ('E', 'S')
        ) 

        , MED_VER AS (
	        SELECT * FROM MED_VER_ALL WHERE RowRank = 1
        )


        SELECT

        SEHID, 
        SEH.PATIENTNR,
        KLACHT,
        VVCODE,
        SPECIALISM,
        TRIADATUM,
        TRIAGETIJD,
        AANKSDATUM,
        AANKSTIJD,
        TRIANIVCOD,
        VOORNAAM, 
        ACHTERNAAM,
        GESLACHT,
        DATEDIFF(YEAR, GEBDAT, AANKSDATUM) AS LEEFTIJD,

        -- Calcuate amount of previous visits 
        (
            SELECT COUNT(*) 
            FROM SEH_SEHREG prev_visits 
            WHERE prev_visits.PATIENTNR = SEH.PATIENTNR
                AND prev_visits.AANKSDATUM > DATEADD(year, -1, SEH.AANKSDATUM) 
                AND prev_visits.AANKSDATUM < SEH.AANKSDATUM
        ) AS PreviousVisits,

        -- Percentage of admissions for previous visits 
        (
            SELECT 
                CASE
                    WHEN COUNT(*) > 0 
                    THEN COUNT(CASE WHEN prev_visits.BESTEMMING IN ('OPN', 'OVER') THEN 1 END) * 100.0 / COUNT(*) 
                    ELSE 0
                END
            FROM SEH_SEHREG prev_visits 
            WHERE prev_visits.PATIENTNR = SEH.PATIENTNR
                AND prev_visits.AANKSDATUM > DATEADD(YEAR, -1, SEH.AANKSDATUM) 
                AND prev_visits.AANKSDATUM < SEH.AANKSDATUM
        ) AS PrevAdmissionPercentage,
        GEBDAT,
		VERIFIED


        FROM SEH_SEHREG SEH


        INNER JOIN PATIENT_PATIENT PAT ON PAT.PATIENTNR = SEH.PATIENTNR
		LEFT JOIN MED_VER MED ON MED.PATCODE = SEH.PATIENTNR

        WHERE DATEDIFF(DAY, AANKSDATUM, GETDATE()) <= 1
        --AND ONTSLAGDAT IS NULL -- of BESTEMMING IS NULL
        AND VERVALL = 0

		ORDER BY AANKSDATUM DESC, AANKSTIJD DESC
        "

        Using cmd As New SqlCommand(sqlQuery, sourceDatabase)
            Using reader As SqlDataReader = cmd.ExecuteReader()
                Using bulkCopy As New SqlBulkCopy(destinationDatabase)

                    bulkCopy.DestinationTableName = "SEH_REG"
                    bulkCopy.WriteToServer(reader)

                End Using
            End Using
        End Using


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