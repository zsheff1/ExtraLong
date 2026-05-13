library(tidyverse)
library(rjson)
scanner_info_files <- list.files(path = '/project/ExtraLong/data/datafreeze-2021/bids_directory',recursive = T,full.names = T,pattern = 'T1w.json$')

read_json_files <- function(f){
    json <- fromJSON(file = f) 
    json$ImageOrientationPatientDICOM <- str_c(as.character(json$ImageOrientationPatientDICOM),collapse = ', ')
    json$ImageType <- str_c(as.character(json$ImageType),collapse = ', ')
    json$ShimSetting <- str_c(as.character(json$ShimSetting),collapse = ', ')
    json <- json[str_detect(names(json),pattern = 'IntendedFor|PatientWeight',negate = T)]
    bblid <- str_extract(f,pattern = '(?<=sub-)[:digit:]+')
    sesid <- str_extract(f,pattern = '(?<=ses-)[:digit:]+')
    output_df <- json %>% as.data.frame() %>% mutate(bblid = bblid,sesid = sesid) %>% relocate(bblid,sesid)
    return(output_df)
}

scan_settings_df <- map_dfr(scanner_info_files,read_json_files)
write_csv(scan_settings_df,file = '/project/ExtraLong/data/datafreeze-2021/QC/scan_metadata.csv')
