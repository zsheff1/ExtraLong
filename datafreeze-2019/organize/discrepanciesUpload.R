### This script identifies discrepancies between scans that were supposed to be
### uploaded to ExtraLong prior to discovering the GRMPY mistake
### (/Users/butellyn/Documents/fwheudiconv/ExtraLong/scanid_to_seslabel_10-08-2019.csv),
### scans that actually made it into ExtraLong
### (/Users/butellyn/Documents/bids_curation/ExtraLong/ExtraLong_10-17-2019.csv),
### and scans that should be in ExtraLong, i.e., after GRMPY mistake was discovered
### (/Users/butellyn/Documents/bids_curation/ExtraLong/scanid_to_seslabel_10-16-2019.csv)
###
### Ellyn Butler
### October 17, 2019

origtoupload_df <- read.csv("/Users/butellyn/Documents/fwheudiconv/ExtraLong/scanid_to_seslabel_10-08-2019.csv")
inextra_df <- read.csv("/Users/butellyn/Documents/bids_curation/ExtraLong/ExtraLong_10-17-2019.csv")
shouldextra_df <- read.csv("/Users/butellyn/Documents/bids_curation/ExtraLong/scanid_to_seslabel_10-16-2019.csv")


# Row-bind and then remove duplicate rows to determine discrepancies between
# origtoupload_df and shouldextra_df

origtoupload_df$source <- "orig"
shouldextra_df$source <- "should"

combo_df <- rbind(origtoupload_df, shouldextra_df)
combo_df$keep <- 0
combo_df$bblidscanid <- paste0(combo_df$bblid, combo_df$scanid)
for (i in 1:nrow(combo_df)) {
  numscans <- length(combo_df$bblidscanid[combo_df$bblidscanid == combo_df[i, "bblidscanid"]])
  if (numscans == 1 ) {
    combo_df[i, "keep"] <- 1
  }
}

combounique_df <- combo_df[combo_df$keep == 1,]

# Looks like all of the same scans should have made it over, but based on different labels.
# So why didn't all of the scans make it over? More importantly, which ones didn't?
origtoupload_df2 <- origtoupload_df[,c("study", "bblid", "seslabel")]
origtoupload_df2$bblidseslabel <- paste0(origtoupload_df2$bblid, origtoupload_df2$seslabel)
inextra_df2 <- inextra_df
inextra_df2$study <- "ExtraLong"
inextra_df2$bblidseslabel <- paste0(inextra_df2$bblid, inextra_df2$seslabel)

discrepanciesUpload_df <- rbind(origtoupload_df2, inextra_df2)
discrepanciesUpload_df$keep <- 0
discrepanciesUpload_df$bblidseslabel <- paste0(discrepanciesUpload_df$bblid, discrepanciesUpload_df$seslabel)
for (i in 1:nrow(discrepanciesUpload_df)) {
  numscans <- length(discrepanciesUpload_df$bblidseslabel[discrepanciesUpload_df$bblidseslabel == discrepanciesUpload_df[i, "bblidseslabel"]])
  if (numscans != 2) {
    discrepanciesUpload_df[i, "keep"] <- 1
  }
}
discunique_df <- discrepanciesUpload_df[discrepanciesUpload_df$keep == 1,]
