library(data.table)
library(dplyr)


#==================#
####  Function  ####
#==================#
read.rawSVdata <- function(dir, vessel, category) {
  
  files.excluded <- c()
  SvSchool.dt <- data.table()
  pattern <- "SvSchool\\s*(.*?)\\s*_T2019"
  files <- list.files(dir, pattern='txt$', full.names=TRUE)
  
  #==   check if there are any files that cannot be processed   ==#
  #      number of pixels between frequencies is different        # 
  
  for(i in 1:length(files)) {
    test <- read.table(files[i], sep = ",", fill = TRUE, colClasses = "character")
    
    if (var(as.numeric(test[-1, 11])) != 0 || anyNA(var(as.numeric(test[-1, 11]))) ) {
      
      files.excluded <- c(files.excluded, files[i])
      
    }
  }
  
  
  files.new <- setdiff(files, files.excluded) # create a new file list
  
  
  #==    read data file(i)    ==#
  
  for(i in 1:length(files.new)) {
    temp <- as.data.table(read.table(header = TRUE, files.new[i], sep = ","))  ## read text data
    temp <- cbind(id = as.numeric(regmatches(files.new[i], regexec(pattern, files.new[i]))[[1]][2]), temp) ## add column "id" and fetch school ID from file name
    temp[, names(temp) := lapply(.SD, as.numeric)] # Convert all columns to numeric
    temp <- data.table::melt(temp, id.vars = c(1:12))
    temp[, category := category]              ## add column category
    setcolorder(temp, c("id", "category", names(temp)[!names(temp) %in% c("id", "category")])) ## set column order, "category" column after "id" column and remainings move right.
    SvSchool.dt <- rbind(SvSchool.dt, temp, fill=TRUE)
    temp <- data.table()
    
  }
  
  #==============================#
  
  
  SvSchool.dt$vessel <- as.character(vessel) # add vessel column
  
  setnames(SvSchool.dt, c("variable", "value"), c("SampleNo","Sv")) # change column names
  
  save(files.excluded, file = paste0(dir, "/file.excluded.Rdata"))
  
  print(paste0(length(files.excluded), " files were excluded."))
  
  return(SvSchool.dt)
  
}






#=====================#
#### load row data ####
#=====================#

#-------------------------------------------------------------------------------------------------------------------------#
#directory                                                                                           vessel     category  #
#-------------------------------------------------------------------------------------------------------------------------#
#'C:/Data/S2019_SAILDRONE_1032/EXPORT/Sv_manual_scrutiny_schools_around_predator_events'             SD1032     SAND_new  #
#'C:/Data/S2019_SAILDRONE_1032/EXPORT/Sv_predator'                                                   SD1032     Predator  #
#'C:/Data/S2019_SAILDRONE_1031/EXPORT/Sv_predator'                                                   SD1031     Predator  #
#-------------------------------------------------------------------------------------------------------------------------#

#choose directory where school txt files from LSSS (raw SV data) are stored
dir <- 'C:/Data/S2019_SAILDRONE_1031/EXPORT/Sv_predator'
dir <- gsub('\\\\', '\\/', dir)




#========================#
#### run the function ####
#========================#

#"vessel"
vessel <- ifelse(grepl("1031", dir),"SD1031", "SD1032")


#"category"
#If Saildrone, PSAND->KORONA, SAND->manual, OTHER->noise
category <- case_when(grepl("_school",dir) ~ "SAND_new",
                      grepl("_predator",dir) ~ "Predator",
                      TRUE ~ "Unknown")


SvSchool.dt <- read.rawSVdata(dir = dir, vessel = vessel, category = category)


#change the table name depending on vessel and category
assign(paste("Svschool", vessel, category, sep = "_"), SvSchool.dt)

#* back to line 79 to conduct the function on all raw Sv data folders *#



#===========================#
####   save data.table   ####
#===========================#

# create a folder "rawSv_data"
dir.create("rawSv_data")
save(Svschool_SD1032_SAND_new, file = "rawSv_data/SvSchool_SD1032_SAND_new.Rdata")
save(Svschool_SD1032_Predator, file = "rawSv_data/SvSchool_SD1032_Predator.Rdata")
save(Svschool_SD1031_Predator, file = "rawSv_data/SvSchool_SD1031_Predator.Rdata")








#=======================#
#### error detection ####
#=======================#

#  when the read.rawSVdata function returned error     #
#  need "files", "dir", "category", "pattern" object   #
#  as well as empty data.table "SvSchool.dt"           #

for(i in 1:length(files)) {
  tryCatch({
    temp <- as.data.table(read.table(header = TRUE, files[i], sep = ","))  ## read text data
    temp <- cbind(id = as.numeric(regmatches(files[i], regexec(pattern, files[i]))[[1]][2]), temp) ## add column "id" and fetch school ID from file name
    temp[, names(temp) := lapply(.SD, as.numeric)] # Convert all columns to numeric
    temp <- data.table::melt(temp, id.vars = c(1:12))
    temp[, category := category]              ## add column category
    setcolorder(temp, c("id", "category", names(temp)[!names(temp) %in% c("id", "category")])) ## set column order, "category" column after "id" column and remainings move right.
    SvSchool.dt <- rbind(SvSchool.dt, temp, fill=TRUE)
    temp <- data.table()
    
    # Print progress every 100 files
    if (i %% 100 == 0) {
      cat(paste("Successfully processed", i, "files.\n"))
      }
    }, error = function(e) {
      
      # Log error message and problematic file
      cat(paste("Error reading file:", files[i], "\n", file = log_file, append = TRUE))
      cat(paste("Error message:", e$message, "\n", file = log_file, append = TRUE))
    })
  }

