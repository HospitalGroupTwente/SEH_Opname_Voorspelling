FROM openanalytics/r-base

LABEL maintainer "Job Maathuis <j.maathuis@zgt.nl>"

# system libraries of general use
RUN apt-get update && apt-get install -y \
    sudo \
    curl \
    pandoc \
    pandoc-citeproc \
    libcurl4-gnutls-dev \
    libcairo2-dev \
    libxt-dev \
    libssl-dev \
    libssh2-1-dev \
    libssl1.1

# Installing pacakges to get odbc connection to microsoft sql server (drivers, system pacakges, etc.)
RUN sudo su
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN curl https://packages.microsoft.com/config/ubuntu/20.04/prod.list > /etc/apt/sources.list.d/mssql-release.list
RUN exit
RUN sudo apt-get update && apt install -y apt-utils
RUN echo 'debconf debconf/frontend select Noninteractive' | debconf-set-selections
RUN sudo apt-get remove -y odbcinst 
RUN sudo ACCEPT_EULA=Y apt-get install -y msodbcsql17
RUN sudo ACCEPT_EULA=Y apt-get install mssql-tools
RUN echo 'export PATH="$PATH:/opt/mssql-tools/bin"' >> ~/.bash_profile
RUN echo 'export PATH="$PATH:/opt/mssql-tools/bin"' >> ~/.bashrc
SHELL ["/bin/bash", "-c"]


# system library dependency for the euler app
RUN apt-get update && apt-get install -y \
    libmpfr-dev \
    unixodbc-dev \
    unixodbc \
    odbcinst \
    odbcinst1debian2 \
    libodbc1 

# basic shiny functionality
RUN R -e "install.packages(c('shiny'), repos='https://cloud.r-project.org/')"

# install dependencies of the app
RUN R -e "install.packages(c('yaml', 'httr', 'jsonlite', 'DT', 'plotly', 'odbc', 'shinythemes', 'dplyr', 'plotly', 'data.table', 'htmltools', 'shinyjs'), repos='https://cloud.r-project.org/')"

# copy the app to the image
RUN mkdir -p /root/seh_opname_voorspelling
COPY components /root/seh_opname_voorspelling

# shiny proxy port
EXPOSE 3838 
# port to SQL server
EXPOSE 1433 

CMD ["R", "-e", "shiny::runApp('/root/seh_opname_voorspelling')"]