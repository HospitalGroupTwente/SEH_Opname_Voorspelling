library(httr)
library(jsonlite)
library(shiny)
library(DT)
library(shinythemes)
library(dplyr)
library(plotly)
library(odbc)
library(data.table)
library(htmltools)
library(shinyjs)
library(yaml)

config <- yaml::yaml.load_file("./config.yaml")

# PREDICTION FUNCTIONS (http requests handling) #

get_seh_data <- function(connection) {
    # ODBC requires long data to be the last column
    # So keep that in mind when changing queries
    query <- "
    SELECT  
        
        SEHID, 
        PATIENTNR,
        VOORNAAM, 
        ACHTERNAAM,
        LEEFTIJD, 
        GESLACHT,
        VVCODE,
        SPECIALISM,
        PreviousVisits,
        PrevAdmissionPercentage,
        AANKSDATUM,
        AANKSTIJD,
        TRIANIVCOD,
        TRIADATUM,
        TRIAGETIJD,
        GEBDAT,
        VERIFIED,
        KLACHT
        
     FROM SEH_REG
     "
    data <- as.list(dbGetQuery(connection, query))
    
    return(toJSON(data))
}

get_lab_data <- function(connection) {
    # no long data so we can use SELECT *

        query <- "SELECT * FROM SEH_LAB"
        data <- as.list(dbGetQuery(connection, query))

    return(toJSON(data))
}

get_vital_data <- function(connection) {
    # no long data so we can use SELECT *

    query <- "SELECT * FROM SEH_VITALS"
    data <- as.list(dbGetQuery(connection, query))

    return(toJSON(data))
}

get_all_data_from_db <- function() {

    # get db connection
    con <- dbConnect(odbc(), Driver = config$driver, Server = config$server,  Database = config$database, UID = config$uid, PWD = config$pwd, Port = config$port)
    
    # get data
    lab_data_json   <- get_lab_data(con)
    vital_data_json <- get_vital_data(con)
    seh_data_json   <- get_seh_data(con)

    all_data <- list(
        seh_data = fromJSON(seh_data_json),
        lab_data = fromJSON(lab_data_json),
        vital_data = fromJSON(vital_data_json)
    )

    # close db connection
    dbDisconnect(con)

    # if there are not patients
    if (length(all_data$seh_data$SEHID) == 0) {
        return(NULL)
    }

    return(toJSON(all_data))
}

write_data_to_db <- function(data) {
    con <- dbConnect(odbc(), Driver = config$driver, Server = config$server,  Database = config$database, UID = config$uid, PWD = config$pwd, Port = config$port)

    data <- data[!is.na(data$PREDICTION), ]  # do not write if no prediction
    dbWriteTable(con, "SEH_PREDICTIONS", as.data.frame(data), append=TRUE)
                                                                                           
    dbDisconnect(con)
}

get_data_and_predictions <- function() {


    # get data from the research db
    data <- get_all_data_from_db()

    if (is.null(data)) {
        return(NULL)
    }

    # get prediction via http POST
    response <- POST("", 
                    add_headers("Content-Type" = "application/json"),
                    body = data)

    response <- fromJSON(content(response, as = 'text', encoding='UTF-8'))
    results <- response$result

    results$PREDICTION[results$PREDICTION == ''] <- NA
    results$PREDICTION <-  round(as.numeric(results$PREDICTION), 3)

    # make dfs from all data
    data <- fromJSON(data)
    data$seh_data <- as.data.frame(data$seh_data)
    data$lab_data <- as.data.frame(data$lab_data)
    data$vital_data <- as.data.frame(data$vital_data)

    # attach predictions
    data$seh_data <- merge(data$seh_data, results, by='SEHID')

    data_to_write <- select(data$seh_data, SEHID, PATIENTNR,  AANKSDATUM, AANKSTIJD, LEEFTIJD, GESLACHT, VVCODE, KLACHT, SPECIALISM, PreviousVisits, PrevAdmissionPercentage, TRIANIVCOD, TRIADATUM, TRIAGETIJD, PREDICTION, TIMEDELTA)
    names(data_to_write)[names(data_to_write) == "TIMEDELTA"] <- "MODEL_USED"
    write_data_to_db(data_to_write)
    
    return(data)
    
}


# DASHBOARD FUNCTIONS #

add_rectangle <- function(plot, x0, x1, color, label){
    return(add_trace(p=plot, x=c(x0, x1), y=c(1.1), fill="tozeroy", fillcolor=color, mode="lines", line=list(color=color), name=label))
}

create_time_plot <- function(patient_time_data) {
    most_recent_entry <- patient_time_data %>%
                            group_by(PATIENTNR) %>%
                            filter(TIMEDELTA == max(TIMEDELTA)) %>%
                            slice(n())

    # plotting
    plot <- plot_ly(data = patient_time_data, 
                    x = ~TIMEDELTA, 
                    y = ~PREDICTION, 
                    type = "scatter", 
                    mode = "lines+markers", 
                    name = "Voorspelling",
                    height=300) %>%
                    # adding areas for lab, vitals, and triage
                    add_rectangle(
                        x0 = ifelse("LAB_START" %in% colnames(most_recent_entry), most_recent_entry$LAB_START, 0),
                        x1 = ifelse("LAB_END" %in% colnames(most_recent_entry), most_recent_entry$LAB_END, 0),
                        color = "rgba(102, 250, 102, 0.4)",
                        label = "Lab uitslag window"
                    ) %>%
                    add_rectangle(
                        x0 = ifelse("VITAL_START" %in% colnames(most_recent_entry), most_recent_entry$VITAL_START, 0),
                        x1 = ifelse("VITAL_END" %in% colnames(most_recent_entry), most_recent_entry$VITAL_END, 0),
                        color = "rgba(0, 186, 255, 0.4)",
                        label = "Vital uitslag window"
                    ) %>%
                    add_lines(
                        x = c(most_recent_entry$TRIAGE, most_recent_entry$TRIAGE),
                        y = c(0, 1.1),
                        mode = "lines",
                        line = list(color = "rgba(255, 89, 0, 1)"),
                        name = "Triage"
                    )


    # styling 
    plot <- layout(
        plot,
        margin = list(pad=50),
        title = "Verloop van de voorspellingen",
        xaxis = list(title = "Tijd op SEH (min)", range=c(0, 190), dtick=30, gridcolor="#545454"),
        yaxis = list(title = "Opname voorspelling", range = c(0, 1), gridcolor="#545454"),
        # margin = list(l = 60, r = 40, b = 40, t = 10),  
        paper_bgcolor = "#373737",  
        plot_bgcolor = "#373737",   
        font = list(color = "white"),
        # legend = list(x = 0.7, y = 1.2, font = list(size = 10)),
        showlegend=TRUE
    )


    return(plot)
}

map_prob_to_color <- function(probability) {
    # returns the color according to a probability between 0 to 1. The color is from green to red gradient. 

    return(ifelse(probability <= 0.5, rgb(probability * 2, 1, 0, maxColorValue = 1), rgb(1, 1 - (probability - 0.5) * 2, 0, maxColorValue = 1)))
}

generate_severity_indicator <- function(probability) {
  
     # if no patient is selected
    if (length(probability) == 0) {
        return(tags$div(
        tags$div("Selecteer een patient")))
    }

    # if a patient is selected:

    percentage <- probability * 100
    
    # calculate color based on gradient from red  to green (0 is green, 1 is red)
    hex_color <- map_prob_to_color(probability)

    # returns a HTML like div with a severity indicator (progress circle) and the probability of admission 
    return(
        tags$div(
        style = paste0(
            "width: 140px; height: 140px; border-radius: 50%; background-color: transparent; position: relative; transform: scale(1.0);",
            "background-image: conic-gradient(", hex_color, " 0%, ", hex_color, " ", percentage, "%, transparent ", percentage, "%, transparent 100%);"
        ),
        class = "center-content",
        tags$div(
            style = "width: 112px; height: 112px; border-radius: 50%; background-color: #222222; position: absolute; top: 14px; left: 14px;",
            class = "center-content",
            tags$h1(
            style = "font-size: 28px; margin: 0; color: white; position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); white-space: nowrap;",
            paste0(percentage, " %")
        )
      )
    )
  )
}

merge_date_and_time <- function(date, time) {
    # merges date and time data, and returns it as a datetime type
    return(as.POSIXct(paste(date, time), format="%Y-%m-%d %H:%M"))
}

get_time_diff <- function(date_time, start_datetime) {
    return(as.numeric(difftime(date_time, start_datetime, units='mins')))
}

get_result_window <- function(df, time_col) {
    if (nrow(df) > 0) {

        window <- df %>%
        group_by(PATIENTNR) %>%
        summarise(START = min({{ time_col }}),
              END = max({{ time_col }}))   
    }
    else {
        window = NULL
    }

    
    return(window)
}

process_result_window <- function(data_over_time, window, prefix) {
    # processes the result window to get start time and end time in minutes with respect to each patients arrival time
    if (!is.null(window)) {
        data_over_time_window <- merge(data_over_time, window, by='PATIENTNR', all.x=TRUE)  # left join
        data_over_time_window <- data_over_time_window[order(match(data_over_time_window$PATIENTNR, data_over_time$PATIENTNR)), ] # order df

        start_col <- paste0(prefix, "_START")
        end_col <- paste0(prefix, "_END")
        data_over_time[[start_col]] <- get_time_diff(data_over_time_window$START, data_over_time_window$AANKOMST)
        data_over_time[[end_col]] <- get_time_diff(data_over_time_window$END, data_over_time_window$AANKOMST)
        # sometime start and end time are the same, if thats the case add 1 to end time so that it becomes visible in the plot later
        data_over_time[[end_col]] <- ifelse(data_over_time[[end_col]] == data_over_time[[start_col]], data_over_time[[end_col]] + 1, data_over_time[[end_col]]) 
    }

    return(data_over_time)
}

get_data_time <- function(data) {
    if (!is.null(data)) {
         data_over_time <- select(data$seh_data, SEHID, PATIENTNR, TIMEDELTA, PREDICTION, AANKSDATUM, AANKSTIJD, TRIADATUM, TRIAGETIJD) 
    
        # change to date type
        data_over_time$AANKOMST <- merge_date_and_time(data_over_time$AANKSDAT, data_over_time$AANKSTIJD)
        data$lab_data$UITSLAGTIJD <- merge_date_and_time(data$lab_data$UITDATUM, data$lab_data$UITTIJD)
        data_over_time$TRIAGE <- merge_date_and_time(data_over_time$TRIADATUM, data_over_time$TRIAGETIJD)

        # get time diffs for TRIAGE, LAB and VITAL
        data_over_time$TRIAGE <- get_time_diff(data_over_time$TRIAGE, data_over_time$AANKOMST)
        
        lab_window <- get_result_window(data$lab_data, UITSLAGTIJD)
        data_over_time <- process_result_window(data_over_time, lab_window, 'LAB')

        vital_window <- get_result_window(data$vital_data, DateTime)
        data_over_time <- process_result_window(data_over_time, vital_window, 'VITAL')
        return(data_over_time)
    }
}

update_data_time <- function(data_time, new_data) {
    new_data_time <- get_data_time(new_data)
    data_time <- rbind(data_time, new_data_time)  # concatenate dataframes
    data_time <- data_time[!duplicated(data_time),]  # removes duplicated rows
    return(data_time)
}

create_color_column <- function(data) {
    # creates the color circle in the last column of the overview table

    data$COLOR <- sapply(data$PREDICTION, function(pred) {
        color <- map_prob_to_color(pred)
        paste0('<div style="width: 15px; height: 15px; border-radius: 50%; background-color: ', color, '; margin: 0 auto;"></div>')
        })
    
    colnames(data)[colnames(data) == "COLOR"] <- " "

    return(data)
}

    # function to format medication verificaiton column to a checkmark
format_verified_column <- function(data) {

    data$VERIFIED <- sapply(data$VERIFIED, function(value) {
        if (is.na(value)) {
            new_value = ""
        } else if (value == 1) {
            new_value = '<span style="color: #1bf756; font-size: 20px;">&#10004;</span>'
        } else {
            new_value = ""
        }
        new_value
    })

    return(data)
}

# initilaize variables when starting the script
data <- get_data_and_predictions()
data_over_time <- get_data_time(data)
lastUpdate <- reactiveVal(Sys.time())

# SHINY R:  

## Shiny server
server <- function(input, output, session) {
    # TIMER:
    # similar to pythons wait.wait()
    autoInvalidateTimer <- reactiveTimer(30000)  # unit is ms, so 30 sec

    observe({

        # wait 60 seconds
        autoInvalidateTimer()

        # check if its time to update the data
        if (as.numeric(difftime(Sys.time(), lastUpdate(), units = "secs")) >= 600) {
    
            data <<- isolate(get_data_and_predictions())  # isolate prevents the re-evaluation so that the timer does not reset
            data_over_time <<- isolate(update_data_time(data_over_time, data))
    
            # update the timestamp of the last data update
            lastUpdate(Sys.time())
            output$overview_data <- renderDT({
                    datatable(overview_data, 
                                selection = list(mode = 'single', selected = c(1)), 
                                escape=FALSE, 
                                options = list(pageLength = 30, scrollX = TRUE,
                                            columnDefs = list(list(className = 'dt-center', targets = c(1,2,3,5,6,7)))))})
        }
    })


    # REACTIVE ELEMENTS:
    # returns the overview data of the selected patient
    get_selected_patient <- reactive({
        patient_number <- data$seh_data[input$overview_data_rows_selected, 'PATIENTNR']
        # if no patient is selected return nothing
        if (length(patient_number) == 0) {
            return(NULL)
        }
        return(patient_number)
    })
    
    # returns all the data of the selected patient (t=0 until t=end)
    get_selected_patient_info <- reactive({
        patient <- get_selected_patient()
        info <- data$seh_data[data$seh_data$PATIENTNR == patient, ]
        # if no patient is selected return nothing
        if (length(info) == 0) {
            return(data.frame())
        }
        return(info)
    })

    # returns all the data of the selected patient (t=0 until t=end)
    get_selected_patient_labs <- reactive({
        patient_number <-  get_selected_patient()
        lab_data <- data$lab_data[data$lab_data$PATIENTNR == patient_number, ]
        # if no patient is selected return nothing
        if (length(lab_data) == 0) {
            return(NULL)
        }
        return(select(lab_data, DESC, UITSLAG, EENHEID))
    })

    get_selected_patient_vitals <- reactive({
        patient_number <- get_selected_patient()
        vital_data <- data$vital_data[data$vital_data$PATIENTNR == patient_number, ]
        # if no patient is selected return nothing
        if (length(vital_data) == 0) {
            return(NULL)
        }

        return(select(vital_data, DateTime, LABEL, Value1))
    })

    # SERVER OUTPUTS:
    if (!is.null(data)) {
        overview_data <- select(data$seh_data, ACHTERNAAM, GEBDAT, AANKSTIJD, KLACHT, SPECIALISM, VERIFIED, PREDICTION)
        overview_data <- create_color_column(overview_data) 
        overview_data <- format_verified_column(overview_data)
        names(overview_data)[names(overview_data) == "GEBDAT"] <- "GEBDATUM" # renaming column
        output$overview_data <- renderDT({
            datatable(overview_data, 
                      selection = list(mode = 'single', selected = c(1)), 
                      escape=FALSE, 
                      options = list(pageLength = 30, scrollX = TRUE,
                                    columnDefs = list(list(className = 'dt-center', targets = c(1,2,3,5,6,7)))))
        })
    }
    else {
        output$overview_data <- renderDT(data.frame(c("Geen patienten op de SEH")), options=list(dom="t", ordering=FALSE), rownames=FALSE, colnames='')
    }

    # renders the severity indicator from the right pane
    output$severity_indicator <- renderUI({
        patient <- get_selected_patient()
        generate_severity_indicator(data$seh_data[data$seh_data$PATIENTNR == patient, 'PREDICTION'])
    })
    
    output$patient_info <- renderDT(t(get_selected_patient_info()),
                                    colnames = rep("", ncol(t(get_selected_patient_info()))),
                                    selection="none",
                                    options=list(
                                        pageLength = 100,
                                        dom="t", 
                                        ordering=FALSE),
    )

    output$lab_data <- renderDT({datatable(get_selected_patient_labs(),
                                rownames=FALSE,
                                selection="none",
                                options=list(
                                    pageLength = 1000,  # could not change it to "All"
                                    dom="t",
                                    ordering=TRUE))})
    
    output$vital_data <- renderDT({vital_data <- get_selected_patient_vitals()
                                    # if checkbox is checked, do a groupby to only get the most recent values
                                    if (input$vital_recent_only && length(vital_data != 0)) {
                                        vital_data <- vital_data %>%
                                        group_by(LABEL) %>%
                                        filter(DateTime == max(DateTime))
                                   }
                                    datatable(vital_data,  
                                        rownames=FALSE,
                                        selection="none",
                                        options=list(
                                            pageLength = 1000, # could not change it to "All"
                                            dom="t",
                                            ordering=TRUE)
                                            )
                                            })
                                    
    # renders the plot of patients prediction over time
    output$patient_plot <- renderPlotly({
        seh_id <- data$seh_data[input$overview_data_rows_selected, 'SEHID']
        n_rows <-  length(seh_id)
        # if a patient is selected create that patients plot 
        if (n_rows != 0) {
            patient_data <- data_over_time %>%
                filter(SEHID == seh_id)
            plot <- create_time_plot(patient_data)
            return(plot)
        }
        
        else {
            return(NULL)
        }
    })
    
}
