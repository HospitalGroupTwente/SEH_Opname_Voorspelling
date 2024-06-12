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

# CSS Styling for dashboard

css_styling = "
        .dataTables_length label,
        .dataTables_filter label,
        .dataTables_info {
            color: white!important;
            font-size: 12px;
        }
        .dataTables_wrapper tbody tr.selected {
        background-color: white !important; 
        color: white; 
        }
        .dataTables_wrapper table {
            color: white; 
            font-size: 12px;
        }

        .tabbable > .nav > li > a         {color: white}
        .tabbable > .nav > li.active> a   {color: white}
        
        .paginate_button {
            background: white !important;
        }
        
        thead {
            color: white;
            font-size: 12px;
        }

        .center-container {
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100%;
            text-align: center;
        }
        
        .center-container .dataTables_wrapper {
            display: inline-block;
            text-align: left;
            width: 55%;
            
        .-title {
            font-size: 16px;
        }
        
        .plot-container {
            width: 100%; 
        }
"

## Shiny UI
ui <- fluidPage(
    # styling:
    theme = shinytheme("darkly"),
    tags$style(HTML(css_styling)),
    shinyjs::useShinyjs(),

    # Application title pane
    titlePanel(
        div(
            h1("SEH Opname Voorspelling", style = "margin: 15;"),
            style = "border-bottom: 2px solid #00BAFF; margin-left: -15px; margin-right: -15px; padding-left: 15px; margin-top: 20px;")
            ),

    # Some whitespace between title and main contents
    fluidRow(br(), br()),

    # Main contents/pane
    fluidRow( 
        # Renders patient overview table (left pane)
        div(
        column(6, style="background-color: #373737; padding: 15px; margin: 15px; border-radius: 10px; margin-left: 50px;" ,
            h3("Patienten overzicht", style="text-align: center;"), br(),
            fluidRow(DTOutput("overview_data"), style="width: 90%; margin: 20px;"), 
            fluidRow(br(), br()),
            )
        ),

        # Shows selected patients data (right pane)
        div(
        column(5, style="background-color: #373737; padding: 15px; margin: 15px; border-radius: 10px;",
            h3("Details geselecteerde patient", style="text-align: center;"), br(),

            # create tabs
            tabsetPanel(type="tabs", id="tab_selected",

                        tabPanel("Patiënt data", value="seh_data",
                                div(
                                    br(),
                                    div(uiOutput("severity_indicator"), class = "center-container"),
                                    div(DTOutput("patient_info"), class = "center-container")
                                    )),
                        
                        tabPanel("Lab data",
                                br(),
                                div(DTOutput("lab_data"), style="width: 80%; margin: 20px;")),
                        
                        tabPanel("Vital data", value="vital_data",
                                br(),
                                div(checkboxInput("vital_recent_only", "Laat alleen meest recente resultaten zien"), style="margin-left: 30px"),
                                div(DTOutput("vital_data"), style="width: 80%; margin: 20px;")),

                        tabPanel("Tijdsplot",
                                br(), br(), br(),
                                div(plotlyOutput("patient_plot", width = "100%"), class = "center-content-column"))
                        )
        ))
    )
)